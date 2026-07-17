"""
Rolling Metrics & Trend Analysis Pipeline
========================================
This script computes time-series revenue metrics including weekly and monthly
resampling, rolling averages, month-over-month change, and cumulative revenue.
It exports a plot and a business interpretation text file for reporting.
"""

import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Ensure stdout and stderr support UTF-8 on Windows environments
if hasattr(sys.stdout, "buffer"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

OUTPUT_DIR = Path("output")
INPUT_FILE = Path("data/processed/parsed_timestamps.csv")
PLOT_FILE = OUTPUT_DIR / "rolling_avg.png"
TEXT_FILE = OUTPUT_DIR / "trend_analysis.txt"
SUMMARY_FILE = OUTPUT_DIR / "rolling_metrics_summary.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_time_series(filepath: Path) -> pd.DataFrame:
    """Load the processed transaction dataset and normalize the date column."""
    if not filepath.exists():
        raise FileNotFoundError(
            f"Input file {filepath} does not exist. Run parse_timestamps.py first."
        )

    df = pd.read_csv(filepath)
    if "transaction_date" not in df.columns:
        raise KeyError("Expected a transaction_date column in the input dataset.")

    df = df.rename(columns={"transaction_date": "date", "amount": "revenue"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "revenue"]).sort_values("date").reset_index(drop=True)
    df["orders"] = 1
    return df


def compute_resampled_metrics(df: pd.DataFrame) -> dict:
    """Compute weekly, monthly, rolling, and cumulative metrics."""
    df_ts = df.set_index("date")

    weekly_revenue = df_ts["revenue"].resample("W").sum()
    weekly_count = df_ts["orders"].resample("W").count()
    weekly_avg = df_ts["revenue"].resample("W").mean()

    monthly_revenue = df_ts["revenue"].resample("M").sum()
    monthly_count = df_ts["orders"].resample("M").count()
    monthly_avg = df_ts["revenue"].resample("M").mean()
    mom_change = monthly_revenue.pct_change() * 100

    df["revenue_ma7"] = df["revenue"].rolling(window=7, min_periods=1).mean()
    df["revenue_ma30"] = df["revenue"].rolling(window=30, min_periods=1).mean()
    df["cumulative_revenue"] = df["revenue"].cumsum()

    recent_ma30 = df["revenue_ma30"].tail(min(30, len(df)))
    trend_direction = "flat"
    trend_magnitude = 0.0
    if len(recent_ma30) >= 2:
        first_value = float(recent_ma30.iloc[0])
        last_value = float(recent_ma30.iloc[-1])
        if last_value > first_value:
            trend_direction = "up"
        elif last_value < first_value:
            trend_direction = "down"
        if first_value != 0:
            trend_magnitude = ((last_value - first_value) / first_value) * 100

    return {
        "df": df,
        "weekly_revenue": weekly_revenue,
        "weekly_count": weekly_count,
        "weekly_avg": weekly_avg,
        "monthly_revenue": monthly_revenue,
        "monthly_count": monthly_count,
        "monthly_avg": monthly_avg,
        "mom_change": mom_change,
        "trend_direction": trend_direction,
        "trend_magnitude": trend_magnitude,
    }


def plot_trends(df: pd.DataFrame) -> None:
    """Plot raw revenue and rolling averages."""
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["revenue"], label="Raw", alpha=0.3)
    plt.plot(df["date"], df["revenue_ma7"], label="7-day MA")
    plt.plot(df["date"], df["revenue_ma30"], label="30-day MA")
    plt.title("Revenue Trend vs Rolling Averages")
    plt.xlabel("Date")
    plt.ylabel("Revenue")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOT_FILE)
    plt.close()

    cumulative_fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["date"], df["cumulative_revenue"], color="#4c72b0")
    ax.set_title("Cumulative Revenue Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Revenue")
    cumulative_fig.tight_layout()
    cumulative_fig.savefig(OUTPUT_DIR / "cumulative.png")
    plt.close(cumulative_fig)


def build_analysis_text(df: pd.DataFrame, metrics: dict) -> str:
    """Create a business summary using the computed metrics."""
    monthly_revenue = metrics["monthly_revenue"]
    mom_change = metrics["mom_change"]
    trend_direction = metrics["trend_direction"]
    trend_magnitude = metrics["trend_magnitude"]

    growth_months = mom_change[mom_change > 0]
    decline_months = mom_change[mom_change < 0]

    last_mom_change = float(mom_change.dropna().iloc[-1]) if mom_change.dropna().shape[0] else 0.0
    total_revenue = float(df["cumulative_revenue"].iloc[-1]) if not df.empty else 0.0
    revenue_noise = float(df["revenue"].std()) if len(df) > 1 else 0.0

    if trend_direction == "up":
        implication = "Accelerating growth - maintain current strategy"
        action = "Double down on the channels and cohorts driving sustained growth."
    elif trend_direction == "down":
        implication = "Declining momentum - investigate causes"
        action = "Investigate pricing, product issues, and acquisition quality immediately."
    else:
        implication = "Stable trend - optimize efficiency"
        action = "Maintain strategy and look for incremental efficiency gains."

    analysis = f"""TREND ANALYSIS:

Rolling Average Trend: {trend_direction.upper()}
Change over last 30 days: {trend_magnitude:.1f}%

Month-over-month growth: {last_mom_change:.1f}%

Monthly Revenue:
{monthly_revenue.to_string()}

Positive growth months:
{growth_months.to_string() if not growth_months.empty else 'None'}

Negative growth months:
{decline_months.to_string() if not decline_months.empty else 'None'}

Business Implications:
- {implication}
- Revenue volatility: ${revenue_noise:.0f} (measure of noise)
- Recommended action: {action}

Total accumulated revenue by end of period: ${total_revenue:,.0f}
"""
    return analysis


def main() -> None:
    df = load_time_series(INPUT_FILE)
    metrics = compute_resampled_metrics(df)
    df = metrics["df"]

    weekly_revenue = metrics["weekly_revenue"]
    weekly_count = metrics["weekly_count"]
    weekly_avg = metrics["weekly_avg"]
    monthly_revenue = metrics["monthly_revenue"]
    monthly_count = metrics["monthly_count"]
    monthly_avg = metrics["monthly_avg"]
    mom_change = metrics["mom_change"]

    plot_trends(df)
    analysis_text = build_analysis_text(df, metrics)

    summary = {
        "weekly_revenue": {str(k.date()): float(v) for k, v in weekly_revenue.items()},
        "weekly_count": {str(k.date()): int(v) for k, v in weekly_count.items()},
        "weekly_avg": {str(k.date()): float(v) for k, v in weekly_avg.items()},
        "monthly_revenue": {str(k.date()): float(v) for k, v in monthly_revenue.items()},
        "monthly_count": {str(k.date()): int(v) for k, v in monthly_count.items()},
        "monthly_avg": {str(k.date()): float(v) for k, v in monthly_avg.items()},
        "mom_change": {str(k.date()): None if pd.isna(v) else float(v) for k, v in mom_change.items()},
        "trend_direction": metrics["trend_direction"],
        "trend_magnitude": round(metrics["trend_magnitude"], 2),
        "total_revenue": float(df["cumulative_revenue"].iloc[-1]),
    }

    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(analysis_text)

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(analysis_text)
    print(f"Saved plot to {PLOT_FILE}")
    print(f"Saved cumulative plot to {OUTPUT_DIR / 'cumulative.png'}")
    print(f"Saved analysis text to {TEXT_FILE}")
    print(f"Saved summary JSON to {SUMMARY_FILE}")


if __name__ == "__main__":
    main()

"""
Statistical Outlier Detection & Handling Pipeline
==================================================
This script implements Z-score and IQR-based outlier detection, applies column-specific
handling strategies (capping, removal, and flagging), and logs all decisions to an audit trail.
"""

import json
import os
import sys
import pandas as pd
import numpy as np
from scipy import stats

# Ensure stdout and stderr support UTF-8 on Windows environments
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration and Constants
OUTPUT_DIR = "output"
RAW_INPUT_FILE = "data/raw/outlier_sample.csv"
PROCESSED_OUTPUT_FILE = "data/processed/clean_outliers.csv"
CLEANING_LOG_FILE = os.path.join(OUTPUT_DIR, "outlier_cleaning_log.json")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "outlier_summary.json")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROCESSED_OUTPUT_FILE), exist_ok=True)


def build_sample_dataset():
    """Create a synthetic dataset with outliers in salary, vacation_days, and customer_spend."""
    print("Generating synthetic dataset with outliers...")
    data = {
        "id": list(range(1, 21)),
        "salary": [
            52000, 58000, 60000, 48000, 62000,
            55000, 75000, 650000, 59000, 51000,  # 650,000 is a Z-score outlier!
            64000, 47000, 53000, 68000, 72000,
            56000, 61000, 50000, 57000, 63000
        ],
        "vacation_days": [
            15, 12, 20, 10, 18,
            14, 25, 22, 150, 11,  # 150 is an IQR outlier!
            16, 13, 19, 8, 21,
            17, 12, 15, 10, 14
        ],
        "customer_spend": [
            25.50, 45.00, 120.00, 15.75, 85.20,
            30.00, 110.00, 55.45, 95.00, 5000.00,  # 5,000.00 is an IQR outlier!
            12.50, 65.00, 140.00, 75.00, 22.00,
            40.00, 105.00, 60.00, 80.00, 35.00
        ]
    }
    return pd.DataFrame(data)


def detect_outliers_zscore(df, column, threshold=3.0):
    """
    Detect outliers using the Z-score method.
    
    Args:
        df: Pandas DataFrame.
        column: Column name to analyze.
        threshold: Z-score threshold (standard deviations from mean).
        
    Returns:
        is_outlier: Boolean series where True indicates an outlier.
        z_scores: Series of computed absolute Z-scores.
    """
    z_scores = np.abs(stats.zscore(df[column]))
    is_outlier = z_scores > threshold
    return is_outlier, z_scores


def detect_outliers_iqr(df, column, factor=1.5):
    """
    Detect outliers using the IQR (Interquartile Range) method.
    
    Args:
        df: Pandas DataFrame.
        column: Column name to analyze.
        factor: Multiplier for IQR (standard is 1.5).
        
    Returns:
        is_outlier: Boolean series.
        bounds: Tuple of (lower_bound, upper_bound).
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    is_outlier = (df[column] < lower_bound) | (df[column] > upper_bound)
    return is_outlier, (lower_bound, upper_bound)


def main():
    # Step 1: Ingest or build raw data
    if os.path.exists(RAW_INPUT_FILE):
        print(f"Loading raw dataset from {RAW_INPUT_FILE}...")
        df = pd.read_csv(RAW_INPUT_FILE)
    else:
        df = build_sample_dataset()
        df.to_csv(RAW_INPUT_FILE, index=False)
        print(f"Saved synthetic dataset to {RAW_INPUT_FILE}")

    print("\n" + "=" * 70)
    print("BEFORE PROCESSING (Raw statistics)")
    print("=" * 70)
    print(df.describe().to_string())

    cleaning_log = []
    df_clean = df.copy()

    # Step 2: Handle "salary" outliers using Flagging strategy
    # Z-score is chosen because salaries are near-normally distributed (except executive outlier)
    # Threshold = 2.0 is appropriate for this small sample size (n=20) to detect the 650k executive
    print("\n[Step 1/3] Analyzing 'salary' outliers...")
    salary_outliers, salary_zs = detect_outliers_zscore(df_clean, "salary", threshold=2.0)
    outlier_count = int(salary_outliers.sum())
    
    # Flag strategy: Add boolean column without altering original column values
    df_clean["is_salary_outlier"] = salary_outliers.astype(int)
    
    cleaning_log.append({
        "column": "salary",
        "method": "Z-score (threshold=2.0)",
        "action": "flag",
        "outliers_detected": outlier_count,
        "rows_affected": outlier_count,
        "business_reasoning": (
            "Salary contains a legitimate but extreme executive salary. "
            "We flag this outlier to preserve the actual values while allowing "
            "downstream models or dashboards to segment or filter it out."
        )
    })
    print(f"✓ Flagged {outlier_count} outlier(s) in 'salary'. Created 'is_salary_outlier' column.")

    # Step 3: Handle "vacation_days" outliers using Capping strategy
    # IQR is chosen because vacation days are bounded and skewed
    print("\n[Step 2/3] Analyzing 'vacation_days' outliers...")
    vacation_outliers, (vac_lb, vac_ub) = detect_outliers_iqr(df_clean, "vacation_days", factor=1.5)
    outlier_count = int(vacation_outliers.sum())
    
    # Cap strategy: Clip values to boundaries
    df_clean["vacation_days"] = df_clean["vacation_days"].clip(lower=vac_lb, upper=vac_ub)
    
    cleaning_log.append({
        "column": "vacation_days",
        "method": "IQR (factor=1.5)",
        "action": "cap",
        "outliers_detected": outlier_count,
        "rows_affected": outlier_count,
        "lower_bound": float(vac_lb),
        "upper_bound": float(vac_ub),
        "business_reasoning": (
            "An employee has 150 vacation days which violates corporate policy limits (max 30). "
            "Since the rest of the employee row is valid, we cap this value at the upper IQR limit "
            "to prevent skewing averages while retaining the row."
        )
    })
    print(f"✓ Capped {outlier_count} outlier(s) in 'vacation_days' at boundaries [{vac_lb:.3f}, {vac_ub:.3f}].")

    # Step 4: Handle "customer_spend" outliers using Removal strategy
    # IQR is chosen because spend is heavily right-skewed
    print("\n[Step 3/3] Analyzing 'customer_spend' outliers...")
    spend_outliers, (spend_lb, spend_ub) = detect_outliers_iqr(df_clean, "customer_spend", factor=1.5)
    outlier_count = int(spend_outliers.sum())
    
    # Remove strategy: Filter out rows containing outliers
    # We keep only rows where spend_outliers is False
    df_clean = df_clean[~spend_outliers]
    
    cleaning_log.append({
        "column": "customer_spend",
        "method": "IQR (factor=1.5)",
        "action": "remove",
        "outliers_detected": outlier_count,
        "rows_affected": outlier_count,
        "lower_bound": float(spend_lb),
        "upper_bound": float(spend_ub),
        "business_reasoning": (
            "A transaction spend of 5,000 is detected when normal customer spend ranges from 12 to 140. "
            "This likely represents an system integration test record or currency translation error. "
            "The row is removed from the analytical dataset to avoid distorting revenue models."
        )
    })
    print(f"✓ Removed {outlier_count} row(s) containing 'customer_spend' outliers.")

    # Step 5: Save processed dataset
    df_clean.to_csv(PROCESSED_OUTPUT_FILE, index=False)
    print(f"\n✓ Cleaned data saved to {PROCESSED_OUTPUT_FILE}")

    # Step 6: Generate summary and save metadata
    # Before/After comparative statistics
    summary_report = {
        "record_counts": {
            "before": len(df),
            "after": len(df_clean)
        },
        "statistics_comparison": {
            "salary": {
                "mean_before": float(df["salary"].mean()),
                "mean_after": float(df_clean["salary"].mean()), # note: flagging preserves value, but row removal of spend outlier (row 10) affects salary count/mean too
                "median_before": float(df["salary"].median()),
                "median_after": float(df_clean["salary"].median())
            },
            "vacation_days": {
                "mean_before": float(df["vacation_days"].mean()),
                "mean_after": float(df_clean["vacation_days"].mean()),
                "median_before": float(df["vacation_days"].median()),
                "median_after": float(df_clean["vacation_days"].median())
            },
            "customer_spend": {
                "mean_before": float(df["customer_spend"].mean()),
                "mean_after": float(df_clean["customer_spend"].mean()),
                "median_before": float(df["customer_spend"].median()),
                "median_after": float(df_clean["customer_spend"].median())
            }
        }
    }

    # Save log files
    with open(CLEANING_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaning_log, f, indent=2)
    print(f"✓ Outlier cleaning audit log saved to {CLEANING_LOG_FILE}")

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
    print(f"✓ Summary report saved to {SUMMARY_FILE}")

    print("\n" + "=" * 70)
    print("AFTER PROCESSING (Cleaned statistics)")
    print("=" * 70)
    print(df_clean.describe().to_string())
    print("=" * 70 + "\nOutlier processing pipeline complete!")


if __name__ == "__main__":
    main()

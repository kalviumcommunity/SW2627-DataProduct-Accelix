import pandas as pd
import numpy as np

def analyze_onboarding_friction(cleaned_data):
    """
    Analyzes onboarding progress, stage completion status, duration, and delays.
    Answers:
    1. Where are new hires facing onboarding difficulties?
    2. Which onboarding stages take the longest or experience delays?
    """
    df_onb = cleaned_data.get("onboarding", pd.DataFrame())

    if df_onb.empty:
        return {}

    total_employees = df_onb["employee_id"].nunique()
    total_stages = len(df_onb)
    completed_stages = len(df_onb[df_onb["stage_status"] == "Completed"])
    overall_completion_rate = round((completed_stages / total_stages) * 100, 2) if total_stages > 0 else 0.0

    # Stage-level metrics
    stage_summary = df_onb.groupby("onboarding_stage").agg(
        total_assigned=("employee_id", "count"),
        completed_count=("stage_status", lambda x: (x == "Completed").sum()),
        delayed_count=("stage_status", lambda x: (x == "Delayed").sum()),
        in_progress_count=("stage_status", lambda x: (x == "In Progress").sum()),
        avg_duration_days=("duration_days", "mean")
    ).reset_index()

    stage_summary["avg_duration_days"] = stage_summary["avg_duration_days"].round(2).fillna(0.0)
    stage_summary["delay_rate_pct"] = (stage_summary["delayed_count"] / stage_summary["total_assigned"] * 100).round(2)
    stage_summary["completion_rate_pct"] = (stage_summary["completed_count"] / stage_summary["total_assigned"] * 100).round(2)

    stage_summary = stage_summary.sort_values(by=["delayed_count", "avg_duration_days"], ascending=False)

    top_delayed_stage = stage_summary.iloc[0]["onboarding_stage"] if not stage_summary.empty else "None"
    top_longest_stage = stage_summary.sort_values(by="avg_duration_days", ascending=False).iloc[0]["onboarding_stage"] if not stage_summary.empty else "None"

    return {
        "total_employees": total_employees,
        "overall_completion_rate": overall_completion_rate,
        "stage_summary": stage_summary,
        "top_delayed_stage": top_delayed_stage,
        "top_longest_stage": top_longest_stage,
        "avg_onboarding_time_days": round(stage_summary["avg_duration_days"].sum(), 1)
    }

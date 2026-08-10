import pandas as pd
import numpy as np

def analyze_support_requests(cleaned_data):
    """
    Analyzes support request categories, timelines over first 30 days, MTTR resolution times, and repeated issues.
    Answers:
    1. What types of support requests are most common?
    2. Which issues take the longest to resolve?
    """
    df_sup = cleaned_data.get("support_requests", pd.DataFrame())

    if df_sup.empty:
        return {}

    total_requests = len(df_sup)
    unresolved_requests = len(df_sup[df_sup["request_status"] != "Resolved"])
    avg_resolution_hrs = float(df_sup["resolution_time"].mean()) if "resolution_time" in df_sup.columns else 0.0

    # Category summary
    if "resolution_time" not in df_sup.columns:
        df_sup["resolution_time"] = 0.0

    cat_summary = df_sup.groupby("request_category").agg(
        total_requests=("employee_id", "count"),
        unresolved_count=("request_status", lambda x: (x != "Resolved").sum()),
        avg_resolution_hours=("resolution_time", "mean")
    ).reset_index()

    cat_summary["avg_resolution_hours"] = cat_summary["avg_resolution_hours"].round(2).fillna(0.0)
    cat_summary = cat_summary.sort_values(by="total_requests", ascending=False)

    most_common_category = cat_summary.iloc[0]["request_category"] if not cat_summary.empty else "None"
    slowest_category = cat_summary.sort_values(by="avg_resolution_hours", ascending=False).iloc[0]["request_category"] if not cat_summary.empty else "None"

    # Support requests over first 30 days
    timeline_df = pd.DataFrame()
    if "days_since_joining" in df_sup.columns:
        timeline_df = df_sup.groupby(["days_since_joining", "request_category"]).size().reset_index(name="request_count")

    # Repeated issues per employee
    emp_cat_counts = df_sup.groupby(["employee_id", "request_category"]).size().reset_index(name="count")
    repeated_issues_count = int((emp_cat_counts[emp_cat_counts["count"] > 1]["count"] - 1).sum())

    return {
        "total_requests": total_requests,
        "unresolved_requests": unresolved_requests,
        "avg_resolution_hrs": round(avg_resolution_hrs, 2),
        "cat_summary": cat_summary,
        "most_common_category": most_common_category,
        "slowest_category": slowest_category,
        "timeline_df": timeline_df,
        "repeated_issues_count": repeated_issues_count
    }

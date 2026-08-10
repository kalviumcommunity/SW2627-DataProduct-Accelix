import pandas as pd
import numpy as np

def analyze_tool_usage_friction(cleaned_data):
    """
    Analyzes internal tool usage patterns, frequency, failure rates, and support ticket overlaps.
    Answers:
    1. Which internal tools show usage problems or unusual usage patterns?
    2. Which tools are most/least used?
    """
    df_tool = cleaned_data.get("tool_usage", pd.DataFrame())
    df_sup = cleaned_data.get("support_requests", pd.DataFrame())

    if df_tool.empty:
        return {}

    # Tool level summary
    tool_summary = df_tool.groupby("tool_name").agg(
        total_usage_events=("employee_id", "count"),
        active_users=("employee_id", "nunique"),
        successful_events=("usage_status", lambda x: (x == "Success").sum()),
        failed_events=("usage_status", lambda x: (x != "Success").sum())
    ).reset_index()

    tool_summary["failure_rate_pct"] = (tool_summary["failed_events"] / tool_summary["total_usage_events"] * 100).round(2)
    tool_summary = tool_summary.sort_values(by="total_usage_events", ascending=False)

    most_used_tool = tool_summary.iloc[0]["tool_name"] if not tool_summary.empty else "None"
    least_used_tool = tool_summary.iloc[-1]["tool_name"] if not tool_summary.empty else "None"
    most_problematic_tool = tool_summary.sort_values(by="failed_events", ascending=False).iloc[0]["tool_name"] if not tool_summary.empty else "None"

    # Identify tool usage by employees who logged support tickets
    tool_support_overlap = []
    if not df_sup.empty:
        sup_emp_ids = set(df_sup["employee_id"].unique())
        tool_sup_df = df_tool[df_tool["employee_id"].isin(sup_emp_ids)]
        tool_support_overlap = tool_sup_df.groupby("tool_name").agg(
            events_by_supported_employees=("employee_id", "count"),
            failed_events=("usage_status", lambda x: (x != "Success").sum())
        ).reset_index().sort_values(by="failed_events", ascending=False)

    return {
        "tool_summary": tool_summary,
        "most_used_tool": most_used_tool,
        "least_used_tool": least_used_tool,
        "most_problematic_tool": most_problematic_tool,
        "tool_support_overlap": tool_support_overlap
    }

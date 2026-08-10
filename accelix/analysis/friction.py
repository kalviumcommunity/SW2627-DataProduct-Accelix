import pandas as pd
import numpy as np

def identify_operational_friction_points(cleaned_data):
    """
    Identifies and ranks operational friction points using evidence from:
    1. Frequency of occurrence
    2. Duration / Delay impact
    3. Number of affected employees
    4. Support dependency
    """
    df_onb = cleaned_data.get("onboarding", pd.DataFrame())
    df_tool = cleaned_data.get("tool_usage", pd.DataFrame())
    df_sup = cleaned_data.get("support_requests", pd.DataFrame())

    total_employees = max(1, df_onb["employee_id"].nunique() if not df_onb.empty else 1)

    friction_list = []

    # 1. Onboarding Stage Delays
    if not df_onb.empty:
        delayed_stages = df_onb[df_onb["stage_status"] == "Delayed"]
        for stage_name, grp in delayed_stages.groupby("onboarding_stage"):
            freq = len(grp)
            aff_emp = grp["employee_id"].nunique()
            aff_pct = round((aff_emp / total_employees) * 100, 1)

            avg_delay = grp["duration_days"].mean() if "duration_days" in grp.columns else 4.0
            avg_delay = round(float(avg_delay) if pd.notnull(avg_delay) else 4.0, 1)

            friction_score = round(freq * (aff_emp / total_employees) * (1 + avg_delay / 5.0) * 10.0, 1)

            friction_list.append({
                "friction_point": f"Onboarding Stage Delay: {stage_name}",
                "source": "Onboarding Progress",
                "frequency": freq,
                "affected_employees": aff_emp,
                "affected_pct": aff_pct,
                "impact_metric": f"{avg_delay} days average completion time",
                "friction_score": friction_score,
                "evidence": f"{freq} delayed stage assignments affecting {aff_pct}% of new hires.",
                "productivity_impact": "Slows down progression to subsequent onboarding milestones and initial team contribution."
            })

    # 2. Internal Tool Errors & Failures
    if not df_tool.empty:
        failed_tools = df_tool[df_tool["usage_status"] != "Success"]
        for tool_name, grp in failed_tools.groupby("tool_name"):
            freq = len(grp)
            aff_emp = grp["employee_id"].nunique()
            aff_pct = round((aff_emp / total_employees) * 100, 1)

            fail_rate = round((freq / len(df_tool[df_tool["tool_name"] == tool_name])) * 100, 1)

            friction_score = round(freq * (aff_emp / total_employees) * (1 + fail_rate / 20.0) * 8.0, 1)

            friction_list.append({
                "friction_point": f"Tool Usage Failure: {tool_name}",
                "source": "Internal Tool Usage",
                "frequency": freq,
                "affected_employees": aff_emp,
                "affected_pct": aff_pct,
                "impact_metric": f"{fail_rate}% usage error rate",
                "friction_score": friction_score,
                "evidence": f"{freq} failed/timeout access events across {aff_pct}% of new hires.",
                "productivity_impact": "Blocks daily operational workflows and creates login/authentication downtime."
            })

    # 3. High Support Request Dependency
    if not df_sup.empty:
        for cat_name, grp in df_sup.groupby("request_category"):
            freq = len(grp)
            aff_emp = grp["employee_id"].nunique()
            aff_pct = round((aff_emp / total_employees) * 100, 1)

            avg_mttr = grp["resolution_time"].mean() if "resolution_time" in grp.columns else 8.0
            avg_mttr = round(float(avg_mttr) if pd.notnull(avg_mttr) else 8.0, 1)

            friction_score = round(freq * (aff_emp / total_employees) * (1 + avg_mttr / 12.0) * 9.0, 1)

            friction_list.append({
                "friction_point": f"Support Dependency: {cat_name}",
                "source": "Support Requests",
                "frequency": freq,
                "affected_employees": aff_emp,
                "affected_pct": aff_pct,
                "impact_metric": f"{avg_mttr} hours MTTR resolution time",
                "friction_score": friction_score,
                "evidence": f"{freq} helpdesk requests logged with average resolution time of {avg_mttr} hrs.",
                "productivity_impact": "Indicates IT access barriers that halt work until helpdesk tickets are resolved."
            })

    df_friction = pd.DataFrame(friction_list)
    if not df_friction.empty:
        df_friction = df_friction.sort_values(by="friction_score", ascending=False).reset_index(drop=True)

    return df_friction

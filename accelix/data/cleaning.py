import pandas as pd
import numpy as np

def clean_and_normalize_data(data):
    """
    Cleans datasets, aligns Day 0 (joining_date) as earliest start_date per employee,
    and restricts all events strictly to the FIRST 30 DAYS window.
    """
    df_onboarding = data["onboarding"].copy()
    df_tool = data["tool_usage"].copy()
    df_support = data["support_requests"].copy()

    # Ensure optional columns exist across datasets
    if not df_onboarding.empty:
        if "completion_date" not in df_onboarding.columns:
            df_onboarding["completion_date"] = pd.NaT
        if "stage_status" not in df_onboarding.columns:
            df_onboarding["stage_status"] = "In Progress"

    if not df_tool.empty:
        if "usage_status" not in df_tool.columns:
            df_tool["usage_status"] = "Success"
        if "usage_activity" not in df_tool.columns:
            df_tool["usage_activity"] = "General Activity"

    if not df_support.empty:
        if "resolution_time" not in df_support.columns:
            df_support["resolution_time"] = np.nan
        if "request_status" not in df_support.columns:
            df_support["request_status"] = "Pending"

    # 1. Determine Day 0 (joining_date) per employee as earliest start_date or event_date
    emp_start_dates = {}
    if not df_onboarding.empty and "start_date" in df_onboarding.columns:
        df_onboarding["start_date"] = pd.to_datetime(df_onboarding["start_date"])
        df_onboarding["completion_date"] = pd.to_datetime(df_onboarding["completion_date"])
        
        onb_starts = df_onboarding.groupby("employee_id")["start_date"].min().to_dict()
        emp_start_dates.update(onb_starts)

    if not df_tool.empty and "usage_date" in df_tool.columns:
        df_tool["usage_date"] = pd.to_datetime(df_tool["usage_date"])
        tool_starts = df_tool.groupby("employee_id")["usage_date"].min().dt.floor('D').to_dict()
        for emp, d in tool_starts.items():
            if emp not in emp_start_dates or d < emp_start_dates[emp]:
                emp_start_dates[emp] = d

    if not df_support.empty and "request_date" in df_support.columns:
        df_support["request_date"] = pd.to_datetime(df_support["request_date"])
        sup_starts = df_support.groupby("employee_id")["request_date"].min().dt.floor('D').to_dict()
        for emp, d in sup_starts.items():
            if emp not in emp_start_dates or d < emp_start_dates[emp]:
                emp_start_dates[emp] = d

    # 2. Filter Onboarding Stages (Strictly within Day 0 to 30)
    if not df_onboarding.empty:
        df_onboarding["joining_date"] = df_onboarding["employee_id"].map(emp_start_dates)
        df_onboarding = df_onboarding[df_onboarding["joining_date"].notnull()].copy()
        
        df_onboarding["days_since_joining"] = (df_onboarding["start_date"] - df_onboarding["joining_date"]).dt.days
        df_onboarding = df_onboarding[(df_onboarding["days_since_joining"] >= 0) & (df_onboarding["days_since_joining"] <= 30)].copy()

        # Compute stage duration days
        df_onboarding["duration_days"] = np.where(
            df_onboarding["completion_date"].notnull(),
            (df_onboarding["completion_date"] - df_onboarding["start_date"]).dt.days,
            np.nan
        )

    # 3. Filter Tool Usage Events (Strictly within Day 0 to 30)
    if not df_tool.empty and "usage_date" in df_tool.columns:
        df_tool["joining_date"] = df_tool["employee_id"].map(emp_start_dates)
        df_tool = df_tool[df_tool["joining_date"].notnull()].copy()

        df_tool["days_since_joining"] = (df_tool["usage_date"] - df_tool["joining_date"]).dt.days
        df_tool = df_tool[(df_tool["days_since_joining"] >= 0) & (df_tool["days_since_joining"] <= 30)].copy()

    # 4. Filter Support Requests (Strictly within Day 0 to 30)
    if not df_support.empty and "request_date" in df_support.columns:
        df_support["joining_date"] = df_support["employee_id"].map(emp_start_dates)
        df_support = df_support[df_support["joining_date"].notnull()].copy()

        df_support["days_since_joining"] = (df_support["request_date"] - df_support["joining_date"]).dt.days
        df_support = df_support[(df_support["days_since_joining"] >= 0) & (df_support["days_since_joining"] <= 30)].copy()
        df_support["resolution_time"] = pd.to_numeric(df_support["resolution_time"], errors="coerce").fillna(0.0).clip(lower=0.0)

    return {
        "onboarding": df_onboarding,
        "tool_usage": df_tool,
        "support_requests": df_support
    }

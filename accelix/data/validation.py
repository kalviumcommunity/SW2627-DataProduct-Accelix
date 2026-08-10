import pandas as pd
import numpy as np

REQUIRED_COLUMNS = {
    "onboarding": ["employee_id", "onboarding_stage", "start_date"],
    "tool_usage": ["employee_id", "tool_name", "usage_date"],
    "support_requests": ["employee_id", "request_category", "request_date"]
}

def validate_uploaded_csv(df, target_table):
    """
    Validates user-uploaded CSV DataFrame against required schema for target_table.
    Returns clean DataFrame or raises ValueError with actionable message.
    """
    if df.empty:
        raise ValueError("Uploaded CSV file is completely empty.")

    # Strip whitespaces from column names
    df.columns = [str(col).strip() for col in df.columns]

    req_cols = REQUIRED_COLUMNS.get(target_table, [])
    missing = [col for col in req_cols if col not in df.columns]

    if missing:
        raise ValueError(
            f"Uploaded CSV for '{target_table}' is missing required column(s): {missing}. "
            f"Required columns are: {req_cols}"
        )

    # Clean string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    return df

def validate_dataset(data):
    """
    Audits dataset quality across onboarding, tool_usage, and support_requests datasets.
    """
    audit = {
        "missing_employee_ids": 0,
        "duplicate_records": 0,
        "invalid_timestamps": 0,
        "negative_resolution_times": 0,
        "warnings": []
    }

    df_onboarding = data.get("onboarding", pd.DataFrame()).copy()
    df_tool = data.get("tool_usage", pd.DataFrame()).copy()
    df_support = data.get("support_requests", pd.DataFrame()).copy()

    # 1. Missing Employee IDs
    for tbl_name, df in [("onboarding", df_onboarding), ("tool_usage", df_tool), ("support_requests", df_support)]:
        if df.empty or "employee_id" not in df.columns:
            continue
        null_cnt = df["employee_id"].isnull().sum()
        if null_cnt > 0:
            audit["missing_employee_ids"] += int(null_cnt)
            audit["warnings"].append(f"Found {null_cnt} missing employee_ids in table '{tbl_name}'.")

    # 2. Duplicate Records Check & Deduplication
    clean_data = {}
    for tbl_name, df in [("onboarding", df_onboarding), ("tool_usage", df_tool), ("support_requests", df_support)]:
        if df.empty:
            clean_data[tbl_name] = df
            continue
        dups = df.duplicated().sum()
        if dups > 0:
            audit["duplicate_records"] += int(dups)
            audit["warnings"].append(f"Deduplicated {dups} duplicate records from '{tbl_name}'.")
        clean_data[tbl_name] = df.drop_duplicates()

    # 3. Timestamp Validity (completion_date >= start_date)
    df_onb = clean_data.get("onboarding", pd.DataFrame())
    if not df_onb.empty and "start_date" in df_onb.columns and "completion_date" in df_onb.columns:
        invalid_onb = df_onb[
            (df_onb["completion_date"].notnull()) & 
            (df_onb["start_date"].notnull()) & 
            (pd.to_datetime(df_onb["completion_date"], errors="coerce") < pd.to_datetime(df_onb["start_date"], errors="coerce"))
        ]
        audit["invalid_timestamps"] += len(invalid_onb)

    # 4. Resolution Time Validity
    df_sup = clean_data.get("support_requests", pd.DataFrame())
    if not df_sup.empty and "resolution_time" in df_sup.columns:
        neg_res = (pd.to_numeric(df_sup["resolution_time"], errors="coerce") < 0).sum()
        audit["negative_resolution_times"] += int(neg_res)

    return audit, clean_data

import json
import os
from datetime import datetime

import numpy as np
import pandas as pd


OUTPUT_DIR = "output"
RAW_INPUT_FILE = "data/raw/data_with_dupes.csv"
DEDUP_OUTPUT_FILE = "data/processed/deduplicated_data.csv"
AUDIT_FILE = os.path.join(OUTPUT_DIR, "removed_duplicates_audit.csv")
AUDIT_SUMMARY_FILE = os.path.join(OUTPUT_DIR, "dedup_audit_summary.json")
DEDUP_SUMMARY_FILE = os.path.join(OUTPUT_DIR, "dedup_summary.json")


os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DEDUP_OUTPUT_FILE), exist_ok=True)


def _ensure_source_tracking(df):
    """Attach a stable source row id for audit logging."""
    tracked = df.copy()
    if "_source_row_id" not in tracked.columns:
        tracked["_source_row_id"] = np.arange(len(tracked))
    return tracked


def _row_hashes(df):
    """Compute deterministic row hashes for exact-match comparison."""
    return pd.util.hash_pandas_object(df, index=False)


def _business_columns(df):
    """Return the data columns used for duplicate comparisons."""
    return [column for column in df.columns if column not in {"_source_row_id", "_row_hash", "_null_count"}]


def detect_exact_duplicates(df):
    """
    Find rows where all values are identical.

    Returns: Tuple of (count, duplicate_rows_dataframe)
    """
    working = df.copy()
    business_cols = _business_columns(working)
    working["_row_hash"] = _row_hashes(working[business_cols])

    exact_dups = working[business_cols].duplicated().sum()
    dup_rows = working[working[business_cols].duplicated(keep=False)].sort_values(by=business_cols)

    print("\nEXACT DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Exact duplicates found: {exact_dups}")
    print(f"Total duplicate rows (including originals): {len(dup_rows)}")

    if len(dup_rows) > 0:
        print("\nSample duplicate rows:")
        print(dup_rows.head(10).to_string(index=False))

    return exact_dups, dup_rows.drop(columns=["_row_hash"], errors="ignore")


def detect_near_duplicates(df, key_columns):
    """
    Find rows with same key values but different other fields.

    Args:
        df: Input DataFrame
        key_columns: Columns defining uniqueness (e.g., ['customer_id', 'date'])

    Returns:
        DataFrame showing near-duplicates grouped by key
    """
    working = df.copy()
    business_cols = _business_columns(working)
    working["_row_hash"] = _row_hashes(working[business_cols])
    duplicate_keys = working[working.duplicated(subset=key_columns, keep=False)]

    print("\nNEAR-DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Records with duplicate keys: {len(duplicate_keys)}")
    print(f"Unique key combinations with duplicates: {len(duplicate_keys.groupby(key_columns))}")

    if len(duplicate_keys) > 0:
        print("\nSample groups with duplicate keys:")
        for keys, group in list(duplicate_keys.groupby(key_columns))[:3]:
            print(f"\n  Key: {keys}")
            print(f"  Records in group: {len(group)}")
            print(f"  Distinct row hashes: {group['_row_hash'].nunique()}")
            print(group.drop(columns=["_row_hash"]).to_string(index=False))

    return duplicate_keys.drop(columns=["_row_hash"], errors="ignore")


def remove_exact_duplicates(df, keep="first"):
    """
    Remove exact duplicates, choosing which record to keep.

    Args:
        df: Input DataFrame
        keep: 'first' (keep oldest), 'last' (keep newest), or False (remove all)

    Returns:
        Deduplicated DataFrame with row counts documented
    """
    rows_before = len(df)

    business_cols = _business_columns(df)
    df_dedup = df.drop_duplicates(subset=business_cols, keep=keep)

    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after
    removal_pct = (rows_removed / rows_before) * 100 if rows_before else 0

    print("\nEXACT DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {rows_after:,}")
    print(f"Rows removed: {rows_removed:,} ({removal_pct:.2f}%)")

    return df_dedup


def remove_near_duplicates(df, key_columns, keep_strategy="most_complete"):
    """
    Remove near-duplicates by choosing best record.

    Args:
        df: Input DataFrame
        key_columns: Columns defining uniqueness
        keep_strategy: 'most_complete' (fewest nulls), 'first', 'last'

    Returns:
        Deduplicated DataFrame
    """
    rows_before = len(df)

    if keep_strategy == "most_complete":
        helper = df.copy()
        helper["_null_count"] = helper.isnull().sum(axis=1)
        sort_cols = list(key_columns) + ["_null_count"]
        if "_source_row_id" in helper.columns:
            sort_cols.append("_source_row_id")
        helper = helper.sort_values(by=sort_cols, ascending=True)
        df_dedup = helper.drop_duplicates(subset=key_columns, keep="first").drop(columns=["_null_count"], errors="ignore")

    elif keep_strategy == "last":
        df_dedup = df.drop_duplicates(subset=key_columns, keep="last")

    else:
        df_dedup = df.drop_duplicates(subset=key_columns, keep="first")

    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after
    removal_pct = (rows_removed / rows_before) * 100 if rows_before else 0

    print("\nNEAR-DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep_strategy}")
    print(f"Key columns: {key_columns}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {rows_after:,}")
    print(f"Rows removed: {rows_removed:,} ({removal_pct:.2f}%)")

    return df_dedup


def log_removed_duplicates(df_original, df_dedup):
    """
    Save all removed duplicate rows to audit file for compliance.

    Returns: Audit summary
    """
    if "_source_row_id" not in df_original.columns or "_source_row_id" not in df_dedup.columns:
        raise ValueError("Both DataFrames must include '_source_row_id' for audit logging.")

    removed_mask = ~df_original["_source_row_id"].isin(df_dedup["_source_row_id"])
    removed_records = df_original[removed_mask].copy()

    print("\nAUDIT LOGGING")
    print("=" * 60)
    print(f"Total records removed: {len(removed_records)}")

    removed_records.to_csv(AUDIT_FILE, index=False)
    print("✓ Removed records saved to audit file")

    audit_summary = {
        "removal_timestamp": datetime.now().isoformat(),
        "total_removed": int(len(removed_records)),
        "reason": "Duplicate detection and deduplication",
        "audit_file": AUDIT_FILE,
        "audit_note": "All removed records logged for compliance and recovery if needed",
    }

    with open(AUDIT_SUMMARY_FILE, "w", encoding="utf-8") as file_handle:
        json.dump(audit_summary, file_handle, indent=2, default=str)

    print("✓ Audit summary saved")
    print("=" * 60)

    return removed_records, audit_summary


def compare_before_after(df_original, df_dedup):
    """
    Log before/after metrics confirming deduplication worked.

    Returns: Comparison dictionary
    """
    comparison = {
        "rows_before": len(df_original),
        "rows_after": len(df_dedup),
        "rows_removed": len(df_original) - len(df_dedup),
        "removal_percentage": round(((len(df_original) - len(df_dedup)) / len(df_original)) * 100, 2)
        if len(df_original)
        else 0,
        "columns": len(df_original.columns),
        "nulls_before": int(df_original.isnull().sum().sum()),
        "nulls_after": int(df_dedup.isnull().sum().sum()),
        "timestamp": datetime.now().isoformat(),
    }

    print("\n" + "=" * 70)
    print("DEDUPLICATION FINAL SUMMARY")
    print("=" * 70)
    print(f"Rows before: {comparison['rows_before']:,}")
    print(f"Rows after:  {comparison['rows_after']:,}")
    print(f"Removed:     {comparison['rows_removed']:,} ({comparison['removal_percentage']}%)")
    print(f"\nNulls before: {comparison['nulls_before']:,}")
    print(f"Nulls after:  {comparison['nulls_after']:,}")
    print(f"Null change:  {comparison['nulls_before'] - comparison['nulls_after']:,}")
    print("=" * 70)

    with open(DEDUP_SUMMARY_FILE, "w", encoding="utf-8") as file_handle:
        json.dump(comparison, file_handle, indent=2)

    return comparison


if __name__ == "__main__":
    df_original = pd.read_csv(RAW_INPUT_FILE)
    df_original = _ensure_source_tracking(df_original)

    print("\n" + "=" * 70)
    print("STARTING DEDUPLICATION WORKFLOW")
    print("=" * 70)
    print(f"Initial record count: {len(df_original):,}")

    print("\n[Step 1/4] Detecting exact duplicates...")
    exact_count, exact_rows = detect_exact_duplicates(df_original)

    print("\n[Step 2/4] Detecting near-duplicates by key...")
    near_dups = detect_near_duplicates(df_original, key_columns=["customer_id", "transaction_date"])

    print("\n[Step 3/4] Removing exact duplicates (keeping first)...")
    df_dedup = remove_exact_duplicates(df_original, keep="first")

    print("\n[Step 4/4] Removing near-duplicates (keeping most complete)...")
    df_dedup = remove_near_duplicates(
        df_dedup,
        key_columns=["customer_id", "transaction_date"],
        keep_strategy="most_complete",
    )

    print("\n[Audit] Logging removed records for compliance...")
    removed_records, audit_summary = log_removed_duplicates(df_original, df_dedup)

    compare_before_after(
        df_original.drop(columns=["_source_row_id"], errors="ignore"),
        df_dedup.drop(columns=["_source_row_id"], errors="ignore"),
    )

    df_output = df_dedup.drop(columns=["_source_row_id"], errors="ignore")
    df_output.to_csv(DEDUP_OUTPUT_FILE, index=False)
    print(f"\n✓ Deduplicated data saved to {DEDUP_OUTPUT_FILE}")
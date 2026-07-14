"""
Multi-Source Merging & Join Validation Pipeline
=================================================
This script merges customer and order datasets using explicit join types,
validates row counts and key multiplicity before and after, detects and
isolates unmatched keys (orphaned orders and inactive customers), saves
unmatched records to CSV for investigation, and generates a structured
audit report.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Ensure stdout and stderr support UTF-8 on Windows environments
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration and Constants
OUTPUT_DIR = "output"
PROCESSED_DIR = "data/processed"
RAW_DIR = "data/raw"

RAW_CUSTOMERS_FILE = os.path.join(RAW_DIR, "customers_validation.csv")
RAW_ORDERS_FILE = os.path.join(RAW_DIR, "orders_validation.csv")

PROCESSED_OUTPUT_FILE = os.path.join(PROCESSED_DIR, "clean_merged_data.csv")
UNMATCHED_CUSTOMERS_FILE = os.path.join(OUTPUT_DIR, "unmatched_customers.csv")
UNMATCHED_ORDERS_FILE = os.path.join(OUTPUT_DIR, "unmatched_orders.csv")
VALIDATION_REPORT_FILE = os.path.join(OUTPUT_DIR, "join_validation_report.json")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)


def build_sample_datasets():
    """
    Generate synthetic customer and order datasets matching the 6,200 row count
    left-join scenario with duplicate multiplicity and unmatched keys.
    
    Returns:
        df_customers, df_orders: Pandas DataFrames.
    """
    print("Generating synthetic datasets for join validation...")
    
    # 1. Customers Dataset (1,000 rows, 100 duplicated customer IDs)
    uniq_ids = list(range(1001, 1801))  # 800 unique IDs
    dup_ids = list(range(1801, 1901)) * 2  # 100 IDs duplicated (200 rows)
    
    customer_rows = []
    # Unique customers
    for cid in uniq_ids:
        customer_rows.append({
            "customer_id": cid,
            "name": f"Customer_{cid}",
            "email": f"customer_{cid}@example.com",
            "signup_date": f"2025-{1 + (cid % 12):02d}-{1 + (cid % 28):02d}"
        })
    # Duplicated customers (representing update history or duplicate registration anomalies)
    for i, cid in enumerate(dup_ids):
        email_suffix = "a" if i % 2 == 0 else "b"
        customer_rows.append({
            "customer_id": cid,
            "name": f"Customer_{cid}",
            "email": f"customer_{cid}_{email_suffix}@example.com",
            "signup_date": f"2025-01-{1 + (i % 28):02d}"
        })
        
    df_customers = pd.DataFrame(customer_rows)
    df_customers = df_customers.sort_values("customer_id").reset_index(drop=True)
    
    # 2. Orders Dataset (5,000 rows, 500 orphaned orders)
    order_rows = []
    order_id_counter = 100001
    
    # 100 duplicated customer IDs get 1,550 orders total (50 get 15, 50 get 16)
    for idx, cid in enumerate(range(1801, 1901)):
        num_orders = 15 if idx < 50 else 16
        for _ in range(num_orders):
            order_rows.append({
                "order_id": order_id_counter,
                "customer_id": cid,
                "amount": round(float(10 + (order_id_counter % 990)), 2),
                "order_date": f"2025-02-{1 + (order_id_counter % 28):02d}"
            })
            order_id_counter += 1
            
    # 650 active unique customer IDs get 2,950 orders total (300 get 4, 350 get 5)
    active_uniq_cids = uniq_ids[:650]  # IDs 1001 to 1650
    for idx, cid in enumerate(active_uniq_cids):
        num_orders = 4 if idx < 300 else 5
        for _ in range(num_orders):
            order_rows.append({
                "order_id": order_id_counter,
                "customer_id": cid,
                "amount": round(float(10 + (order_id_counter % 990)), 2),
                "order_date": f"2025-03-{1 + (order_id_counter % 28):02d}"
            })
            order_id_counter += 1
            
    # 500 orphaned orders (non-existent customer IDs from 2001 to 2500)
    for cid in range(2001, 2501):
        order_rows.append({
            "order_id": order_id_counter,
            "customer_id": cid,
            "amount": round(float(10 + (order_id_counter % 990)), 2),
            "order_date": f"2025-04-{1 + (order_id_counter % 28):02d}"
        })
        order_id_counter += 1
        
    df_orders = pd.DataFrame(order_rows)
    df_orders = df_orders.sort_values("order_id").reset_index(drop=True)
    
    return df_customers, df_orders


def validate_keys_pre_merge(df_left, df_right, key):
    """
    Perform key validation and cardinality profiling prior to joining.
    
    Args:
        df_left (pd.DataFrame): Customers table (left input).
        df_right (pd.DataFrame): Orders table (right input).
        key (str): Join key.
        
    Returns:
        dict: Summary of key overlaps and duplication issues.
    """
    left_keys = df_left[key]
    right_keys = df_right[key]
    
    left_total = len(df_left)
    left_unique = left_keys.nunique()
    left_dups = left_total - left_unique
    
    right_total = len(df_right)
    right_unique = right_keys.nunique()
    right_dups = right_total - right_unique
    
    left_set = set(left_keys.dropna())
    right_set = set(right_keys.dropna())
    
    overlap = left_set.intersection(right_set)
    unmatched_left = left_set - right_set
    unmatched_right = right_set - left_set
    
    print("\n" + "=" * 70)
    print("PRE-MERGE JOIN KEY DIAGNOSTIC REPORT")
    print("=" * 70)
    print(f"Left Table (Customers): {left_total} rows")
    print(f"  - Unique Keys: {left_unique}")
    print(f"  - Duplicate Keys (Potential Multiplicity): {left_dups}")
    print(f"Right Table (Orders): {right_total} rows")
    print(f"  - Unique Keys: {right_unique}")
    print(f"  - Duplicate Keys (Expected Multiplicity): {right_dups}")
    print(f"Overlap and Mismatch Diagnostics:")
    print(f"  - Shared Unique Keys: {len(overlap)}")
    print(f"  - Unmatched Left Keys (Inactive Customers): {len(unmatched_left)}")
    print(f"  - Unmatched Right Keys (Orphaned Orders): {len(unmatched_right)}")
    print("=" * 70)
    
    return {
        "left_table": {
            "total_rows": left_total,
            "unique_keys_count": left_unique,
            "duplicate_keys_count": left_dups,
            "has_key_duplicates": left_dups > 0
        },
        "right_table": {
            "total_rows": right_total,
            "unique_keys_count": right_unique,
            "duplicate_keys_count": right_dups,
            "has_key_duplicates": right_dups > 0
        },
        "key_overlap_summary": {
            "shared_unique_keys": len(overlap),
            "unmatched_left_keys": len(unmatched_left),
            "unmatched_right_keys": len(unmatched_right)
        }
    }


def execute_explicit_joins(df_customers, df_orders, key):
    """
    Execute and profile all four major join types.
    
    Args:
        df_customers: Customers DataFrame.
        df_orders: Orders DataFrame.
        key: Join key.
        
    Returns:
        dict: Dictionary of join results (join_type -> DataFrame) and metadata.
    """
    join_types = ['inner', 'left', 'right', 'outer']
    results = {}
    metadata = {}
    
    print("\nExecuting explicit merges for all join types...")
    for jt in join_types:
        df_merged = pd.merge(df_customers, df_orders, on=key, how=jt)
        results[jt] = df_merged
        
        # Calculate size comparison
        expected_if_one_to_one = max(len(df_customers), len(df_orders))
        row_diff_from_max = len(df_merged) - expected_if_one_to_one
        
        print(f"  - {jt.capitalize()} Join: {len(df_merged)} rows (Change vs max input: {row_diff_from_max:+d})")
        
        metadata[jt] = {
            "row_count": len(df_merged),
            "columns_count": len(df_merged.columns),
            "change_vs_max_input": row_diff_from_max
        }
        
    return results, metadata


def main():
    # Step 1: Load or build raw datasets
    if os.path.exists(RAW_CUSTOMERS_FILE) and os.path.exists(RAW_ORDERS_FILE):
        print(f"Loading raw datasets from {RAW_DIR}...")
        df_customers = pd.read_csv(RAW_CUSTOMERS_FILE)
        df_orders = pd.read_csv(RAW_ORDERS_FILE)
    else:
        df_customers, df_orders = build_sample_datasets()
        df_customers.to_csv(RAW_CUSTOMERS_FILE, index=False)
        df_orders.to_csv(RAW_ORDERS_FILE, index=False)
        print(f"Saved synthetic datasets to {RAW_DIR}")

    # Step 2: Validate keys pre-merge
    pre_merge_diag = validate_keys_pre_merge(df_customers, df_orders, "customer_id")

    # Step 3: Run joins and compare row counts
    join_results, join_metadata = execute_explicit_joins(df_customers, df_orders, "customer_id")

    # Step 4: Identify and isolate unmatched keys
    # Customers with no orders (left join null indicators or isin negation)
    unmatched_customers = df_customers[
        ~df_customers['customer_id'].isin(df_orders['customer_id'])
    ]
    
    # Orders with no matching customer ID (orphaned orders)
    unmatched_orders = df_orders[
        ~df_orders['customer_id'].isin(df_customers['customer_id'])
    ]
    
    # Save unmatched records for audit trail
    unmatched_customers.to_csv(UNMATCHED_CUSTOMERS_FILE, index=False)
    unmatched_orders.to_csv(UNMATCHED_ORDERS_FILE, index=False)
    
    print("\n" + "=" * 70)
    print("UNMATCHED RECORD SUMMARY")
    print("=" * 70)
    print(f"Inactive Customers (No orders): {len(unmatched_customers)} rows saved to {UNMATCHED_CUSTOMERS_FILE}")
    print(f"Orphaned Orders (No customer): {len(unmatched_orders)} rows saved to {UNMATCHED_ORDERS_FILE}")
    print("=" * 70)

    # Step 5: Document and select final merge
    # For downstream business intelligence and sales analysis:
    # A Full Outer Join is chosen as the final export.
    # Reasoning: A full outer join preserves 100% of all data points. It keeps customers who have never ordered
    # (valuable for CRM re-engagement campaigns) AND orphaned orders (which must be retained for financial/revenue
    # auditing, even if their customer profiles are missing or corrupted).
    final_join_type = "outer"
    final_merged_df = join_results[final_join_type]
    final_merged_df.to_csv(PROCESSED_OUTPUT_FILE, index=False)
    print(f"✓ Final merged dataset ({final_join_type} join) saved to {PROCESSED_OUTPUT_FILE} ({len(final_merged_df)} rows)")

    # Step 6: Write structured JSON report
    report = {
        "timestamp": datetime.now().isoformat(),
        "input_files": {
            "customers": RAW_CUSTOMERS_FILE,
            "orders": RAW_ORDERS_FILE
        },
        "output_files": {
            "final_merged_data": PROCESSED_OUTPUT_FILE,
            "unmatched_customers": UNMATCHED_CUSTOMERS_FILE,
            "unmatched_orders": UNMATCHED_ORDERS_FILE
        },
        "pre_merge_diagnostics": pre_merge_diag,
        "join_types_comparison": join_metadata,
        "unmatched_counts": {
            "inactive_customers": len(unmatched_customers),
            "orphaned_orders": len(unmatched_orders)
        },
        "final_merge_decision": {
            "selected_join_type": final_join_type,
            "resulting_row_count": len(final_merged_df),
            "business_reasoning": (
                "Full Outer Join is selected to prevent silent data loss. "
                "It retains both inactive customers (crucial for marketing campaigns and user churn analysis) "
                "and orphaned orders (critical for reconciliation and revenue audit), flagging "
                "mismatches for data quality intervention rather than filtering them out."
            )
        }
    }

    with open(VALIDATION_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"✓ Structured join validation report saved to {VALIDATION_REPORT_FILE}")
    print("\nJoin validation pipeline completed successfully!")


if __name__ == "__main__":
    main()

"""
Consistency & Data Validation Firewall Pipeline
==================================================
This script runs a data validation check to enforce range limits, null constraints,
formatting patterns, and business domain rules. It isolates clean and failed records,
generating a validation report for auditable and traceable data cleaning.
"""

import json
import os
import sys
import pandas as pd
from datetime import datetime

# Ensure stdout and stderr support UTF-8 on Windows environments
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration and Constants
OUTPUT_DIR = "output"
RAW_INPUT_FILE = "data/raw/consistency_validation_sample.csv"
PROCESSED_OUTPUT_FILE = "data/processed/clean_validated_data.csv"
FAILURES_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "validation_failures.csv")
VALIDATION_REPORT_FILE = os.path.join(OUTPUT_DIR, "validation_report.json")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROCESSED_OUTPUT_FILE), exist_ok=True)


def build_sample_dataset():
    """Create a synthetic dataset with validation error cases."""
    print("Generating synthetic dataset with validation error cases...")
    data = {
        "record_id": list(range(1, 11)),
        "customer_id": [
            "C101", "C102", "C103", "C104", None,
            "C105", "C106", "C107", "C108", "C109"
        ],
        "birth_date": [
            "1990-05-15", "1985-11-20", "2050-06-01", "1978-02-14", "1995-08-30",
            "2002-12-25", "1989-04-10", "1992-09-05", "1935-10-15", "1915-03-22"
        ],
        "price": [
            99.99, 150.00, 75.00, -20.00, 45.50,
            120.00, 30.00, 250.00, 65.25, 110.00
        ],
        "campaign_start_date": [
            "2025-01-01", "2025-01-05", "2025-01-10", "2025-01-12", "2025-01-15",
            "2025-01-25", "2025-01-18", "2025-01-20", "2025-01-15", "2025-01-05"
        ],
        "campaign_end_date": [
            "2025-01-10", "2025-01-12", "2025-01-15", "2025-01-20", "2025-01-22",
            "2025-01-20", "2025-01-25", "2025-01-30", "2025-01-15", "2025-01-15"
        ],
        "email": [
            "valid.email@example.com", "bob@example.com", "carol@example.com", "diana@example.com", "eric@example.com",
            "frank@example.com", "grace_example.com", "helen@example.com", "ian@example.com", "jack@example.com"
        ]
    }
    return pd.DataFrame(data)


def run_validation_checks(df):
    """
    Apply range checks, null constraints, format patterns, and business rules.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        df_checked: DataFrame containing validation flag columns.
        report_details: Summary of checks performed.
    """
    df_checked = df.copy()
    today = datetime.now()
    
    print("\nRunning Range Checks...")
    # Parse birth_date to datetime for comparison
    birth_dates = pd.to_datetime(df_checked["birth_date"], errors="coerce")
    
    # Range check birth_date: between 1920-01-01 and today
    df_checked["valid_birth_date"] = (
        (birth_dates >= pd.Timestamp("1920-01-01")) & 
        (birth_dates <= today) &
        (birth_dates.notna())
    )
    
    # Range check price: price >= 0
    df_checked["valid_price"] = df_checked["price"] >= 0

    print("Running Null Constraints...")
    # Null constraint: customer_id is not null and not blank string
    df_checked["valid_customer_id"] = (
        df_checked["customer_id"].notna() & 
        (df_checked["customer_id"].astype(str).str.strip() != "")
    )

    print("Running Format Patterns...")
    # Format pattern: email must contain '@'
    df_checked["valid_email_format"] = df_checked["email"].str.contains("@", na=False)

    print("Running Business Rules...")
    # Business rule: campaign_end_date >= campaign_start_date
    start_dates = pd.to_datetime(df_checked["campaign_start_date"], errors="coerce")
    end_dates = pd.to_datetime(df_checked["campaign_end_date"], errors="coerce")
    
    # If parsing fails, dates are invalid
    df_checked["valid_campaign_dates"] = (
        (end_dates >= start_dates) & 
        (start_dates.notna()) & 
        (end_dates.notna())
    )
    
    # Combine checks: passes all checks
    validation_columns = [
        "valid_birth_date",
        "valid_price",
        "valid_customer_id",
        "valid_email_format",
        "valid_campaign_dates"
    ]
    df_checked["passes_all_checks"] = df_checked[validation_columns].all(axis=1)
    
    # Count rules performance
    total_records = len(df_checked)
    rules_summary = {
        "range_check_birth_date": {
            "type": "Range Check",
            "description": "Birth date must be between 1920-01-01 and today.",
            "passed": int(df_checked["valid_birth_date"].sum()),
            "failed": int((~df_checked["valid_birth_date"]).sum())
        },
        "range_check_price": {
            "type": "Range Check",
            "description": "Price must be non-negative (>= 0).",
            "passed": int(df_checked["valid_price"].sum()),
            "failed": int((~df_checked["valid_price"]).sum())
        },
        "null_check_customer_id": {
            "type": "Null Constraint",
            "description": "Customer ID must not be null or blank.",
            "passed": int(df_checked["valid_customer_id"].sum()),
            "failed": int((~df_checked["valid_customer_id"]).sum())
        },
        "format_check_email": {
            "type": "Format Pattern",
            "description": "Email address must contain '@' character.",
            "passed": int(df_checked["valid_email_format"].sum()),
            "failed": int((~df_checked["valid_email_format"]).sum())
        },
        "business_check_campaign_dates": {
            "type": "Business Rule",
            "description": "Campaign end date must be on or after campaign start date.",
            "passed": int(df_checked["valid_campaign_dates"].sum()),
            "failed": int((~df_checked["valid_campaign_dates"]).sum())
        }
    }
    
    return df_checked, rules_summary, validation_columns


def main():
    # Step 1: Load or build raw dataset
    if os.path.exists(RAW_INPUT_FILE):
        print(f"Loading raw dataset from {RAW_INPUT_FILE}...")
        df = pd.read_csv(RAW_INPUT_FILE)
    else:
        df = build_sample_dataset()
        df.to_csv(RAW_INPUT_FILE, index=False)
        print(f"Saved synthetic dataset to {RAW_INPUT_FILE}")

    print("\n" + "=" * 70)
    print("STARTING DATA CONSISTENCY VALIDATION")
    print("=" * 70)
    print(f"Total input records: {len(df)}")

    # Step 2: Run validation checks
    df_checked, rules_summary, validation_cols = run_validation_checks(df)

    # Step 3: Isolate and route records
    clean_df = df_checked[df_checked["passes_all_checks"]].drop(
        columns=validation_cols + ["passes_all_checks"], errors="ignore"
    )
    
    failures_df = df_checked[~df_checked["passes_all_checks"]]
    
    # Save partitioned datasets
    clean_df.to_csv(PROCESSED_OUTPUT_FILE, index=False)
    print(f"\n✓ Clean validated data saved to {PROCESSED_OUTPUT_FILE} ({len(clean_df)} records)")
    
    failures_df.to_csv(FAILURES_OUTPUT_FILE, index=False)
    print(f"✓ Isolated validation failures saved to {FAILURES_OUTPUT_FILE} ({len(failures_df)} records)")

    # Step 4: Write structured JSON report
    total_passed = int(df_checked["passes_all_checks"].sum())
    total_failed = int((~df_checked["passes_all_checks"]).sum())
    
    # Retrieve failing record details for report audit trail
    failing_records_list = failures_df.apply(
        lambda r: {
            "record_id": int(r["record_id"]),
            "customer_id": str(r["customer_id"]) if pd.notna(r["customer_id"]) else None,
            "failed_rules": [
                col.replace("valid_", "") for col in validation_cols if not r[col]
            ]
        },
        axis=1
    ).tolist()

    report = {
        "timestamp": datetime.now().isoformat(),
        "input_file": RAW_INPUT_FILE,
        "clean_output_file": PROCESSED_OUTPUT_FILE,
        "failures_output_file": FAILURES_OUTPUT_FILE,
        "summary": {
            "total_records": len(df),
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate_percentage": round((total_passed / len(df)) * 100, 2)
        },
        "rules_assessment": rules_summary,
        "audit_failing_records": failing_records_list
    }

    with open(VALIDATION_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"✓ Structured validation report saved to {VALIDATION_REPORT_FILE}")

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Passed: {total_passed} / {len(df)}")
    print(f"Failed: {total_failed} / {len(df)}")
    print(f"Rules Breakdown:")
    for rule, details in rules_summary.items():
        print(f"  - {rule} ({details['type']}): {details['passed']} passed, {details['failed']} failed")
    print("=" * 70 + "\nConsistency check complete!")


if __name__ == "__main__":
    main()

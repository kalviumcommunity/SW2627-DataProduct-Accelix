"""
Timestamp Parser & Temporal Feature Extraction Pipeline
======================================================
This script demonstrates how to parse string-based timestamps into native
Pandas datetime objects, extract time-based features, compute recency
metrics, and perform time-series resample aggregations.
"""

import json
import os
import sys
import pandas as pd
import numpy as np

# Ensure stdout and stderr support UTF-8 on Windows environments
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration and Constants
OUTPUT_DIR = "output"
RAW_INPUT_FILE = "data/raw/unparsed_timestamps.csv"
PROCESSED_OUTPUT_FILE = "data/processed/parsed_timestamps.csv"
COMPARISON_FILE = os.path.join(OUTPUT_DIR, "timestamp_parsing_comparison.json")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "timestamp_parsing_summary.json")

# A fixed reference date for computing elapsed time (recency) consistently
REFERENCE_DATE = pd.Timestamp("2025-02-01 12:00:00")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROCESSED_OUTPUT_FILE), exist_ok=True)


def build_sample_dataset():
    """Create a synthetic dataset with unparsed string timestamps."""
    print(f"Generating synthetic dataset with unparsed timestamps...")
    data = {
        "transaction_id": list(range(1, 16)),
        "customer_id": [
            "C101", "C102", "C101", "C103", "C104",
            "C102", "C105", "C101", "C103", "C104",
            "C102", "C105", "C101", "C106", "C103"
        ],
        "amount": [
            150.50, 250.00, 99.95, 120.00, 300.25,
            45.00, 135.20, 85.00, 210.00, 75.50,
            180.00, 95.00, 110.00, 400.00, 65.25
        ],
        "transaction_date": [
            "2025-01-15 14:30:45",
            "2025-01-15 18:20:10",
            "2025-01-16 09:15:00",
            "2025-01-17 23:45:30",
            "2025-01-18 11:30:00",
            "2025-01-19 08:05:15",
            "2025-01-20 16:40:00",
            "2025-01-21 12:00:00",
            "2025-01-22 15:50:45",
            "2025-01-22 19:10:00",
            "2025-01-23 10:25:35",
            "2025-01-24 14:00:00",
            "2025-01-25 17:15:30",
            "2025-01-26 09:00:00",
            "2025-01-27 22:30:15"
        ]
    }
    return pd.DataFrame(data)


def parse_and_extract_features(df):
    """
    Parse string timestamps and extract temporal features.
    
    Args:
        df: Pandas DataFrame with transaction_date string column.
        
    Returns:
        df_parsed: DataFrame with transaction_date converted to datetime and
                   additional temporal features extracted.
        comparison_info: Dictionary containing before/after type information.
    """
    df_parsed = df.copy()
    
    # Store dtype before conversion
    dtype_before = str(df_parsed['transaction_date'].dtype)
    
    # 1. Parse string to datetime
    print("Parsing transaction_date column to datetime...")
    df_parsed['transaction_date'] = pd.to_datetime(
        df_parsed['transaction_date'],
        format='%Y-%m-%d %H:%M:%S'
    )
    
    dtype_after = str(df_parsed['transaction_date'].dtype)
    
    # 2. Extract day-of-week
    print("Extracting day-of-week features...")
    df_parsed['day_of_week'] = df_parsed['transaction_date'].dt.day_name()
    df_parsed['dow_numeric'] = df_parsed['transaction_date'].dt.dayofweek
    
    # 3. Extract hour-of-day
    print("Extracting hour-of-day...")
    df_parsed['hour'] = df_parsed['transaction_date'].dt.hour
    
    # 4. Extract week, month, and quarter
    print("Extracting week number, month, and quarter...")
    df_parsed['week_num'] = df_parsed['transaction_date'].dt.isocalendar().week.astype(int)
    df_parsed['month'] = df_parsed['transaction_date'].dt.month
    df_parsed['quarter'] = df_parsed['transaction_date'].dt.quarter
    
    # 5. Compute elapsed time (recency)
    print(f"Calculating days elapsed since purchase using reference date: {REFERENCE_DATE}...")
    df_parsed['days_since_purchase'] = (REFERENCE_DATE - df_parsed['transaction_date']).dt.days
    
    comparison_info = {
        "column_name": "transaction_date",
        "dtype_before": dtype_before,
        "dtype_after": dtype_after,
        "new_features_extracted": [
            "day_of_week",
            "dow_numeric",
            "hour",
            "week_num",
            "month",
            "quarter",
            "days_since_purchase"
        ]
    }
    
    return df_parsed, comparison_info


def perform_resample_aggregations(df):
    """
    Demonstrate time-series resampling on datetime-indexed data.
    
    Args:
        df: Pandas DataFrame with datetime transaction_date column.
        
    Returns:
        resample_summary: Dictionary containing resampled outputs.
    """
    print("Setting transaction_date as index for resample aggregations...")
    # Set datetime as index for resampling
    df_ts = df.set_index('transaction_date')
    
    # Resample weekly and sum amounts
    weekly_revenue = df_ts['amount'].resample('W').sum()
    print("\nWeekly Revenue Aggregation:")
    print(weekly_revenue.to_string())
    
    # Resample daily and sum amounts
    daily_revenue = df_ts['amount'].resample('D').sum()
    print("\nDaily Revenue Aggregation (First 5 days):")
    print(daily_revenue.head(5).to_string())
    
    # Convert resampled pandas series to dictionary format for JSON storage
    weekly_dict = {str(k.date()): float(v) for k, v in weekly_revenue.items()}
    daily_dict = {str(k.date()): float(v) for k, v in daily_revenue.items()}
    
    return {
        "weekly_revenue": weekly_dict,
        "daily_revenue": daily_dict
    }


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
    print("BEFORE PROCESSING (Raw string dates)")
    print("=" * 70)
    print(df.head(5))
    print(f"transaction_date dtype: {df['transaction_date'].dtype}\n")
    
    # Step 2: Parse and extract features
    df_parsed, comparison_info = parse_and_extract_features(df)
    
    print("\n" + "=" * 70)
    print("AFTER PROCESSING (Parsed datetime and features)")
    print("=" * 70)
    print(df_parsed.head(5))
    print(f"transaction_date dtype: {df_parsed['transaction_date'].dtype}\n")
    
    # Step 3: Resample aggregations
    resample_data = perform_resample_aggregations(df_parsed)
    
    # Step 4: Compute summaries
    hour_counts = df_parsed['hour'].value_counts().sort_index()
    dow_counts = df_parsed['day_of_week'].value_counts()
    
    summary_info = {
        "analysis_reference_date": str(REFERENCE_DATE),
        "total_records": len(df_parsed),
        "total_revenue": float(df_parsed['amount'].sum()),
        "average_days_since_purchase": float(df_parsed['days_since_purchase'].mean()),
        "peak_hours_distribution": {int(k): int(v) for k, v in hour_counts.items()},
        "day_of_week_distribution": {str(k): int(v) for k, v in dow_counts.items()},
        "resampled_aggregations": resample_data
    }
    
    # Save processed dataset
    df_parsed.to_csv(PROCESSED_OUTPUT_FILE, index=False)
    print(f"\n✓ Processed data saved to {PROCESSED_OUTPUT_FILE}")
    
    # Save comparison info
    with open(COMPARISON_FILE, "w", encoding="utf-8") as f:
        json.dump(comparison_info, f, indent=2)
    print(f"✓ Comparison details saved to {COMPARISON_FILE}")
    
    # Save summary report
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_info, f, indent=2)
    print(f"✓ Summary report saved to {SUMMARY_FILE}")
    print("=" * 70 + "\nPipeline execution complete!")


if __name__ == "__main__":
    main()

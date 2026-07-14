"""
Feature Engineering & Derived Business Columns Pipeline
=========================================================
This script aggregates transaction data to the customer level, constructs
ratio features normalizing for customer tenure and transaction volume, bins
metrics using equal-width and quantile methods, and calculates a composite
RFM (Recency, Frequency, Monetary) engagement score. It handles missing
values and infinite ranges, exporting clean features and an audit report.
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
INPUT_FILE = "data/processed/clean_merged_data.csv"
OUTPUT_FILE = "data/processed/customer_features.csv"
REPORT_FILE = "output/feature_engineering_report.json"
REFERENCE_DATE = "2026-01-01"

# Ensure directories exist
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)


def calculate_ratio_features(df):
    """
    Compute normalised customer ratios for tenure and volume.
    
    Args:
        df (pd.DataFrame): Aggregated customer DataFrame.
        
    Returns:
        pd.DataFrame: DataFrame enriched with ratio features.
    """
    print("Calculating ratio features...")
    
    # 1. Transactions per month = total_transactions / (days_as_customer / 30)
    # Handle days_as_customer being null (orphaned orders) or 0 (new signups)
    df['transactions_per_month'] = df['total_transactions'] / (df['days_as_customer'] / 30.0)
    
    # 2. Avg spend per transaction = total_spent / total_transactions
    df['avg_spend_per_transaction'] = df['total_spent'] / df['total_transactions']
    
    # 3. Lifetime value per month = total_spent / (days_as_customer / 30)
    df['lifetime_value_per_month'] = df['total_spent'] / (df['days_as_customer'] / 30.0)
    
    # Standardise infinite values (division by zero) or NaNs to 0
    ratio_columns = ['transactions_per_month', 'avg_spend_per_transaction', 'lifetime_value_per_month']
    for col in ratio_columns:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        
    return df


def apply_categorical_binning(df):
    """
    Bin customer metrics into business-friendly engagement and spend tiers.
    
    Args:
        df (pd.DataFrame): Customer DataFrame with ratio features.
        
    Returns:
        pd.DataFrame: DataFrame enriched with binned categorical columns.
    """
    print("Applying categorical binning rules...")
    
    # 1. Fixed-width / rule-based binning: Engagement Bin
    # Bins: [-0.01, 2, 10, inf] -> low, medium, high
    # We start bins at -0.01 so 0.0 values (inactive customers) are correctly binned into 'low'
    df['engagement_bin_equal'] = pd.cut(
        df['transactions_per_month'],
        bins=[-0.01, 2.0, 10.0, float('inf')],
        labels=['low', 'medium', 'high']
    )
    
    # 2. Quantile-based / equal-frequency binning: Spend Tier
    # q=4 divides total_spent into 4 quantiles: tier_1 (lowest 25%) to tier_4 (highest 25%)
    # If the customer has never spent anything (total_spent = 0), they will be placed in tier_1
    df['spend_tier_quantile'] = pd.qcut(
        df['total_spent'].rank(method='first'),  # Rank method ensures unique edges for qcut stability
        q=4,
        labels=['tier_1', 'tier_2', 'tier_3', 'tier_4']
    )
    
    return df


def calculate_rfm_score(df):
    """
    Calculate Recency, Frequency, and Monetary scores and combine into a composite RFM score.
    
    Args:
        df (pd.DataFrame): Customer DataFrame.
        
    Returns:
        pd.DataFrame: DataFrame enriched with RFM scores.
    """
    print("Computing composite RFM scores...")
    
    # Recency: Smaller days_since_last_purchase is better -> higher recency score
    # We fill NaNs (inactive customers) with 9999 (lowest recency) so they receive a score of 1
    recency_filled = df['days_since_last_purchase'].fillna(9999.0)
    df['recency_score'] = pd.qcut(
        recency_filled.rank(method='first'),
        q=5,
        labels=[5, 4, 3, 2, 1]  # Most recent (smallest days) gets 5; least recent gets 1
    ).astype(int)
    
    # Frequency: Larger transactions count is better -> higher frequency score
    df['frequency_score'] = pd.qcut(
        df['total_transactions'].rank(method='first'),
        q=5,
        labels=[1, 2, 3, 4, 5]  # Most transactions gets 5
    ).astype(int)
    
    # Monetary: Larger spend amount is better -> higher monetary score
    df['monetary_score'] = pd.qcut(
        df['total_spent'].rank(method='first'),
        q=5,
        labels=[1, 2, 3, 4, 5]  # Most spent gets 5
    ).astype(int)
    
    # Composite Score
    df['rfm_score'] = df['recency_score'] + df['frequency_score'] + df['monetary_score']
    
    return df


def main():
    print(f"Loading merged dataset from {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file {INPUT_FILE} does not exist. Please run merge_and_validate.py first.")
        sys.exit(1)
        
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} rows from merge output.")
    
    # Parse dates
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    
    ref_date = pd.Timestamp(REFERENCE_DATE)
    print(f"Using reference date: {REFERENCE_DATE} for customer tenure and recency calculations.")
    
    # Step 1: Group-by aggregation to customer level (1 row per unique customer_id)
    print("Aggregating transactional records to customer level...")
    cust_df = df.groupby("customer_id").agg(
        name=("name", "first"),
        email=("email", "first"),
        signup_date=("signup_date", "first"),
        total_spent=("amount", "sum"),
        total_transactions=("order_id", "count"),
        last_purchase_date=("order_date", "max")
    ).reset_index()
    
    # Step 2: Compute Tenure (days as customer) and Recency (days since last purchase)
    cust_df["days_as_customer"] = (ref_date - cust_df["signup_date"]).dt.days
    cust_df["days_since_last_purchase"] = (ref_date - cust_df["last_purchase_date"]).dt.days
    
    # Step 3: Calculate ratios
    cust_df = calculate_ratio_features(cust_df)
    
    # Step 4: Apply categorical binning
    cust_df = apply_categorical_binning(cust_df)
    
    # Step 5: Compute RFM score
    cust_df = calculate_rfm_score(cust_df)
    
    # Step 6: Save output dataset
    cust_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✓ Engineered features saved to {OUTPUT_FILE} ({len(cust_df)} rows)")
    
    # Step 7: Write structured validation report
    # Calculate feature statistics and value counts for validation
    engagement_counts = cust_df['engagement_bin_equal'].value_counts().to_dict()
    spend_tier_counts = cust_df['spend_tier_quantile'].value_counts().to_dict()
    rfm_score_distribution = cust_df['rfm_score'].value_counts().sort_index().to_dict()
    
    # Convert keys to strings for JSON safety
    engagement_counts = {str(k): int(v) for k, v in engagement_counts.items()}
    spend_tier_counts = {str(k): int(v) for k, v in spend_tier_counts.items()}
    rfm_score_distribution = {str(k): int(v) for k, v in rfm_score_distribution.items()}
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "input_file": INPUT_FILE,
        "output_file": OUTPUT_FILE,
        "reference_date": REFERENCE_DATE,
        "summary": {
            "total_customers": len(cust_df),
            "missing_signup_date_count": int(cust_df["signup_date"].isnull().sum()),
            "missing_last_purchase_count": int(cust_df["last_purchase_date"].isnull().sum()),
            "total_revenue": float(cust_df["total_spent"].sum()),
            "total_transactions": int(cust_df["total_transactions"].sum())
        },
        "distributions": {
            "engagement_bin_equal": engagement_counts,
            "spend_tier_quantile": spend_tier_counts,
            "rfm_score_composite": rfm_score_distribution
        },
        "feature_definitions": [
            {
                "feature": "transactions_per_month",
                "type": "Ratio",
                "business_reasoning": "Normalises order frequencies over time, reflecting correct activity velocity independent of tenure."
            },
            {
                "feature": "avg_spend_per_transaction",
                "type": "Ratio",
                "business_reasoning": "Measures average monetary ticket size per transaction."
            },
            {
                "feature": "lifetime_value_per_month",
                "type": "Ratio",
                "business_reasoning": "Normalises cumulative customer revenue over time, reflecting rate of LTV generation."
            },
            {
                "feature": "engagement_bin_equal",
                "type": "Binned / Categorical",
                "business_reasoning": "Fixed-threshold segmentation of transaction velocity into Low (<2), Medium (2-10), and High (>10) engagement categories."
            },
            {
                "feature": "spend_tier_quantile",
                "type": "Binned / Categorical",
                "business_reasoning": "Quantile segmentation (q=4) of customer spend to partition customer base into equal-sized value cohorts."
            },
            {
                "feature": "rfm_score",
                "type": "Composite Score",
                "business_reasoning": "Blends Recency, Frequency, and Monetary scores (each ranked into 1-5 scales) to create a single customer health metric ranging from 3 to 15."
            }
        ]
    }
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"✓ Feature engineering audit report saved to {REPORT_FILE}")
    print("\nFeature engineering pipeline completed successfully!")


if __name__ == "__main__":
    main()

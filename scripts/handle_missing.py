"""
Missing value handling workflow.

This script analyzes incomplete records, applies strategy-specific imputation
or row dropping, documents the business reasoning for each decision, and
validates the before/after null counts.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("data/raw/missing_data.csv")
OUTPUT_PATH = Path("data/processed/cleaned_data.csv")
DECISIONS_PATH = Path("output/imputation_decisions.json")


def analyze_missing_values(df):
    """
    Compute null counts and percentages before treatment.

    Returns: DataFrame with analysis of missing data by column
    """
    missing_analysis = pd.DataFrame({
        'column': df.columns,
        'null_count': df.isnull().sum().values,
        'null_percentage': (df.isnull().sum() / len(df) * 100).round(2).values,
        'data_type': df.dtypes.values,
        'null_meaning': ''
    })

    context_map = {
        'customer_id': 'Critical record identifier; missing values invalidate the row.',
        'name': 'Customer identity field; missing values prevent reliable record matching.',
        'email': 'Contact field; missing values block outreach and lifecycle communication.',
        'amount': 'Revenue field; missing values block revenue aggregation.',
        'category': 'Business segment label; missing values weaken segmentation analysis.',
        'last_updated': 'Timestamp field; missing values disrupt chronological analysis.',
    }
    missing_analysis['null_meaning'] = missing_analysis['column'].map(context_map).fillna('Requires business review.')

    print("=" * 70)
    print("BEFORE IMPUTATION - Missing Value Analysis")
    print("=" * 70)
    print(missing_analysis.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")
    print(f"Total cells: {len(df) * len(df.columns)}")
    print(f"Missing cells: {df.isnull().sum().sum()}")
    print("=" * 70)

    return missing_analysis


def impute_mean_median(df, numerical_cols, strategy='median'):
    """Fill numerical nulls with mean or median."""
    df_imputed = df.copy()
    for col in numerical_cols:
        if col not in df_imputed.columns:
            continue
        null_count = df_imputed[col].isnull().sum()
        if null_count > 0:
            fill_value = df_imputed[col].median() if strategy == 'median' else df_imputed[col].mean()
            df_imputed[col] = df_imputed[col].fillna(fill_value)
            print(f"  ✓ {col}: filled {null_count} nulls with {strategy} ({fill_value:.2f})")
    return df_imputed


def impute_mode(df, categorical_cols):
    """Fill categorical nulls with mode (most common value)."""
    df_imputed = df.copy()
    for col in categorical_cols:
        if col not in df_imputed.columns:
            continue
        null_count = df_imputed[col].isnull().sum()
        if null_count > 0:
            mode_series = df_imputed[col].mode(dropna=True)
            if mode_series.empty:
                continue
            mode_val = mode_series.iloc[0]
            df_imputed[col] = df_imputed[col].fillna(mode_val)
            print(f"  ✓ {col}: filled {null_count} nulls with mode '{mode_val}'")
    return df_imputed


def impute_forward_fill(df, time_series_cols):
    """Fill with previous value (for time-series data)."""
    df_imputed = df.copy()
    for col in time_series_cols:
        if col not in df_imputed.columns:
            continue
        null_count = df_imputed[col].isnull().sum()
        if null_count > 0:
            df_imputed[col] = df_imputed[col].ffill()
            print(f"  ✓ {col}: forward-filled {null_count} nulls")
    return df_imputed


def drop_rows_with_nulls(df, critical_cols):
    """Drop rows where critical columns are null."""
    present_cols = [col for col in critical_cols if col in df.columns]
    rows_before = len(df)
    df_imputed = df.dropna(subset=present_cols)
    rows_dropped = rows_before - len(df_imputed)
    print(f"  ✓ Dropped {rows_dropped} rows with null in: {present_cols}")
    return df_imputed


def document_imputation_decisions(df_original, df_imputed):
    """Document all imputation decisions with business justification."""
    decisions = {
        'dataset': 'data/raw/missing_data.csv',
        'metrics_before': {
            'rows': int(len(df_original)),
            'columns': int(len(df_original.columns)),
            'total_nulls': int(df_original.isnull().sum().sum()),
            'nulls_by_column': {col: int(df_original[col].isnull().sum()) for col in df_original.columns},
        },
        'metrics_after': {
            'rows': int(len(df_imputed)),
            'columns': int(len(df_imputed.columns)),
            'total_nulls': int(df_imputed.isnull().sum().sum()),
            'nulls_by_column': {col: int(df_imputed[col].isnull().sum()) for col in df_imputed.columns},
        },
        'decisions': {
            'customer_id': {
                'column_type': 'critical identifier',
                'null_count_before': int(df_original['customer_id'].isnull().sum()) if 'customer_id' in df_original else 0,
                'strategy': 'drop_rows',
                'rows_affected': int(df_original['customer_id'].isnull().sum()) if 'customer_id' in df_original else 0,
                'business_reasoning': 'Customer ID is the primary key for the record. Any row missing it cannot be matched, deduplicated, or trusted in downstream analysis.',
                'risk_assessment': 'Low - dropping protects data integrity',
            },
            'name': {
                'column_type': 'customer identity',
                'null_count_before': int(df_original['name'].isnull().sum()) if 'name' in df_original else 0,
                'strategy': 'drop_rows',
                'rows_affected': int(df_original['name'].isnull().sum()) if 'name' in df_original else 0,
                'business_reasoning': 'Customer name is needed for human review, account lookup, and support workflows. Filling it artificially would create a misleading customer identity.',
                'risk_assessment': 'Low - incomplete identity records are removed instead of guessed',
            },
            'email': {
                'column_type': 'categorical_identifier',
                'null_count_before': int(df_original['email'].isnull().sum()) if 'email' in df_original else 0,
                'strategy': 'drop_rows',
                'rows_affected': int(df_original['email'].isnull().sum()) if 'email' in df_original else 0,
                'business_reasoning': 'Email is required for outreach, verification, and retention campaigns. Records without email cannot support customer communication.',
                'risk_assessment': 'Low - only incomplete contact records are removed',
            },
            'amount': {
                'column_type': 'numerical',
                'null_count_before': int(df_original['amount'].isnull().sum()) if 'amount' in df_original else 0,
                'strategy': 'median_imputation',
                'value_used': float(df_original['amount'].median()) if 'amount' in df_original and df_original['amount'].notna().any() else None,
                'business_reasoning': 'Median purchase amount represents the typical transaction without being skewed by high-value outliers.',
                'risk_assessment': 'Low - median is stable and resistant to skew',
            },
            'category': {
                'column_type': 'categorical',
                'null_count_before': int(df_original['category'].isnull().sum()) if 'category' in df_original else 0,
                'strategy': 'mode_imputation',
                'value_used': df_original['category'].mode(dropna=True).iloc[0] if 'category' in df_original and not df_original['category'].mode(dropna=True).empty else None,
                'business_reasoning': 'The most common category is a defensible default for a low-cardinality business segment field.',
                'risk_assessment': 'Medium - mode assumes missing records follow the dominant group',
            },
            'last_updated': {
                'column_type': 'datetime_series',
                'null_count_before': int(df_original['last_updated'].isnull().sum()) if 'last_updated' in df_original else 0,
                'strategy': 'forward_fill',
                'interpretation': 'Assumes the last known timestamp remains valid until updated',
                'business_reasoning': 'For time-series feeds, forward fill preserves temporal continuity when later observations inherit the prior state.',
                'risk_assessment': 'Medium - only suitable where values change slowly over time',
            },
        },
    }

    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DECISIONS_PATH.open('w', encoding='utf-8') as f:
        json.dump(decisions, f, indent=2, default=str)

    return decisions


def validate_imputation(df_original, df_imputed):
    """Compare metrics before and after imputation."""

    print("\n" + "=" * 70)
    print("AFTER IMPUTATION - Validation Report")
    print("=" * 70)
    print(f"Total rows before: {len(df_original)}")
    print(f"Total rows after:  {len(df_imputed)}")
    print(f"Rows removed: {len(df_original) - len(df_imputed)}")
    print(f"\nTotal nulls before: {df_original.isnull().sum().sum()}")
    print(f"Total nulls after:  {df_imputed.isnull().sum().sum()}")

    missing_after = pd.DataFrame({
        'column': df_imputed.columns,
        'null_count_after': df_imputed.isnull().sum().values,
        'null_percentage_after': (df_imputed.isnull().sum() / len(df_imputed) * 100).round(2).values if len(df_imputed) else np.zeros(len(df_imputed)),
    })

    print("\nNull values by column after imputation:")
    print(missing_after.to_string(index=False))
    print("=" * 70)

    return missing_after


def main():
    df = pd.read_csv(INPUT_PATH)

    print("Step 1: Analyzing missing values...")
    analyze_missing_values(df)

    print("\nStep 2: Applying imputation strategies...")
    df_before = df.copy()
    df = drop_rows_with_nulls(df, ['customer_id', 'name', 'email'])
    df = impute_mean_median(df, ['amount'], strategy='median')
    df = impute_mode(df, ['category'])
    df = impute_forward_fill(df, ['last_updated'])

    print("\nStep 3: Documenting imputation decisions...")
    decisions = document_imputation_decisions(df_before, df)

    print("\nStep 4: Validating imputation...")
    validate_imputation(df_before, df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✓ Cleaned data saved to {OUTPUT_PATH}")
    print(f"✓ Decision log saved to {DECISIONS_PATH}")

    return decisions


if __name__ == "__main__":
    main()
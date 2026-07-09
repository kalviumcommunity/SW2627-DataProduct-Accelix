"""
Data Quality Profiling Script
=============================
Profiles raw tabular data for nulls, duplicates, numerical summaries,
categorical distributions, and common quality issues.
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path("output/profile_report.json")
DEFAULT_INPUT_PATH = Path("data/raw/quality_test.csv")


def profile_nulls_and_duplicates(df):
    """
    Compute null percentage and duplicate counts per column.

    Returns: Dictionary with null analysis by column.
    """
    profile = {
        'null_counts': {},
        'null_percentages': {},
        'exact_duplicate_count': 0,
        'business_duplicate_count': 0,
    }

    row_count = len(df)
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = (null_count / row_count) * 100 if row_count else 0
        profile['null_counts'][col] = int(null_count)
        profile['null_percentages'][col] = round(null_pct, 2)

    exact_duplicate_count = int(df.duplicated().sum())
    duplicate_percentage = (exact_duplicate_count / row_count) * 100 if row_count else 0
    profile['exact_duplicate_count'] = exact_duplicate_count
    profile['duplicate_percentage'] = round(duplicate_percentage, 2)

    id_like_columns = [col for col in df.columns if col.lower() == 'id' or col.lower().endswith('_id')]
    business_columns = [col for col in df.columns if col not in id_like_columns]
    if business_columns:
        business_duplicate_count = int(df.duplicated(subset=business_columns).sum())
        profile['business_duplicate_count'] = business_duplicate_count
        profile['business_duplicate_percentage'] = round(
            (business_duplicate_count / row_count) * 100 if row_count else 0,
            2,
        )

    return profile


def profile_numerical_columns(df):
    """
    Summarise numerical columns with statistical measures.

    Returns: DataFrame with min, max, mean, median, std.
    """
    numerical_cols = df.select_dtypes(include=[np.number]).columns

    stats = {}
    for col in numerical_cols:
        stats[col] = {
            'min': round(df[col].min(), 2),
            'max': round(df[col].max(), 2),
            'mean': round(df[col].mean(), 2),
            'median': round(df[col].median(), 2),
            'std': round(df[col].std(), 2),
            'null_count': int(df[col].isnull().sum()),
        }

    return pd.DataFrame(stats).T


def profile_categorical_columns(df, top_n=5):
    """
    Summarise categorical columns with value distributions.

    Returns: Dictionary with unique counts and top values.
    """
    categorical_cols = df.select_dtypes(include=['object']).columns

    profile = {}
    for col in categorical_cols:
        profile[col] = {
            'unique_count': int(df[col].nunique()),
            'top_values': df[col].value_counts(dropna=True).head(top_n).to_dict(),
            'null_count': int(df[col].isnull().sum()),
        }

    return profile


def identify_quality_issues(df, null_threshold=30, duplicate_threshold=5):
    """
    Identify data quality problems based on thresholds.

    Returns: List of issues found with severity and recommendations.
    """
    issues = []

    row_count = len(df)
    if row_count == 0:
        return issues

    null_pcts = (df.isnull().sum() / row_count) * 100
    for col, pct in null_pcts.items():
        if pct > null_threshold:
            issues.append({
                'type': 'High nulls',
                'column': col,
                'severity': 'HIGH',
                'value': f"{pct:.1f}% missing",
                'recommendation': 'Consider imputation or column exclusion',
            })

    dup_count = int(df.duplicated().sum())
    dup_pct = (dup_count / row_count) * 100
    if dup_pct > duplicate_threshold:
        issues.append({
            'type': 'High duplicates',
            'column': 'Full row',
            'severity': 'HIGH',
            'value': f"{dup_pct:.1f}% duplicated",
            'recommendation': 'Deduplication required before analysis',
        })

    id_like_columns = [col for col in df.columns if col.lower() == 'id' or col.lower().endswith('_id')]
    business_columns = [col for col in df.columns if col not in id_like_columns]
    if business_columns:
        business_dup_count = int(df.duplicated(subset=business_columns).sum())
        business_dup_pct = (business_dup_count / row_count) * 100
        if business_dup_count > 0:
            issues.append({
                'type': 'Suspicious duplicates',
                'column': ', '.join(business_columns),
                'severity': 'HIGH',
                'value': f"{business_dup_pct:.1f}% duplicated on business fields",
                'recommendation': 'Review records that match on non-ID fields before deduping',
            })

    for col in df.select_dtypes(include=[np.number]).columns:
        if (df[col] < 0).any() and 'amount' in col.lower():
            issues.append({
                'type': 'Invalid range',
                'column': col,
                'severity': 'MEDIUM',
                'value': 'Contains negative values',
                'recommendation': 'Investigate negative entries',
            })

    numeric_like_pattern = re.compile(r'^-?\d+(\.\d+)?$')
    for col in df.select_dtypes(include=['object']).columns:
        non_null_values = df[col].dropna().astype(str)
        if not non_null_values.empty and any(numeric_like_pattern.match(value.strip()) for value in non_null_values):
            issues.append({
                'type': 'Corrupted categorical value',
                'column': col,
                'severity': 'MEDIUM',
                'value': 'Contains numeric-looking category value(s)',
                'recommendation': 'Validate categorical domain and recode or remove invalid entries',
            })

    return issues


def generate_profile_report(df, filepath):
    """
    Generate complete data quality report and save to JSON.

    Returns: Complete profile report dictionary.
    """
    report = {
        'dataset': filepath,
        'record_count': int(len(df)),
        'column_count': int(len(df.columns)),
        'nulls_and_duplicates': profile_nulls_and_duplicates(df),
        'numerical_stats': profile_numerical_columns(df).to_dict(),
        'categorical_stats': profile_categorical_columns(df),
        'quality_issues': identify_quality_issues(df),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open('w', encoding='utf-8') as file_handle:
        json.dump(report, file_handle, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"DATA QUALITY PROFILE: {filepath}")
    print(f"{'=' * 60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"\nQuality Issues Found: {len(report['quality_issues'])}")
    for issue in report['quality_issues']:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} → {issue['recommendation']}")
    print(f"{'=' * 60}\n")

    return report


def load_dataset(filepath):
    """Load a CSV file into a DataFrame with a clear error if it is missing."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found at path: {filepath}")
    return pd.read_csv(path)


def parse_args():
    parser = argparse.ArgumentParser(description='Generate a data quality profile report.')
    parser.add_argument(
        'filepath',
        nargs='?',
        default=str(DEFAULT_INPUT_PATH),
        help='Path to the CSV file to profile.',
    )
    parser.add_argument(
        '--output',
        default=str(OUTPUT_PATH),
        help='Path for the JSON report output.',
    )
    return parser.parse_args()


def main():
    args = parse_args()

    global OUTPUT_PATH
    OUTPUT_PATH = Path(args.output)

    df = load_dataset(args.filepath)
    generate_profile_report(df, args.filepath)


if __name__ == '__main__':
    main()
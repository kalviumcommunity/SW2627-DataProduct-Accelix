import json
import os

import pandas as pd


OUTPUT_DIR = "output"
RAW_INPUT_FILE = "data/raw/string_cleaning_sample.csv"
PROCESSED_OUTPUT_FILE = "data/processed/string_cleaned_data.csv"
COMPARISON_FILE = os.path.join(OUTPUT_DIR, "string_cleaning_comparison.json")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "string_cleaning_summary.json")


os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROCESSED_OUTPUT_FILE), exist_ok=True)


segment_map = {
    "b2b": "B2B",
    "b 2 b": "B2B",
    "b2 b": "B2B",
    "business-to-business": "B2B",
    "sme": "SMB",
    "small medium enterprise": "SMB",
    "small-medium enterprise": "SMB",
    "enterprise": "Enterprise",
    "enter prise": "Enterprise",
    "enterprise customer": "Enterprise",
}


def clean_text_column(series, lowercase=True, strip=True, remove_special=False, mapping=None):
    """Reusable text cleaning function for any string column."""
    result = series.copy()

    if result.isna().any():
        print(f"Warning: {result.isna().sum()} null values in column")

    result = result.astype("string")

    if strip:
        result = result.str.strip()

    if lowercase:
        result = result.str.lower()

    if remove_special:
        result = result.str.replace(r"[^a-zA-Z0-9 ]", "", regex=True)

    if mapping:
        result = result.replace(mapping)

    return result


def strip_all_strings(df):
    """Strip whitespace from all string columns."""
    df_clean = df.copy()
    string_cols = df_clean.select_dtypes(include=["object", "string"]).columns
    summary = []

    for col in string_cols:
        before_counts = df_clean[col].value_counts(dropna=False)
        whitespace_count = int(
            df_clean[col]
            .astype("string")
            .str.match(r"^\s+|.*\s+$", na=False)
            .sum()
        )
        df_clean[col] = clean_text_column(df_clean[col], lowercase=False, strip=True)
        after_counts = df_clean[col].value_counts(dropna=False)

        print(f"{col}: {before_counts.shape[0]} → {after_counts.shape[0]} unique values")
        print(f"Whitespace values fixed in {col}: {whitespace_count}")
        summary.append(
            {
                "column": col,
                "whitespace_values_fixed": whitespace_count,
                "unique_values_before": int(before_counts.shape[0]),
                "unique_values_after": int(after_counts.shape[0]),
            }
        )

        print(f"\n{col} value counts before:")
        print(before_counts.to_string())
        print(f"\n{col} value counts after:")
        print(after_counts.to_string())

    return df_clean, summary


def normalize_casing(df, columns_to_lower):
    """Normalize casing for specified columns."""
    df_clean = df.copy()

    for col in columns_to_lower:
        if col not in df_clean.columns:
            print(f"Warning: Column {col} not found")
            continue
        df_clean[col] = clean_text_column(df_clean[col], lowercase=True, strip=False)
        print(f"Normalized {col} to lowercase")

    return df_clean


def remove_special_characters(df, columns):
    """Remove special characters from specified columns."""
    df_clean = df.copy()

    for col in columns:
        if col not in df_clean.columns:
            print(f"Warning: Column {col} not found")
            continue
        df_clean[col] = clean_text_column(df_clean[col], lowercase=False, strip=False, remove_special=True)
        print(f"Removed special characters from {col}")

    return df_clean


def standardize_categorical_labels(df, column, mapping, canonical_name):
    """Standardize categorical labels to a canonical form."""
    df_clean = df.copy()
    if column not in df_clean.columns:
        print(f"Warning: Column {column} not found")
        return df_clean

    normalized = clean_text_column(df_clean[column], lowercase=True, strip=True, remove_special=False)
    before_counts = normalized.value_counts(dropna=False)
    df_clean[column] = normalized.replace(mapping)
    after_counts = df_clean[column].value_counts(dropna=False)

    print(f"\nStandardized {column} to canonical form: {canonical_name}")
    print(f"{column} value counts before mapping:")
    print(before_counts.to_string())
    print(f"\n{column} value counts after mapping:")
    print(after_counts.to_string())

    return df_clean


def build_sample_dataset():
    """Create a synthetic dataset with messy text fields."""
    return pd.DataFrame(
        {
            "product_name": [
                " Electronics ",
                "electronics",
                "ELECTRONICS",
                " Home Audio ",
                "home-audio",
                "Home Audio",
                "Accessory Pack",
            ],
            "customer_segment": [
                "B2B",
                "b2b",
                "B 2 B",
                "SME",
                "small medium enterprise",
                "business-to-business",
                "enterprise",
            ],
            "customer_name": [
                "JOHN",
                "john",
                "John",
                "Maria",
                "maria ",
                " MARIA",
                None,
            ],
            "location": [
                "São Paulo",
                "Montréal",
                "München",
                "New York",
                " São Paulo ",
                "Montréal",
                "Québec",
            ],
        }
    )


def compare_before_after(df_before, df_after):
    """Summarize row-level text standardization results."""
    comparison = {
        "rows_before": len(df_before),
        "rows_after": len(df_after),
        "columns": list(df_before.columns),
        "nulls_before": int(df_before.isnull().sum().sum()),
        "nulls_after": int(df_after.isnull().sum().sum()),
    }

    print("\n" + "=" * 70)
    print("STRING CLEANING SUMMARY")
    print("=" * 70)
    print(f"Rows before: {comparison['rows_before']}")
    print(f"Rows after:  {comparison['rows_after']}")
    print(f"Nulls before: {comparison['nulls_before']}")
    print(f"Nulls after:  {comparison['nulls_after']}")
    print("=" * 70)

    with open(COMPARISON_FILE, "w", encoding="utf-8") as file_handle:
        json.dump(comparison, file_handle, indent=2)

    return comparison


def run_pipeline(df):
    """Apply the string cleaning pipeline to the dataset."""
    df_clean = df.copy()

    print("\n[Step 1/4] Strip whitespace from all string columns...")
    df_clean, strip_summary = strip_all_strings(df_clean)

    print("\n[Step 2/4] Normalize casing for categorical fields...")
    df_clean = normalize_casing(df_clean, ["product_name", "customer_segment", "customer_name", "location"])

    print("\n[Step 3/4] Remove special characters from location and product_name...")
    df_clean = remove_special_characters(df_clean, ["location", "product_name"])

    print("\n[Step 4/4] Standardize categorical labels using mapping dictionary...")
    df_clean = standardize_categorical_labels(df_clean, "customer_segment", segment_map, "B2B/SMB/Enterprise")

    return df_clean, strip_summary


if __name__ == "__main__":
    if os.path.exists(RAW_INPUT_FILE):
        df = pd.read_csv(RAW_INPUT_FILE)
    else:
        df = build_sample_dataset()
        df.to_csv(RAW_INPUT_FILE, index=False)
        print(f"Created synthetic dataset at {RAW_INPUT_FILE}")

    print("=" * 70)
    print("BEFORE CLEANING")
    print("=" * 70)
    print(df.head())

    df_cleaned, strip_summary = run_pipeline(df)

    print("\n" + "=" * 70)
    print("AFTER CLEANING")
    print("=" * 70)
    print(df_cleaned.head())

    compare_before_after(df, df_cleaned)

    df_cleaned.to_csv(PROCESSED_OUTPUT_FILE, index=False)
    print(f"\n✓ Cleaned data saved to {PROCESSED_OUTPUT_FILE}")

    report = {
        "strip_summary": strip_summary,
        "mapping_used": segment_map,
        "regex_pattern": "[^a-zA-Z0-9 ]",
        "comparison_file": COMPARISON_FILE,
        "notes": [
            "Lowercase was chosen as the canonical case for categorical fields.",
            "Special characters are removed from product and location fields to avoid downstream encoding issues.",
            "International characters such as São and Montréal are normalized using the configured regex pattern.",
        ],
    }

    with open(SUMMARY_FILE, "w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2, ensure_ascii=False)

    print(f"✓ Summary saved to {SUMMARY_FILE}")
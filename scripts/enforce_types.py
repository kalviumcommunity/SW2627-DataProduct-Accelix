import json
import os

import numpy as np
import pandas as pd


OUTPUT_DIR = "output"
RAW_INPUT_FILE = "data/raw/untyped_data.csv"
TYPED_OUTPUT_FILE = "data/processed/typed_data.csv"
TYPE_REPORT_FILE = os.path.join(OUTPUT_DIR, "dtype_conversion_report.csv")
TYPE_LOG_FILE = os.path.join(OUTPUT_DIR, "dtype_conversion_log.json")


os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(TYPED_OUTPUT_FILE), exist_ok=True)


def cast_columns_to_types(df, type_mapping):
    """
    Explicitly cast columns to correct dtypes.

    Args:
        df: Input DataFrame
        type_mapping: Dict of {column: target_dtype}

    Returns:
        DataFrame with corrected types and conversion log
    """
    df_typed = df.copy()
    conversion_log = {}

    for col, target_dtype in type_mapping.items():
        if col not in df.columns:
            print(f"Warning: Column {col} not found in DataFrame")
            continue

        original_dtype = df[col].dtype

        try:
            df_typed[col] = df_typed[col].astype(target_dtype)
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "success",
            }
            print(f"✓ {col}: {original_dtype} → {target_dtype}")
        except Exception as e:
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "failed",
                "error": str(e),
            }
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed, conversion_log


def convert_string_dates_to_datetime(df, date_columns, date_format=None):
    """
    Convert string columns to datetime with explicit format.

    Args:
        df: Input DataFrame
        date_columns: List of column names containing dates
        date_format: Datetime format string (e.g., '%Y-%m-%d')

    Returns:
        DataFrame with datetime columns converted

    Note: ALWAYS specify format. "01-02-2025" is ambiguous without it.
    """
    df_typed = df.copy()

    for col in date_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            if date_format:
                df_typed[col] = pd.to_datetime(df_typed[col], format=date_format)
            else:
                df_typed[col] = pd.to_datetime(df_typed[col])

            print(f"✓ {col}: Converted to datetime")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            print(f"  Sample values: {df[col].head(3).tolist()}")
            print(f"  Expected format: {date_format}")
            raise

    return df_typed


def convert_currency_to_float(df, currency_columns):
    """
    Strip currency symbols and convert to float.

    Example: '$150.50' → 150.50

    Args:
        df: Input DataFrame
        currency_columns: List of column names with currency

    Returns:
        DataFrame with clean numeric columns
    """
    df_typed = df.copy()

    for col in currency_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            original_nulls = df_typed[col].isnull().sum()
            df_typed[col] = (
                df_typed[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
                .replace({"": np.nan, "nan": np.nan, "None": np.nan})
            )

            df_typed[col] = pd.to_numeric(df_typed[col], errors="coerce")

            failed_conversions = df_typed[col].isnull().sum() - original_nulls
            if failed_conversions > 0:
                print(f"⚠ {col}: {failed_conversions} values could not be converted to numeric")

            print(f"✓ {col}: Stripped symbols, converted to float")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed


def convert_integers_to_boolean(df, boolean_columns):
    """
    Convert 0/1 or yes/no columns to proper boolean type.

    Args:
        df: Input DataFrame
        boolean_columns: List of column names with binary values

    Returns:
        DataFrame with bool columns
    """
    df_typed = df.copy()

    for col in boolean_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            unique_vals = df[col].unique()
            print(f"  {col} unique values: {unique_vals}")

            if df[col].dtype == "object":
                normalized = df_typed[col].astype(str).str.strip().str.lower()
                mapping = {
                    "yes": True,
                    "no": False,
                    "y": True,
                    "n": False,
                    "true": True,
                    "false": False,
                    "1": True,
                    "0": False,
                }
                mapped = normalized.map(mapping)
                if mapped.isna().any() and not normalized.isna().any():
                    unmapped = sorted(set(normalized[mapped.isna()].dropna().tolist()))
                    raise ValueError(f"Unrecognized boolean values in {col}: {unmapped}")
                df_typed[col] = mapped.astype("boolean")
            else:
                df_typed[col] = df_typed[col].astype(bool)

            print(f"✓ {col}: Converted to boolean")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed


def compare_dtypes(df_original, df_typed):
    """
    Compare dtypes before and after conversion.

    Returns: Summary of all changes
    """
    comparison = pd.DataFrame(
        {
            "column": df_original.columns,
            "dtype_before": df_original.dtypes.values,
            "dtype_after": df_typed.dtypes.values,
            "changed": (df_original.dtypes != df_typed.dtypes).values,
        }
    )

    print("\n" + "=" * 70)
    print("DTYPE CONVERSION SUMMARY")
    print("=" * 70)
    print(comparison.to_string(index=False))

    comparison.to_csv(TYPE_REPORT_FILE, index=False)
    print(f"\nReport saved to {TYPE_REPORT_FILE}")
    print("=" * 70)

    return comparison


def save_conversion_log(conversion_log, output_path):
    """Persist a conversion log for auditability."""
    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(conversion_log, file_handle, indent=2, default=str)


if __name__ == "__main__":
    df = pd.read_csv(RAW_INPUT_FILE)

    print("=" * 70)
    print("BEFORE TYPE CONVERSION")
    print("=" * 70)
    print(df.dtypes)
    print("\nSample data:")
    print(df.head(3))

    df_typed = df.copy()
    conversion_log = {}

    print("\n1. Converting date columns...")
    df_typed = convert_string_dates_to_datetime(
        df_typed,
        ["transaction_date", "signup_date"],
        date_format="%Y-%m-%d",
    )
    conversion_log["date_columns"] = {
        "transaction_date": {
            "from": str(df["transaction_date"].dtype),
            "to": "datetime64[ns]",
            "status": "success",
            "format": "%Y-%m-%d",
        },
        "signup_date": {
            "from": str(df["signup_date"].dtype),
            "to": "datetime64[ns]",
            "status": "success",
            "format": "%Y-%m-%d",
        },
    }

    print("\n2. Converting currency columns...")
    df_typed = convert_currency_to_float(
        df_typed,
        ["amount"],
    )
    conversion_log["currency_columns"] = {
        "amount": {
            "from": str(df["amount"].dtype),
            "to": "float64",
            "status": "success",
            "standardization": "stripped currency symbols and commas",
        },
    }

    print("\n3. Converting boolean columns...")
    df_typed = convert_integers_to_boolean(
        df_typed,
        ["is_active"],
    )
    conversion_log["boolean_columns"] = {
        "is_active": {
            "from": str(df["is_active"].dtype),
            "to": "boolean",
            "status": "success",
            "standardization": "mapped binary indicator to boolean",
        },
    }

    print("\n4. Comparing before/after types...")
    print("=" * 70)
    print("AFTER TYPE CONVERSION")
    print("=" * 70)
    print(df_typed.dtypes)
    print("\nSample data:")
    print(df_typed.head(3))

    compare_dtypes(df, df_typed)

    df_typed.to_csv(TYPED_OUTPUT_FILE, index=False)
    save_conversion_log(conversion_log, TYPE_LOG_FILE)
    print(f"\n✓ Typed data saved to {TYPED_OUTPUT_FILE}")
    print(f"✓ Conversion log saved to {TYPE_LOG_FILE}")
"""
Dataset Intake & Source Validation Script
==========================================
This script runs a data validation firewall check before analysis or transformation.
It validates file existence, format consistency, column schema completeness, file encoding,
and gathers baseline metrics to produce a structured JSON validation report.
"""

import os
import sys
import json
import logging
from datetime import datetime
import pandas as pd
import chardet

# Ensure stdout and stderr support UTF-8 (particularly on Windows shell environments)
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
INPUT_FILE = "data/raw/sample.csv"
OUTPUT_REPORT = "output/intake_report.json"
EXPECTED_COLUMNS = [
    "customer_id",
    "customer_name",
    "transaction_amount",
    "transaction_date"
]

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_REPORT), exist_ok=True)

# ==============================================================================
# VALIDATION CHECKS
# ==============================================================================

def validate_file_exists(filepath):
    """
    Check if file exists on disk and is non-empty.

    Args:
        filepath (str): Path to the input dataset file.

    Returns:
        tuple: (bool, str) status and detailed description.
    """
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"
    
    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"
    
    return True, "File exists and has content"


def validate_file_format(filepath, allowed_formats=['csv', 'json', 'xlsx']):
    """
    Check if the file extension matches the expected allowed formats.

    Args:
        filepath (str): Path to the input dataset file.
        allowed_formats (list): List of allowed string format extensions.

    Returns:
        tuple: (bool, str) status and detailed description.
    """
    extension = filepath.split('.')[-1].lower()
    
    if extension not in allowed_formats:
        return False, f"Unsupported format: {extension}. Allowed: {allowed_formats}"
    
    return True, f"Format valid: {extension}"


def validate_schema(df, expected_columns):
    """
    Validate that the DataFrame has all expected columns.
    Flags missing required columns and identifies unexpected extra columns.

    Args:
        df (pd.DataFrame): Ingested dataset DataFrame.
        expected_columns (list): List of column names expected in schema.

    Returns:
        tuple: (bool, str) status and detailed list of discrepancies (if any).
    """
    if not isinstance(df, pd.DataFrame):
        return False, "Input data is not a Pandas DataFrame"

    missing = set(expected_columns) - set(df.columns)
    extra = set(df.columns) - set(expected_columns)
    
    issues = []
    if missing:
        issues.append(f"Missing columns: {missing}")
    if extra:
        issues.append(f"Unexpected columns: {extra}")
    
    if not issues:
        return True, f"Schema valid: {len(df.columns)} columns present"
    
    return False, " | ".join(issues)


def detect_encoding(filepath):
    """
    Detect file character encoding using a confidence threshold.
    Reads up to the first 10,000 bytes.

    Args:
        filepath (str): Path to the input dataset file.

    Returns:
        tuple: (str, str) detected encoding and formatted status description.
    """
    try:
        with open(filepath, 'rb') as f:
            result = chardet.detect(f.read(10000))
        
        encoding = result.get('encoding', 'utf-8')
        # If encoding detection fails, default to ascii/utf-8
        if encoding is None:
            encoding = 'utf-8'
        confidence = result.get('confidence', 1.0)
        
        # Format detected encoding message
        status_msg = f"Detected: {encoding} (confidence: {confidence:.1%})"
        return encoding, status_msg
    except Exception as e:
        return 'unknown', f"Failed to detect encoding: {str(e)}"


def capture_dataset_stats(filepath, df):
    """
    Log dataset dimensions, row count, column count, and size in bytes/MB.

    Args:
        filepath (str): Path to the input dataset file.
        df (pd.DataFrame): Ingested dataset DataFrame.

    Returns:
        dict: A dictionary of dataset statistics.
    """
    file_size_bytes = os.path.getsize(filepath)
    file_size_mb = file_size_bytes / (1024 * 1024)
    row_count = len(df)
    col_count = len(df.columns)
    
    return {
        'rows': row_count,
        'columns': col_count,
        'file_size_mb': round(file_size_mb, 5), # Keep precise precision for small test file
        'bytes': file_size_bytes
    }


def generate_intake_report(filepath, expected_columns):
    """
    Perform a complete dataset intake check and build a structured validation report.
    Gates downstream processing by failing fast on major errors.

    Args:
        filepath (str): Path to the input dataset file.
        expected_columns (list): List of column names expected in schema.

    Returns:
        dict: Structured validation report dictionary.
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'filepath': filepath,
        'validations': {}
    }
    
    # 1. Check file existence
    file_exists, msg = validate_file_exists(filepath)
    report['validations']['file_exists'] = msg
    if not file_exists:
        return report
    
    # 2. Check file format
    format_valid, msg = validate_file_format(filepath)
    report['validations']['format'] = msg
    if not format_valid:
        return report
    
    # 3. Read data to execute remaining validation gates
    try:
        # Detect encoding to ensure clean parsing
        encoding, enc_msg = detect_encoding(filepath)
        report['validations']['encoding'] = enc_msg
        
        # Load dataset
        df = pd.read_csv(filepath, encoding=encoding)
        
        # 4. Check schema
        schema_valid, schema_msg = validate_schema(df, expected_columns)
        report['validations']['schema'] = schema_msg
        
        # 5. Capture statistics
        stats = capture_dataset_stats(filepath, df)
        report['statistics'] = stats
        
    except Exception as e:
        report['validations']['ingestion_error'] = f"Failed to ingest/parse data file: {str(e)}"
    
    # Write report output to JSON
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
        
    return report

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print(f"Starting intake validation for: {INPUT_FILE}")
    validation_report = generate_intake_report(INPUT_FILE, EXPECTED_COLUMNS)
    print("✓ Intake validation completed. Report generated at:")
    print(f"  {OUTPUT_REPORT}")

"""
Python Data Workflow Script
============================
This script implements a production-ready data pipeline utilizing the
Three-Function Pattern (Ingest, Process, Output). It is designed to run
from the command line, log execution details, and support parameter configuration.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

# Ensure stdout and stderr support UTF-8 (particularly on Windows shell environments)
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
INPUT_FILE = "data/raw/sample.csv"
OUTPUT_FILE = "output/processed.csv"
LOG_FILE = "output/workflow.log"

# Ensure directories exist
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# ==============================================================================
# LOGGING SETUP
# ==============================================================================
logging.basicConfig(
    filename=LOG_FILE,
    filemode="w",  # Recreate log file on each run
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==============================================================================
# MAIN FUNCTIONS
# ==============================================================================

def ingest_data(filepath):
    """
    Load raw data from a CSV file into a Pandas DataFrame.

    This function isolates data loading from any transformation logic. If the data
    source format changes (e.g., to JSON or database connection), only this
    function needs to be modified.

    Args:
        filepath (str): The absolute or relative path to the CSV data source.

    Returns:
        pd.DataFrame: A Pandas DataFrame containing the raw dataset.

    Raises:
        FileNotFoundError: If the source CSV file does not exist.
        pd.errors.EmptyDataError: If the source file is empty.
    """
    logging.info(f"Starting ingestion from: {filepath}")
    try:
        df = pd.read_csv(filepath)
        logging.info(f"Ingested {len(df)} rows and {len(df.columns)} columns successfully")
        return df
    except FileNotFoundError as e:
        logging.error(f"Failed to find input file at {filepath}: {str(e)}")
        raise FileNotFoundError(f"Input file not found at path: {filepath}") from e
    except Exception as e:
        logging.error(f"Unexpected error during data ingestion: {str(e)}")
        raise

def process_data(df):
    """
    Transform raw data into a clean, analysis-ready format.

    This function isolates all business logic/transformations:
    - Removes duplicate records where all column values are identical.
    - Imputes missing values (NaN) in all numerical columns using the column-wise median.

    This function does not perform any disk I/O, database access, or network calls,
    allowing it to be easily tested in isolation.

    Args:
        df (pd.DataFrame): The raw input Pandas DataFrame.

    Returns:
        pd.DataFrame: The cleaned and transformed Pandas DataFrame.

    Raises:
        ValueError: If the input DataFrame is empty or not a DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input to process_data must be a Pandas DataFrame.")
    
    if df.empty:
        logging.warning("Input DataFrame to process_data is empty.")
        return df

    rows_before = len(df)
    logging.info(f"Starting data processing. Initial row count: {rows_before}")

    # Remove exact duplicates (rows where all values are identical)
    df_cleaned = df.drop_duplicates()
    rows_after_duplicates = len(df_cleaned)
    logging.info(f"Removed {rows_before - rows_after_duplicates} duplicate rows.")

    # Fill missing values in numerical columns with their median
    numeric_cols = df_cleaned.select_dtypes(include=['number']).columns
    logging.info(f"Identified numerical columns for imputation: {list(numeric_cols)}")

    # We make a copy of the dataframe to avoid setting with copy warnings
    df_cleaned = df_cleaned.copy()
    
    for col in numeric_cols:
        null_count = df_cleaned[col].isnull().sum()
        if null_count > 0:
            median_value = df_cleaned[col].median()
            df_cleaned[col] = df_cleaned[col].fillna(median_value)
            logging.info(f"Imputed {null_count} null value(s) in column '{col}' with median: {median_value}")

    logging.info(f"Data processing completed. Final row count: {len(df_cleaned)}")
    return df_cleaned

def output_results(df, output_path):
    """
    Save the processed data to a target CSV file and print a console summary.

    This function isolates target delivery details from data processing logic. If the
    output medium changes (e.g., writing to a SQL table or sending an API request),
    only this function needs to be modified.

    Args:
        df (pd.DataFrame): The cleaned and processed Pandas DataFrame.
        output_path (str): The target file path where the CSV should be saved.

    Returns:
        None

    Raises:
        OSError: If the target file cannot be created or written.
    """
    logging.info(f"Saving processed data to: {output_path}")
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write to CSV
        df.to_csv(output_path, index=False)
        logging.info(f"Output successfully saved to {output_path}")
        
        # Print formatted execution confirmation to console
        print(f"✓ Data successfully processed")
        print(f"✓ Rows processed: {len(df)}")
        print(f"✓ Output saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save output to {output_path}: {str(e)}")
        raise OSError(f"Could not write output file at {output_path}: {str(e)}") from e

# ==============================================================================
# MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    try:
        logging.info("================== Starting data workflow pipeline ==================")
        
        # Run three-function pipeline
        data = ingest_data(INPUT_FILE)
        processed = process_data(data)
        output_results(processed, OUTPUT_FILE)
        
        logging.info("================== Data workflow completed successfully ==============")
    except Exception as e:
        logging.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        print(f"✗ Error: Workflow failed to execute. Reason: {str(e)}")
        exit(1)

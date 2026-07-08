# Data Workflow Documentation

This document describes the structure and execution details of the modular Python data pipeline implemented in `scripts/data_workflow.py`.

Transitioning from notebook-based exploration to structured script-based pipelines ensures reliability, automation capability, and collaborative maintainability.

---

## Folder Structure

The pipeline is organized using a standard data project layout:
- [data/raw/](file:///d:/Kalvium/SW2627-DataProduct-Accelix/data/raw/) - Source datasets that are never modified in place. Contains the raw `sample.csv` for workflow validation.
- [data/processed/](file:///d:/Kalvium/SW2627-DataProduct-Accelix/data/processed/) - Transformed datasets ready for downstream analysis.
- [scripts/](file:///d:/Kalvium/SW2627-DataProduct-Accelix/scripts/) - Modular, automated scripts. Contains `data_workflow.py`.
- [output/](file:///d:/Kalvium/SW2627-DataProduct-Accelix/output/) - Generated reports, verification artifacts, and logs. Contains `processed.csv`, `workflow.log`, and `sample_run.txt`.

---

## How to Execute the Script

Ensure your packages in `requirements.txt` (like `pandas` and `numpy`) are installed and ready.

Run the script from the project root directory:

```bash
python scripts/data_workflow.py
```

### Verification and Artifacts
Upon completion, the script outputs the following files and logs:
- `output/processed.csv`: The cleaned data.
- `output/workflow.log`: A comprehensive log showing step-by-step telemetry (e.g., loaded row count, duplicates removed, and columns imputed).

---

## Function Summaries (Three-Function Pattern)

The script separates ingestion, processing, and output concerns into distinct, testable functions:

### 1. `ingest_data(filepath)`
- **Purpose**: Loads a raw CSV file from disk into a Pandas DataFrame.
- **Inputs**: `filepath` (str) - path to the input CSV.
- **Returns**: `pd.DataFrame` - the loaded raw dataset.
- **Error Handling**: Catches missing files or reading errors and logs them, raising a descriptive exception.
- **Why it matters**: Decouples the physical storage location and retrieval format from the downstream analysis logic.

### 2. `process_data(df)`
- **Purpose**: Runs cleaning and transformation business logic.
- **Operations**:
  1. Identifies and removes exact duplicate rows.
  2. Imputes missing (null) values in numeric columns using the column's median.
- **Inputs**: `df` (pd.DataFrame) - the raw input DataFrame.
- **Returns**: `pd.DataFrame` - a new, cleaned, and imputed DataFrame.
- **Why it matters**: Acts as a pure function with no disk/network I/O. It can be easily tested in isolation using dummy inputs.

### 3. `output_results(df, output_path)`
- **Purpose**: Saves the final DataFrame to the specified destination and outputs a summary to the console.
- **Inputs**:
  - `df` (pd.DataFrame) - the processed dataset.
  - `output_path` (str) - path where the CSV file will be written.
- **Returns**: None.
- **Why it matters**: Decouples target delivery format (CSV, database, email, webhook) from the ingestion and processing phases.

---

## How to Modify for New Datasets

To adapt the script for new tables or alternative data pipelines, adjust the configuration block or replace specific components:

### A. Changing File Paths
At the top of [data_workflow.py](file:///d:/Kalvium/SW2627-DataProduct-Accelix/scripts/data_workflow.py), edit the configuration constants:
```python
INPUT_FILE = "data/raw/my_new_dataset.csv"
OUTPUT_FILE = "output/my_processed_dataset.csv"
LOG_FILE = "output/my_workflow.log"
```

### B. Adjusting Imputation Strategies
To change how missing values are handled (e.g., using mean or a static value instead of the median), edit the imputation block in `process_data`:
```diff
-            median_value = df_cleaned[col].median()
-            df_cleaned[col] = df_cleaned[col].fillna(median_value)
+            mean_value = df_cleaned[col].mean()
+            df_cleaned[col] = df_cleaned[col].fillna(mean_value)
```

### C. Integrating with Databases
If you need to load data from a database instead of CSV files, replace `ingest_data` to use SQLAlchemy/Pandas DB reader:
```python
def ingest_data(connection_uri, query):
    """Ingest data from database."""
    import sqlalchemy as sa
    engine = sa.create_engine(connection_uri)
    return pd.read_sql_query(query, engine)
```
Since the ingestion interface remains decoupled, `process_data` remains completely unaffected.

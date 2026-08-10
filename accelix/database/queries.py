import pandas as pd
from sqlalchemy import text
import logging

logger = logging.getLogger("db_queries")

def load_table(engine, table_name):
    """
    Loads raw table contents into Pandas DataFrame using SQL query.
    """
    query = f"SELECT * FROM {table_name}"
    try:
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        logger.error(f"Error loading table {table_name}: {e}")
        return pd.DataFrame()

def load_all_raw_data(engine):
    """
    Loads the 3 primary tables into a dictionary of DataFrames.
    """
    tables = ["onboarding", "tool_usage", "support_requests"]
    data = {}
    for table in tables:
        data[table] = load_table(engine, table)
    return data

def execute_custom_query(engine, sql_query, params=None):
    """
    Executes parameterized custom SQL query.
    """
    try:
        df = pd.read_sql_query(text(sql_query), engine, params=params)
        return df
    except Exception as e:
        logger.error(f"Error executing custom query: {e}")
        return pd.DataFrame()

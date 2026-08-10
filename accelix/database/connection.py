import os
import logging
from sqlalchemy import create_engine, text
import config

logger = logging.getLogger("accelix_database")

def get_engine(use_fallback=False):
    """
    Returns a production-grade SQLAlchemy engine for PostgreSQL with connection pooling (or SQLite fallback).
    """
    if use_fallback or os.environ.get("USE_SQLITE") == "true":
        logger.info("Using SQLite database engine.")
        return create_engine(config.SQLITE_FALLBACK_URI, connect_args={"check_same_thread": False})

    try:
        engine = create_engine(
            config.POSTGRES_URI,
            pool_size=config.DB_POOL_SIZE,
            max_overflow=config.DB_MAX_OVERFLOW,
            pool_recycle=config.DB_POOL_RECYCLE,
            pool_pre_ping=True
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to PostgreSQL database.")
        return engine
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite database.")
        try:
            default_engine = create_engine(config.DEFAULT_POSTGRES_URI, pool_pre_ping=True)
            with default_engine.connect() as conn:
                conn.execute(text("COMMIT"))
                conn.execute(text(f"CREATE DATABASE {config.DB_NAME}"))
                logger.info(f"Created database '{config.DB_NAME}'.")
            return create_engine(
                config.POSTGRES_URI,
                pool_size=config.DB_POOL_SIZE,
                max_overflow=config.DB_MAX_OVERFLOW,
                pool_pre_ping=True
            )
        except Exception:
            return create_engine(config.SQLITE_FALLBACK_URI, connect_args={"check_same_thread": False})

def initialize_database(engine):
    """
    Executes production DDL schema and view creation scripts safely.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
    views_path = os.path.join(os.path.dirname(__file__), "..", "sql", "views.sql")

    is_sqlite = engine.name == "sqlite"

    with engine.connect() as conn:
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
                if is_sqlite:
                    schema_sql = schema_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
                    schema_sql = schema_sql.replace("TIMESTAMP WITH TIME ZONE", "DATETIME")
                    schema_sql = schema_sql.replace("VARCHAR(50)", "TEXT")
                    schema_sql = schema_sql.replace("VARCHAR(100)", "TEXT")
                    schema_sql = schema_sql.replace("ON DELETE CASCADE", "")

                statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
                for stmt in statements:
                    try:
                        conn.execute(text(stmt))
                    except Exception as err:
                        logger.debug(f"Schema execution notice: {err}")
                conn.commit()

        if os.path.exists(views_path) and not is_sqlite:
            with open(views_path, "r", encoding="utf-8") as f:
                views_sql = f.read()
                statements = [stmt.strip() for stmt in views_sql.split(";") if stmt.strip()]
                for stmt in statements:
                    try:
                        conn.execute(text(stmt))
                    except Exception as err:
                        logger.debug(f"View execution notice: {err}")
                conn.commit()

    logger.info("Database schema and views initialized successfully.")

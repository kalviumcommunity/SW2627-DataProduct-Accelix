import os
import logging

# Project Branding
APP_NAME = "Accelix"
APP_TAGLINE = "Employee Onboarding Friction Analytics"

# PostgreSQL Database Configuration
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "accelix_db")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")

# Production Connection Pool Parameters
DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
DB_POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "1800"))

# Database URIs
POSTGRES_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DEFAULT_POSTGRES_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "accelix_production_fallback.db")
SQLITE_FALLBACK_URI = os.environ.get("SQLITE_FALLBACK_URI", f"sqlite:///{DEFAULT_SQLITE_PATH.replace('\\', '/')}")

# Analytics & Constraint Boundaries
ANALYSIS_WINDOW_DAYS = 30  # Strict Day 0 - 30 analysis scope

# UI Color System
THEME_COLORS = {
    "primary": "#4F46E5",       # Indigo accent
    "secondary": "#0EA5E9",     # Sky blue
    "success": "#10B981",       # Emerald green
    "warning": "#F59E0B",       # Amber
    "danger": "#EF4444",        # Crimson Red
    "background": "#0F172A",    # Dark Slate
    "card_bg": "#1E293B",       # Slate Card
    "text": "#F8FAFC"
}

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

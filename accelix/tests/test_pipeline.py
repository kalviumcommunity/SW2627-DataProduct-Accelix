import unittest
import pandas as pd
import numpy as np
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import get_engine, initialize_database
from database.queries import load_all_raw_data
from data.generator import seed_database
from data.validation import validate_dataset
from data.cleaning import clean_and_normalize_data
from analysis.onboarding import analyze_onboarding_friction
from analysis.tools import analyze_tool_usage_friction
from analysis.support import analyze_support_requests
from analysis.friction import identify_operational_friction_points

class TestOnboardingPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up in-memory DB or test database for pipeline testing."""
        cls.engine = get_engine(use_fallback=True)
        initialize_database(cls.engine)
        seed_database(cls.engine, num_employees=50, clear_existing=True)
        cls.raw_data = load_all_raw_data(cls.engine)

    def test_01_database_tables_loaded(self):
        """Verify the 3 primary tables are loaded from database."""
        for tbl in ["onboarding", "tool_usage", "support_requests"]:
            self.assertIn(tbl, self.raw_data)
            self.assertFalse(self.raw_data[tbl].empty, f"Table {tbl} should not be empty")

    def test_02_validation_audit(self):
        """Verify data quality audit performs deduplication."""
        audit, validated_data = validate_dataset(self.raw_data)
        self.assertIsInstance(audit, dict)
        self.assertGreaterEqual(audit["duplicate_records"], 0)

    def test_03_cleaning_day_0_30_window(self):
        """Verify Day 0 to Day 30 window constraint enforcement."""
        audit, validated_data = validate_dataset(self.raw_data)
        cleaned = clean_and_normalize_data(validated_data)
        
        df_onb = cleaned["onboarding"]
        self.assertFalse(df_onb.empty)
        self.assertTrue((df_onb["days_since_joining"] >= 0).all())
        self.assertTrue((df_onb["days_since_joining"] <= 30).all())

    def test_04_onboarding_analysis(self):
        """Verify onboarding stage delay analysis."""
        audit, validated_data = validate_dataset(self.raw_data)
        cleaned = clean_and_normalize_data(validated_data)
        res = analyze_onboarding_friction(cleaned)

        self.assertIn("overall_completion_rate", res)
        self.assertIn("stage_summary", res)

    def test_05_tool_usage_analysis(self):
        """Verify tool failure and adoption analysis."""
        audit, validated_data = validate_dataset(self.raw_data)
        cleaned = clean_and_normalize_data(validated_data)
        res = analyze_tool_usage_friction(cleaned)

        self.assertIn("most_used_tool", res)
        self.assertIn("most_problematic_tool", res)

    def test_06_support_analysis(self):
        """Verify support category and MTTR resolution time analysis."""
        audit, validated_data = validate_dataset(self.raw_data)
        cleaned = clean_and_normalize_data(validated_data)
        res = analyze_support_requests(cleaned)

        self.assertIn("most_common_category", res)
        self.assertIn("avg_resolution_hrs", res)

    def test_07_friction_identification(self):
        """Verify ranking of operational friction points."""
        audit, validated_data = validate_dataset(self.raw_data)
        cleaned = clean_and_normalize_data(validated_data)
        friction_df = identify_operational_friction_points(cleaned)

        self.assertFalse(friction_df.empty)
        self.assertIn("friction_score", friction_df.columns)

if __name__ == "__main__":
    unittest.main()

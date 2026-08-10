import streamlit as st
import pandas as pd
import numpy as np
import logging

# Page Configuration
st.set_page_config(
    page_title="Accelix — Onboarding Friction Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Dark/Glassmorphism Aesthetic
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0F172A;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Styling */
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700;
    }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600;
    }
    
    div[data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        font-size: 1.6rem !important;
        font-weight: 800;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1E293B;
        border-radius: 8px;
        color: #94A3B8;
        padding: 8px 16px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4F46E5 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

from database.connection import get_engine, initialize_database
from database.queries import load_all_raw_data
from data.generator import seed_database
from data.validation import validate_dataset, validate_uploaded_csv
from data.cleaning import clean_and_normalize_data

from analysis.onboarding import analyze_onboarding_friction
from analysis.tools import analyze_tool_usage_friction
from analysis.support import analyze_support_requests
from analysis.friction import identify_operational_friction_points

from dashboard.overview import render_overview_page
from dashboard.onboarding import render_onboarding_page
from dashboard.tools import render_tools_page
from dashboard.support import render_support_page
from dashboard.friction import render_friction_page
from dashboard.journey import render_journey_page

@st.cache_resource
def get_database_engine():
    """
    Initializes PostgreSQL / SQLite database engine.
    """
    engine = get_engine()
    initialize_database(engine)
    return engine

def main():
    st.sidebar.title("⚡ Accelix Analytics")
    st.sidebar.markdown("**Employee Onboarding Friction Intelligence**")
    st.sidebar.markdown("---")

    # Load Database Backend & Fresh Raw Data
    engine = get_database_engine()
    raw_data = load_all_raw_data(engine)

    # Sidebar CSV File Uploader Section
    with st.sidebar.expander("📤 Upload Custom CSV Dataset", expanded=True):
        st.caption("Upload your custom operational CSV files to analyze:")
        target_tbl = st.selectbox("Select Target Table", ["onboarding", "tool_usage", "support_requests"])
        up_file = st.file_uploader(f"Upload {target_tbl}.csv", type=["csv"], key=f"upload_{target_tbl}")
        
        if up_file is not None:
            try:
                df_up = pd.read_csv(up_file)
                # Validate uploaded CSV schema
                df_clean_up = validate_uploaded_csv(df_up, target_tbl)
                
                if st.button(f"Import {len(df_clean_up)} Rows into '{target_tbl}'", type="primary"):
                    df_clean_up.to_sql(target_tbl, con=engine, if_exists="replace", index=False)
                    st.sidebar.success(f"✅ Imported {len(df_clean_up)} rows into '{target_tbl}'!")
                    st.rerun()
            except Exception as err:
                st.error(f"Upload failed: {err}")
        
        st.markdown("---")
        st.caption("Optional Actions:")
        if st.button("🌱 Load Demo Dataset"):
            seed_database(engine, num_employees=250)
            st.rerun()
        if st.button("🗑️ Clear Database"):
            from sqlalchemy import text
            with engine.connect() as conn:
                for t in ["support_requests", "tool_usage", "onboarding"]:
                    try:
                        conn.execute(text(f"DELETE FROM {t}"))
                    except Exception:
                        pass
                conn.commit()
            st.rerun()

    # Check if database is empty (No uploaded dataset)
    if (raw_data.get("onboarding", pd.DataFrame()).empty and 
        raw_data.get("tool_usage", pd.DataFrame()).empty and 
        raw_data.get("support_requests", pd.DataFrame()).empty):
        
        st.info("📂 **No dataset uploaded yet.**\n\nPlease upload your CSV files (`onboarding.csv`, `tool_usage.csv`, or `support_requests.csv`) in the sidebar under **'📤 Upload Custom CSV Dataset'** to start analyzing your data.")
        return

    # Step 1: Validation Audit
    audit_results, validated_data = validate_dataset(raw_data)

    if audit_results["duplicate_records"] > 0 or audit_results["missing_employee_ids"] > 0:
        with st.sidebar.expander("🛡️ Data Audit Health Check", expanded=False):
            st.write(f"• **Deduplicated Records**: {audit_results['duplicate_records']}")
            st.write(f"• **Missing Employee IDs**: {audit_results['missing_employee_ids']}")
            for w in audit_results["warnings"]:
                st.caption(f"• {w}")

    # Step 2: Cleaning & First 30 Days Scope Filtering
    cleaned_data = clean_and_normalize_data(validated_data)

    # Sidebar Filter: Stage Filter
    all_stages = ["All Stages"]
    if not cleaned_data["onboarding"].empty:
        all_stages += sorted(cleaned_data["onboarding"]["onboarding_stage"].dropna().unique().tolist())
    sel_stage = st.sidebar.selectbox("Filter Onboarding Stage", all_stages)

    filtered_cleaned = cleaned_data
    if sel_stage != "All Stages":
        emp_ids = set(cleaned_data["onboarding"][cleaned_data["onboarding"]["onboarding_stage"] == sel_stage]["employee_id"].unique())
        filtered_cleaned = {
            "onboarding": cleaned_data["onboarding"][cleaned_data["onboarding"]["employee_id"].isin(emp_ids)],
            "tool_usage": cleaned_data["tool_usage"][cleaned_data["tool_usage"]["employee_id"].isin(emp_ids)],
            "support_requests": cleaned_data["support_requests"][cleaned_data["support_requests"]["employee_id"].isin(emp_ids)]
        }

    # Step 3: Run Analytical Engines
    onboarding_analysis = analyze_onboarding_friction(filtered_cleaned)
    tool_analysis = analyze_tool_usage_friction(filtered_cleaned)
    support_analysis = analyze_support_requests(filtered_cleaned)
    friction_df = identify_operational_friction_points(filtered_cleaned)

    # --- 6 STREAMLIT DASHBOARD SECTIONS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 1. OVERVIEW",
        "🚀 2. ONBOARDING FRICTION",
        "🛠️ 3. INTERNAL TOOL USAGE",
        "🎧 4. SUPPORT REQUESTS",
        "⚙️ 5. FRICTION POINTS",
        "🧭 6. FIRST-MONTH JOURNEY"
    ])

    with tab1:
        render_overview_page(onboarding_analysis, tool_analysis, support_analysis, friction_df)
    with tab2:
        render_onboarding_page(onboarding_analysis)
    with tab3:
        render_tools_page(tool_analysis)
    with tab4:
        render_support_page(support_analysis)
    with tab5:
        render_friction_page(friction_df)
    with tab6:
        render_journey_page(filtered_cleaned)

if __name__ == "__main__":
    main()

import streamlit as st
import plotly.express as px
import pandas as pd

def render_overview_page(onboarding_analysis, tool_analysis, support_analysis, friction_df):
    """
    Section 1: OVERVIEW
    Displays required executive KPIs and core bottleneck callouts.
    """
    st.markdown("## 📊 Executive Overview")
    st.markdown("Leadership visibility into operational friction points slowing down new-hire onboarding progress during their first 30 days.")

    # KPI CARDS ROW 1
    col1, col2, col3, col4 = st.columns(4)
    total_hires = onboarding_analysis.get("total_employees", 0)
    completion_rate = onboarding_analysis.get("overall_completion_rate", 0.0)
    avg_comp_time = onboarding_analysis.get("avg_onboarding_time_days", 0.0)
    total_support = support_analysis.get("total_requests", 0)

    col1.metric("New Hires Analyzed", f"{total_hires}")
    col2.metric("Onboarding Completion Rate", f"{completion_rate:.1f}%")
    col3.metric("Avg Onboarding Completion Time", f"{avg_comp_time:.1f} days")
    col4.metric("Total Support Requests", f"{total_support}")

    st.markdown("---")

    # KPI CARDS ROW 2: TOP BOTTLENECK CALLOUTS
    c1, c2, c3 = st.columns(3)
    most_common_issue = support_analysis.get("most_common_category", "N/A")
    top_delayed_stage = onboarding_analysis.get("top_delayed_stage", "N/A")
    most_prob_tool = tool_analysis.get("most_problematic_tool", "N/A")

    c1.metric("Most Common Support Issue", most_common_issue)
    c2.metric("Most Problematic Stage", top_delayed_stage)
    c3.metric("Most Problematic Tool", most_prob_tool)

    st.markdown("---")

    # EXECUTIVE SUMMARY BANNER
    if not friction_df.empty:
        top_friction = friction_df.iloc[0]
        st.error(f"""
        🔥 **PRIMARY OPERATIONAL BOTTLENECK**: **{top_friction['friction_point']}**
        - **Impact**: Affects **{top_friction['affected_pct']}%** of new hires ({top_friction['affected_employees']} employees).
        - **Evidence**: {top_friction['evidence']}
        - **Productivity Effect**: {top_friction['productivity_impact']}
        """)

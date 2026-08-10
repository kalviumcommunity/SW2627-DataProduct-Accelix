import streamlit as st
import plotly.express as px
import pandas as pd

def render_onboarding_page(onboarding_analysis):
    """
    Section 2: ONBOARDING FRICTION
    Visualizes stage completion, average duration per stage, delayed stages, stage-wise friction.
    """
    st.markdown("## 🚀 Onboarding Friction Analytics")
    st.markdown("Identify which onboarding stages experience the longest completion times and highest delay rates.")

    stage_df = onboarding_analysis.get("stage_summary", pd.DataFrame())

    if stage_df.empty:
        st.warning("No onboarding stage data available.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Average Completion Time per Stage (Days)")
        fig_time = px.bar(
            stage_df,
            x="onboarding_stage",
            y="avg_duration_days",
            color="avg_duration_days",
            labels={"onboarding_stage": "Stage Name", "avg_duration_days": "Avg Duration (Days)"},
            title="Average Time Taken to Complete Each Onboarding Stage",
            color_continuous_scale="Reds"
        )
        fig_time.update_layout(template="plotly_dark", height=400, xaxis_tickangle=-30)
        st.plotly_chart(fig_time, use_container_width=True)

    with c2:
        st.markdown("### Stage Delay Rate (%)")
        fig_delay = px.bar(
            stage_df,
            x="onboarding_stage",
            y="delay_rate_pct",
            color="delayed_count",
            labels={"onboarding_stage": "Stage Name", "delay_rate_pct": "% Delayed", "delayed_count": "Delayed Count"},
            title="Percentage of Assigned New Hires Experiencing Delays",
            color_continuous_scale="Oranges"
        )
        fig_delay.update_layout(template="plotly_dark", height=400, xaxis_tickangle=-30)
        st.plotly_chart(fig_delay, use_container_width=True)

    st.markdown("---")

    # STAGE STATUS FUNNEL BREAKDOWN
    st.markdown("### Stage Completion Status Breakdown")
    stage_status_melt = stage_df.melt(
        id_vars=["onboarding_stage"],
        value_vars=["completed_count", "delayed_count", "in_progress_count"],
        var_name="status_type",
        value_name="count"
    )
    fig_funnel = px.bar(
        stage_status_melt,
        x="count",
        y="onboarding_stage",
        color="status_type",
        orientation="h",
        labels={"count": "Assignments Count", "onboarding_stage": "Onboarding Stage"},
        title="Completion vs Delay vs In-Progress Assignments per Stage",
        color_discrete_map={
            "completed_count": "#10B981",
            "delayed_count": "#EF4444",
            "in_progress_count": "#F59E0B"
        }
    )
    fig_funnel.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_funnel, use_container_width=True)

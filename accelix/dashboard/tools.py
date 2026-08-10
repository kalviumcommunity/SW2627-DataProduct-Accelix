import streamlit as st
import plotly.express as px
import pandas as pd

def render_tools_page(tool_analysis):
    """
    Section 3: INTERNAL TOOL USAGE
    Visualizes tool usage frequency, most/least used tools, tool failure rates, tool-support correlations.
    """
    st.markdown("## 🛠️ Internal Tool Usage Analytics")
    st.markdown("Examine tool usage adoption, authentication errors, and software access obstacles for new hires.")

    tool_df = tool_analysis.get("tool_summary", pd.DataFrame())

    if tool_df.empty:
        st.warning("No tool usage data available.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Total Usage Events per Internal Tool")
        fig_usage = px.bar(
            tool_df,
            x="tool_name",
            y="total_usage_events",
            color="active_users",
            labels={"tool_name": "Internal Tool", "total_usage_events": "Usage Events", "active_users": "Active New Hires"},
            title="Tool Usage Volume by New Hires (Most vs Least Used)",
            color_continuous_scale="Blues"
        )
        fig_usage.update_layout(template="plotly_dark", height=400, xaxis_tickangle=-30)
        st.plotly_chart(fig_usage, use_container_width=True)

    with c2:
        st.markdown("### Tool Failure & Error Rate (%)")
        fig_fail = px.bar(
            tool_df,
            x="tool_name",
            y="failure_rate_pct",
            color="failed_events",
            labels={"tool_name": "Internal Tool", "failure_rate_pct": "Failure Rate (%)", "failed_events": "Failed Actions"},
            title="Tool Error/Failure Rates (Unusual & Problematic Patterns)",
            color_continuous_scale="Reds"
        )
        fig_fail.update_layout(template="plotly_dark", height=400, xaxis_tickangle=-30)
        st.plotly_chart(fig_fail, use_container_width=True)

    st.markdown("---")

    # TOOL-RELATED SUPPORT REQUEST OVERLAP
    st.markdown("### Tool Usage Failures for Employees Logging IT Support Tickets")
    tool_sup_df = tool_analysis.get("tool_support_overlap", pd.DataFrame())
    if isinstance(tool_sup_df, pd.DataFrame) and not tool_sup_df.empty:
        fig_overlap = px.bar(
            tool_sup_df,
            x="tool_name",
            y="failed_events",
            color="events_by_supported_employees",
            title="Tool Access Errors Experienced by Employees Requesting Support",
            labels={"tool_name": "Tool", "failed_events": "Failed Tool Events", "events_by_supported_employees": "Total Events"}
        )
        fig_overlap.update_layout(template="plotly_dark", height=380, xaxis_tickangle=-30)
        st.plotly_chart(fig_overlap, use_container_width=True)

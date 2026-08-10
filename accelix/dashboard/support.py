import streamlit as st
import plotly.express as px
import pandas as pd

def render_support_page(support_analysis):
    """
    Section 4: SUPPORT REQUESTS
    Visualizes support requests by category, timeline over first 30 days, MTTR resolution times, repeated issues.
    """
    st.markdown("## 🎧 Support Request History Analytics")
    st.markdown("Analyze IT helpdesk ticket volume, most common request categories, and resolution delays.")

    cat_df = support_analysis.get("cat_summary", pd.DataFrame())

    if cat_df.empty:
        st.warning("No support request data available.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Total Support Requests by Category")
        fig_cat = px.bar(
            cat_df,
            x="request_category",
            y="total_requests",
            color="unresolved_count",
            labels={"request_category": "Request Category", "total_requests": "Total Requests", "unresolved_count": "Unresolved"},
            title="Support Request Density across Operational Categories",
            color_continuous_scale="Oranges"
        )
        fig_cat.update_layout(template="plotly_dark", height=400, xaxis_tickangle=-30)
        st.plotly_chart(fig_cat, use_container_width=True)

    with c2:
        st.markdown("### Average Resolution Time (MTTR in Hours)")
        fig_mttr = px.bar(
            cat_df,
            x="request_category",
            y="avg_resolution_hours",
            color="avg_resolution_hours",
            labels={"request_category": "Request Category", "avg_resolution_hours": "Avg Resolution Hours"},
            title="Mean Time to Resolution (MTTR) by Category",
            color_continuous_scale="Reds"
        )
        fig_mttr.update_layout(template="plotly_dark", height=400, xaxis_tickangle=-30)
        st.plotly_chart(fig_mttr, use_container_width=True)

    st.markdown("---")

    # SUPPORT REQUESTS OVER FIRST 30 DAYS LINE CHART
    st.markdown("### Support Request Activity Over First 30 Days")
    timeline_df = support_analysis.get("timeline_df", pd.DataFrame())
    if isinstance(timeline_df, pd.DataFrame) and not timeline_df.empty:
        fig_line = px.line(
            timeline_df,
            x="days_since_joining",
            y="request_count",
            color="request_category",
            labels={"days_since_joining": "Day Since Joining (Day 0 to 30)", "request_count": "Daily Requests"},
            title="Timeline of Support Request Generation During First Month"
        )
        fig_line.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig_line, use_container_width=True)

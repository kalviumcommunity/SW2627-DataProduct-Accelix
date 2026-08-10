import streamlit as st
import plotly.express as px
import pandas as pd

def render_friction_page(friction_df):
    """
    Section 5: FRICTION POINTS
    Displays major operational friction points ranked by Frequency, Delay, Affected Employees, Support Dependency.
    """
    st.markdown("## ⚙️ Major Operational Friction Points")
    st.markdown("Identified bottlenecks connecting Onboarding Progress, Internal Tool Usage, and Support Request History.")

    if friction_df.empty:
        st.warning("No operational friction points identified.")
        return

    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("### Top Operational Friction Points Ranked by Impact")
        fig_rank = px.bar(
            friction_df,
            x="friction_score",
            y="friction_point",
            color="source",
            orientation="h",
            labels={"friction_score": "Friction Impact Index", "friction_point": "Operational Friction Point"},
            title="Ranked Friction Points (Based on Frequency, Delay & Affected Hires)"
        )
        fig_rank.update_layout(template="plotly_dark", height=420, yaxis={"autorange": "reversed"})
        st.plotly_chart(fig_rank, use_container_width=True)

    with c2:
        st.markdown("### Summary Evidence Table")
        st.dataframe(
            friction_df[["friction_point", "frequency", "affected_pct", "impact_metric", "friction_score"]],
            use_container_width=True,
            height=420
        )

    st.markdown("---")

    # DETAILED FRICTION BREAKDOWN CARDS
    st.markdown("### 📋 Detailed Operational Bottleneck Evidence")

    for idx, row in friction_df.iterrows():
        with st.expander(f"#{idx+1} {row['friction_point']} — Impact Score: {row['friction_score']}", expanded=(idx == 0)):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**📌 Data Source**: `{row['source']}`")
                st.markdown(f"**🔢 Frequency**: {row['frequency']} occurrences")
                st.markdown(f"**👥 Affected New Hires**: {row['affected_employees']} ({row['affected_pct']}% of cohort)")
            with col_b:
                st.markdown(f"**📊 Operational Metric**: {row['impact_metric']}")
                st.markdown(f"**🔍 Empirical Evidence**: {row['evidence']}")
                st.markdown(f"**⚡ Progress Impact**: {row['productivity_impact']}")

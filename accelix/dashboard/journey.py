import streamlit as st
import plotly.express as px
import pandas as pd

def render_journey_page(cleaned_data):
    """
    Section 6: FIRST-MONTH JOURNEY
    Shows how new hires progress through their first 30 days and where operational friction appears.
    """
    st.markdown("## 🧭 First-Month New Hire Journey")
    st.markdown("Chronological tracking of onboarding stage progression, tool usage events, and support tickets from Day 0 to Day 30.")

    df_onb = cleaned_data.get("onboarding", pd.DataFrame())
    df_tool = cleaned_data.get("tool_usage", pd.DataFrame())
    df_sup = cleaned_data.get("support_requests", pd.DataFrame())

    if df_onb.empty:
        st.warning("No journey data available.")
        return

    # WEEKLY COHORT TIMELINE SUMMARY (Days 0-7, 8-14, 15-21, 22-30)
    st.markdown("### Weekly Event Density across First 30 Days")

    # Combine events by relative day
    days_onb = df_onb.groupby("days_since_joining").size().reset_index(name="onboarding_events") if "days_since_joining" in df_onb.columns else pd.DataFrame()
    days_tool = df_tool.groupby("days_since_joining").size().reset_index(name="tool_events") if "days_since_joining" in df_tool.columns else pd.DataFrame()
    days_sup = df_sup.groupby("days_since_joining").size().reset_index(name="support_tickets") if "days_since_joining" in df_sup.columns else pd.DataFrame()

    journey_df = pd.DataFrame({"days_since_joining": list(range(0, 31))})
    if not days_onb.empty:
        journey_df = journey_df.merge(days_onb, on="days_since_joining", how="left").fillna(0)
    if not days_tool.empty:
        journey_df = journey_df.merge(days_tool, on="days_since_joining", how="left").fillna(0)
    if not days_sup.empty:
        journey_df = journey_df.merge(days_sup, on="days_since_joining", how="left").fillna(0)

    fig_journey = px.line(
        journey_df,
        x="days_since_joining",
        y=[col for col in ["onboarding_events", "tool_events", "support_tickets"] if col in journey_df.columns],
        markers=True,
        title="Chronological Event Density Across Day 0 to Day 30",
        labels={"days_since_joining": "Day Since Joining (Day 0 = Start Date)", "value": "Daily Event Volume", "variable": "Event Source"}
    )
    fig_journey.update_layout(template="plotly_dark", height=420)
    st.plotly_chart(fig_journey, use_container_width=True)

    st.markdown("---")

    # 30-DAY MILESTONE MAP
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("#### 🟢 Week 1 (Day 0–7)")
        st.caption("Account creation, hardware provisioning, initial tool logins.")
        sup_w1 = len(df_sup[(df_sup["days_since_joining"] >= 0) & (df_sup["days_since_joining"] <= 7)]) if "days_since_joining" in df_sup.columns else 0
        st.metric("Week 1 Support Tickets", f"{sup_w1}")

    with c2:
        st.markdown("#### 🟡 Week 2 (Day 8–14)")
        st.caption("Tooling access grants, compliance & security training.")
        sup_w2 = len(df_sup[(df_sup["days_since_joining"] >= 8) & (df_sup["days_since_joining"] <= 14)]) if "days_since_joining" in df_sup.columns else 0
        st.metric("Week 2 Support Tickets", f"{sup_w2}")

    with c3:
        st.markdown("#### 🟠 Week 3 (Day 15–21)")
        st.caption("Department orientation, system configuration, shadowing.")
        sup_w3 = len(df_sup[(df_sup["days_since_joining"] >= 15) & (df_sup["days_since_joining"] <= 21)]) if "days_since_joining" in df_sup.columns else 0
        st.metric("Week 3 Support Tickets", f"{sup_w3}")

    with c4:
        st.markdown("#### 🔵 Week 4 (Day 22–30)")
        st.caption("Full operational involvement, first project assignments.")
        sup_w4 = len(df_sup[(df_sup["days_since_joining"] >= 22) & (df_sup["days_since_joining"] <= 30)]) if "days_since_joining" in df_sup.columns else 0
        st.metric("Week 4 Support Tickets", f"{sup_w4}")

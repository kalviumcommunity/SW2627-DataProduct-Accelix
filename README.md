# ⚡ Accelix — Employee Onboarding Friction Analytics Platform

**Accelix** is a specialized data analytics and decision-support platform designed to connect fragmented operational data across onboarding progress, internal tool usage, and IT support request history to answer:

> **"What is slowing new hires down, why is it happening, and what should we fix first?"**

---

## 🏗️ Tech Stack
- **Data Analysis & Processing**: Python (Pandas, NumPy)
- **Database & Data Integration**: PostgreSQL (SQLAlchemy, psycopg2, SQL Views)
- **Dashboard & Visualization**: Streamlit & Plotly Express

---

## 🔑 3 Core Integrated Datasets
1. **`onboarding`**: `employee_id`, `onboarding_stage`, `stage_status`, `start_date`, `completion_date`
2. **`tool_usage`**: `employee_id`, `tool_name`, `usage_date`, `usage_activity`, `usage_status`
3. **`support_requests`**: `employee_id`, `request_category`, `request_date`, `request_status`, `resolution_time`

---

## 🖥️ Streamlit Dashboard Sections
1. **📊 1. OVERVIEW**: Executive KPIs, top delayed stage, top support category, top problematic tool callout.
2. **🚀 2. ONBOARDING FRICTION**: Stage completion rates, average duration per stage, delayed stages breakdown.
3. **🛠️ 3. INTERNAL TOOL USAGE**: Most vs least used tools, failure & error rates (%), tool access errors by supported new hires.
4. **🎧 4. SUPPORT REQUESTS**: Category request volume, MTTR resolution hours, 30-day ticket generation timeline.
5. **⚙️ 5. FRICTION POINTS**: Ranked list of operational friction points based on Frequency, Delay, Affected Hires, and Support Dependency.
6. **🧭 6. FIRST-MONTH JOURNEY**: Chronological event progression tracking new hires across Week 1 (Day 0–7), Week 2 (Day 8–14), Week 3 (Day 15–21), and Week 4 (Day 22–30).

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Pipeline Tests
```bash
python tests/test_pipeline.py
```

### 3. Launch Accelix Dashboard
```bash
streamlit run app.py
```

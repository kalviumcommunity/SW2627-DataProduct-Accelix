import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
import logging

logger = logging.getLogger("data_generator")

ONBOARDING_STAGES = [
    "1. Account & Security Provisioning",
    "2. IT Hardware & Device Setup",
    "3. Internal Tooling Access & Permissions",
    "4. Compliance & Security Training",
    "5. Team Orientation & Setup",
    "6. First Operational Project"
]

TOOLS = [
    "Jira", "GitHub", "Salesforce", "Snowflake", "AWS Console", 
    "Slack", "Okta", "Internal Admin Portal", "Confluence"
]

TOOL_ACTIVITIES = [
    "Account Authentication", "Dashboard Access", "API Call", 
    "Code Commit", "Data Export", "Permission Request"
]

SUPPORT_CATEGORIES = [
    "Access & Permissions",
    "Hardware Failure",
    "Software Licensing",
    "Network & VPN Access",
    "Environment Configuration",
    "Account Lockout"
]

def generate_synthetic_data(num_employees=250, seed=42):
    """
    Generates synthetic dataset strictly matching the 3 required schemas:
    1. onboarding (employee_id, onboarding_stage, stage_status, start_date, completion_date)
    2. tool_usage (employee_id, tool_name, usage_date, usage_activity, usage_status)
    3. support_requests (employee_id, request_category, request_date, request_status, resolution_time)
    """
    random.seed(seed)
    np.random.seed(seed)

    base_date = datetime(2026, 1, 5)
    onboarding = []
    tool_usage = []
    support_requests = []

    req_seq = 1000

    for i in range(1, num_employees + 1):
        emp_id = f"EMP-{1000 + i}"
        
        # Join date spread across last 60 days
        join_offset = random.randint(0, 45)
        joining_date = base_date + timedelta(days=join_offset)

        # High friction profile (30% of new hires experience setup issues)
        is_high_friction = random.random() < 0.30

        # 1. ONBOARDING PROGRESS DATA
        current_date = joining_date.date()
        for stage in ONBOARDING_STAGES:
            stage_duration = random.randint(1, 3) + (random.randint(4, 9) if (is_high_friction and "Access" in stage) else 0)
            comp_date = current_date + timedelta(days=stage_duration)
            expected_date = current_date + timedelta(days=2)

            if comp_date > expected_date:
                status = "Delayed"
            elif random.random() < 0.08:
                status = "In Progress"
            else:
                status = "Completed"

            onboarding.append({
                "employee_id": emp_id,
                "onboarding_stage": stage,
                "stage_status": status,
                "start_date": current_date,
                "completion_date": comp_date if status == "Completed" else None
            })

            current_date = comp_date + timedelta(days=1)

        # 2. INTERNAL TOOL USAGE DATA (First 30 days)
        num_events = random.randint(15, 50)
        for _ in range(num_events):
            rel_day = random.randint(0, 30)
            usage_dt = datetime.combine(joining_date + timedelta(days=rel_day), datetime.min.time()) + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
            tool = random.choice(TOOLS)
            act = random.choice(TOOL_ACTIVITIES)

            failure_prob = 0.40 if (is_high_friction and tool in ["Okta", "AWS Console", "Internal Admin Portal"]) else 0.06
            status = "Success" if random.random() > failure_prob else random.choice(["Failed", "Timeout", "Permission Denied"])

            tool_usage.append({
                "employee_id": emp_id,
                "tool_name": tool,
                "usage_date": usage_dt,
                "usage_activity": act,
                "usage_status": status
            })

        # 3. SUPPORT REQUEST HISTORY DATA (First 30 days)
        num_tickets = random.randint(2, 6) if is_high_friction else random.randint(0, 2)
        for _ in range(num_tickets):
            req_seq += 1
            t_id = f"REQ-{req_seq}"
            rel_day = random.randint(1, 28)
            req_dt = datetime.combine(joining_date + timedelta(days=rel_day), datetime.min.time()) + timedelta(hours=random.randint(9, 17))
            cat = random.choice(SUPPORT_CATEGORIES)

            res_hrs = round(random.uniform(16.0, 72.0), 1) if is_high_friction else round(random.uniform(1.0, 12.0), 1)
            status = "Resolved" if random.random() > 0.1 else "Pending"

            support_requests.append({
                "request_id": t_id,
                "employee_id": emp_id,
                "request_category": cat,
                "request_date": req_dt,
                "request_status": status,
                "resolution_time": res_hrs if status == "Resolved" else None
            })

    # Intentional duplicate event for validation testing
    tool_usage.append(tool_usage[0].copy())

    df_onboarding = pd.DataFrame(onboarding)
    df_tool = pd.DataFrame(tool_usage)
    df_support = pd.DataFrame(support_requests)

    return {
        "onboarding": df_onboarding,
        "tool_usage": df_tool,
        "support_requests": df_support
    }

def seed_database(engine, num_employees=250, clear_existing=True):
    """
    Seeds database tables with generated synthetic data.
    """
    data = generate_synthetic_data(num_employees=num_employees)

    with engine.connect() as conn:
        if clear_existing:
            for table_name in ["support_requests", "tool_usage", "onboarding"]:
                try:
                    conn.execute(text(f"DELETE FROM {table_name}"))
                except Exception:
                    pass
            conn.commit()

        for table_name, df in data.items():
            logger.info(f"Seeding table '{table_name}' with {len(df)} records...")
            df.to_sql(table_name, con=engine, if_exists="append", index=False)
            conn.commit()
    logger.info("Database seeding completed successfully.")

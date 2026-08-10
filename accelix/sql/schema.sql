-- Database Schema for Employee Onboarding Friction Analytics
-- Data Engine: PostgreSQL

-- 1. ONBOARDING TABLE
CREATE TABLE IF NOT EXISTS onboarding (
    onboarding_id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    onboarding_stage VARCHAR(100) NOT NULL,
    stage_status VARCHAR(50) NOT NULL CHECK (stage_status IN ('Completed', 'In Progress', 'Delayed', 'Not Started')),
    start_date DATE NOT NULL,
    completion_date DATE,
    CONSTRAINT check_onboarding_dates CHECK (completion_date IS NULL OR completion_date >= start_date)
);

-- 2. TOOL USAGE TABLE
CREATE TABLE IF NOT EXISTS tool_usage (
    usage_id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    usage_date TIMESTAMP WITH TIME ZONE NOT NULL,
    usage_activity VARCHAR(100) NOT NULL,
    usage_status VARCHAR(50) DEFAULT 'Success' CHECK (usage_status IN ('Success', 'Failed', 'Timeout', 'Permission Denied'))
);

-- 3. SUPPORT REQUEST HISTORY TABLE
CREATE TABLE IF NOT EXISTS support_requests (
    request_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    request_category VARCHAR(100) NOT NULL,
    request_date TIMESTAMP WITH TIME ZONE NOT NULL,
    request_status VARCHAR(50) NOT NULL CHECK (request_status IN ('Resolved', 'Pending', 'In Progress', 'Closed')),
    resolution_time FLOAT CHECK (resolution_time IS NULL OR resolution_time >= 0) -- in hours
);

-- INDEXES FOR QUERY OPTIMIZATION
CREATE INDEX IF NOT EXISTS idx_onboarding_emp ON onboarding(employee_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_emp_date ON tool_usage(employee_id, usage_date);
CREATE INDEX IF NOT EXISTS idx_support_requests_emp_date ON support_requests(employee_id, request_date);

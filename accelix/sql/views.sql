-- Analytical SQL Views for Employee Onboarding Friction Analytics

-- VIEW 1: EMPLOYEE JOINING DATE (Day 0 = earliest onboarding start_date)
CREATE OR REPLACE VIEW vw_employee_start_dates AS
SELECT 
    employee_id,
    MIN(start_date) AS joining_date
FROM onboarding
GROUP BY employee_id;

-- VIEW 2: FIRST 30 DAYS ONBOARDING STAGES
CREATE OR REPLACE VIEW vw_first_30_days_onboarding AS
SELECT 
    o.onboarding_id,
    o.employee_id,
    s.joining_date,
    o.onboarding_stage,
    o.stage_status,
    o.start_date,
    o.completion_date,
    (o.start_date - s.joining_date) AS start_day_offset,
    (o.completion_date - o.start_date) AS stage_duration_days
FROM onboarding o
JOIN vw_employee_start_dates s ON o.employee_id = s.employee_id
WHERE o.start_date >= s.joining_date 
  AND o.start_date <= (s.joining_date + INTERVAL '30 days');

-- VIEW 3: FIRST 30 DAYS TOOL USAGE
CREATE OR REPLACE VIEW vw_first_30_days_tool_usage AS
SELECT 
    t.usage_id,
    t.employee_id,
    s.joining_date,
    t.tool_name,
    t.usage_date,
    t.usage_activity,
    t.usage_status,
    EXTRACT(DAY FROM (t.usage_date - s.joining_date::timestamp)) AS days_since_joining
FROM tool_usage t
JOIN vw_employee_start_dates s ON t.employee_id = s.employee_id
WHERE t.usage_date >= s.joining_date::timestamp
  AND t.usage_date <= (s.joining_date + INTERVAL '30 days')::timestamp;

-- VIEW 4: FIRST 30 DAYS SUPPORT REQUESTS
CREATE OR REPLACE VIEW vw_first_30_days_support AS
SELECT 
    r.request_id,
    r.employee_id,
    s.joining_date,
    r.request_category,
    r.request_date,
    r.request_status,
    r.resolution_time,
    EXTRACT(DAY FROM (r.request_date - s.joining_date::timestamp)) AS days_since_joining
FROM support_requests r
JOIN vw_employee_start_dates s ON r.employee_id = s.employee_id
WHERE r.request_date >= s.joining_date::timestamp
  AND r.request_date <= (s.joining_date + INTERVAL '30 days')::timestamp;

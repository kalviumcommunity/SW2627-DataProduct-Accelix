-- Analytical Queries for Operational Friction Analysis

-- QUERY 1: ONBOARDING STAGE DELAYS AND DURATION
SELECT 
    onboarding_stage,
    COUNT(*) AS total_assignments,
    SUM(CASE WHEN stage_status = 'Completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN stage_status = 'Delayed' THEN 1 ELSE 0 END) AS delayed_count,
    ROUND(AVG(completion_date - start_date)::NUMERIC, 2) AS avg_duration_days
FROM onboarding
GROUP BY onboarding_stage
ORDER BY delayed_count DESC, avg_duration_days DESC;

-- QUERY 2: TOOL USAGE PROBLEMS AND FAILURE RATES
SELECT 
    tool_name,
    COUNT(*) AS total_usage_events,
    SUM(CASE WHEN usage_status != 'Success' THEN 1 ELSE 0 END) AS failed_usage_events,
    ROUND((SUM(CASE WHEN usage_status != 'Success' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 2) AS failure_rate_pct
FROM tool_usage
GROUP BY tool_name
ORDER BY failed_usage_events DESC;

-- QUERY 3: SUPPORT REQUESTS BY CATEGORY AND MTTR
SELECT 
    request_category,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN request_status != 'Resolved' THEN 1 ELSE 0 END) AS unresolved_requests,
    ROUND(AVG(resolution_time)::NUMERIC, 2) AS avg_resolution_hours
FROM support_requests
GROUP BY request_category
ORDER BY total_requests DESC, avg_resolution_hours DESC;

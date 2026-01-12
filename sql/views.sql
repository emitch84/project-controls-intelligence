-- Weekly EV Metrics Aggregated at Project Level
DROP VIEW IF EXISTS vw_ev_weekly;
CREATE VIEW vw_ev_weekly AS
SELECT
    project_id,
    week_ending,
    SUM(pv) as pv,
    SUM(ev) as ev,
    SUM(ac) as ac,
    SUM(bac) as bac
FROM timephased_cost
GROUP BY project_id, week_ending;

-- Weekly Schedule Metrics Aggregated at Project Level
-- Note: 'critical_count' is approximate here, derived from joining back to activities current status if historical status isn't tracked perfectly.
-- Since we don't have timephased activity status (only pct complete), we'll assume critical path status is static or model it simply.
-- For this exercise, we will aggregate pct complete, WEIGHTED by Duration (EVMS Best Practice).
DROP VIEW IF EXISTS vw_schedule_weekly;
CREATE VIEW vw_schedule_weekly AS
SELECT
    tp.project_id,
    tp.week_ending,
    SUM(tp.planned_pct * a.original_duration) / NULLIF(SUM(a.original_duration), 0) as planned_pct_total,
    SUM(tp.actual_pct * a.original_duration) / NULLIF(SUM(a.original_duration), 0) as actual_pct_total,
    COUNT(CASE WHEN a.is_critical THEN 1 END) as critical_count, -- Static approximation
    AVG(a.total_float) as avg_float, -- Static approximation
    COUNT(CASE WHEN a.constraint_type IS NOT NULL THEN 1 END) as constraint_count
FROM timephased_progress tp
JOIN activities a ON tp.activity_id = a.activity_id
GROUP BY tp.project_id, tp.week_ending;

-- Monthly Views (Snapshot at Month End)
DROP VIEW IF EXISTS vw_ev_monthly;
CREATE VIEW vw_ev_monthly AS
SELECT * FROM vw_ev_weekly
WHERE (project_id, week_ending) IN (
    SELECT project_id, MAX(week_ending)
    FROM vw_ev_weekly
    GROUP BY project_id, strftime('%Y-%m', week_ending)
);

DROP VIEW IF EXISTS vw_schedule_monthly;
CREATE VIEW vw_schedule_monthly AS
SELECT * FROM vw_schedule_weekly
WHERE (project_id, week_ending) IN (
    SELECT project_id, MAX(week_ending)
    FROM vw_schedule_weekly
    GROUP BY project_id, strftime('%Y-%m', week_ending)
);

-- WBS Performance Snapshot (Project-to-Date by WBS, Month End)
-- Aggregates cost metrics by WBS for the latest available date in the month
DROP VIEW IF EXISTS vw_wbs_performance_monthly;
CREATE VIEW vw_wbs_performance_monthly AS
SELECT 
    tc.project_id,
    tc.wbs_id,
    tc.week_ending,
    SUM(tc.pv) as pv,
    SUM(tc.ev) as ev,
    SUM(tc.ac) as ac,
    SUM(tc.bac) as bac,
    (SUM(tc.ev) - SUM(tc.ac)) as cv,
    (SUM(tc.ev) - SUM(tc.pv)) as sv
FROM timephased_cost tc
WHERE (tc.project_id, tc.week_ending) IN (
    SELECT project_id, MAX(week_ending)
    FROM timephased_cost
    GROUP BY project_id, strftime('%Y-%m', week_ending)
)
GROUP BY tc.project_id, tc.wbs_id, tc.week_ending;

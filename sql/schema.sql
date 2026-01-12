-- Projects
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    name TEXT,
    client TEXT,
    start_date DATE,
    finish_date DATE
);

-- WBS
CREATE TABLE wbs (
    wbs_id TEXT PRIMARY KEY,
    project_id TEXT,
    wbs_path TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(project_id)
);

-- Activities
CREATE TABLE activities (
    activity_id TEXT PRIMARY KEY,
    project_id TEXT,
    wbs_id TEXT,
    name TEXT,
    activity_type TEXT,
    original_duration INTEGER,
    start DATE,
    finish DATE,
    baseline_start DATE,
    baseline_finish DATE,
    total_float INTEGER,
    is_critical BOOLEAN,
    constraint_type TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(project_id),
    FOREIGN KEY(wbs_id) REFERENCES wbs(wbs_id)
);

-- Timephased Progress
CREATE TABLE timephased_progress (
    project_id TEXT,
    activity_id TEXT,
    week_ending DATE,
    planned_pct REAL,
    actual_pct REAL,
    FOREIGN KEY(activity_id) REFERENCES activities(activity_id)
);

-- Timephased Cost
CREATE TABLE timephased_cost (
    project_id TEXT,
    wbs_id TEXT,
    week_ending DATE,
    bac REAL,
    pv REAL,
    ev REAL,
    ac REAL,
    FOREIGN KEY(wbs_id) REFERENCES wbs(wbs_id)
);

-- Changes
CREATE TABLE changes (
    project_id TEXT,
    change_id TEXT,
    week_ending DATE,
    change_type TEXT,
    delta_bac REAL,
    delta_finish_days INTEGER,
    reason TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(project_id)
);

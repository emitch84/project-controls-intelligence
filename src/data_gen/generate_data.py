
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random

# Configuration
DATA_DIR = "data/raw"
os.makedirs(DATA_DIR, exist_ok=True)

START_DATE = datetime(2024, 1, 1)
WEEKS = 104 # 2 years
PROJECTS_CONFIG = [
    {"id": "P001", "name": "Alpha Infrastructure", "client": "MetaCorp", "budget_factor": 1.0, "perf_profile": "stable"},
    {"id": "P002", "name": "Beta Software Suite", "client": "CyberDyne", "budget_factor": 0.8, "perf_profile": "good"},
    {"id": "P003", "name": "Gamma Facility", "client": "Vandelay", "budget_factor": 1.5, "perf_profile": "deteriorating"},
]

def generate_dates(start_date, weeks):
    return [start_date + timedelta(weeks=i) for i in range(weeks)]

def generate_projects():
    projects = []
    for p in PROJECTS_CONFIG:
        projects.append({
            "project_id": p["id"],
            "name": p["name"],
            "client": p["client"],
            "start_date": START_DATE.strftime("%Y-%m-%d"),
            "finish_date": (START_DATE + timedelta(weeks=WEEKS)).strftime("%Y-%m-%d")
        })
    return pd.DataFrame(projects)

def generate_wbs(project_ids):
    wbs_data = []
    for pid in project_ids:
        # Simple WBS: 1.1 Design, 1.2 Build, 1.3 Test
        wbs_nodes = [
            {"wbs_id": f"{pid}.1", "wbs_path": "Design"},
            {"wbs_id": f"{pid}.2", "wbs_path": "Build"},
            {"wbs_id": f"{pid}.3", "wbs_path": "Test"},
        ]
        for node in wbs_nodes:
            node["project_id"] = pid
            wbs_data.append(node)
    return pd.DataFrame(wbs_data)

def generate_activities(wbs_df):
    activities = []
    for _, row in wbs_df.iterrows():
        pid = row["project_id"]
        wbs_id = row["wbs_id"]
        # Generate 3-5 activities per WBS
        num_acts = random.randint(3, 5)
        for i in range(num_acts):
            act_id = f"{wbs_id}.A{i+1}"
            duration = random.randint(5, 20) * 7 # days
            # Stagger starts based on WBS type roughly
            if "Design" in row["wbs_path"]:
                base_start_offset = random.randint(0, 10) * 7
            elif "Build" in row["wbs_path"]:
                base_start_offset = random.randint(10, 30) * 7
            else: # Test
                base_start_offset = random.randint(30, 50) * 7
            
            start_date = START_DATE + timedelta(days=base_start_offset)
            float_val = random.randint(-5, 20) # Allow for negative float (delay)
            params = {
                "activity_id": act_id,
                "project_id": pid,
                "wbs_id": wbs_id,
                "name": f"Activity {act_id}",
                "activity_type": "Task",
                "original_duration": duration,
                "start": start_date.strftime("%Y-%m-%d"),
                "finish": (start_date + timedelta(days=duration)).strftime("%Y-%m-%d"),
                "baseline_start": start_date.strftime("%Y-%m-%d"),
                "baseline_finish": (start_date + timedelta(days=duration)).strftime("%Y-%m-%d"),
                "total_float": float_val,
                "is_critical": float_val <= 0,
                "constraint_type": random.choice(["ASAP", "Start No Earlier Than", None])
            }
            activities.append(params)
    return pd.DataFrame(activities)

def generate_timephased(projects_df, activities_df):
    progress_records = []
    cost_records = []
    week_endings = generate_dates(START_DATE, WEEKS)
    
    # Cost Data by WBS
    # We will simulate cost at WBS level for simplicity in aggregation, or maybe distribute
    # The requirement says timephased_cost (project_id, wbs_id, week_ending, bac, pv, ev, ac)
    
    for _, proj in projects_df.iterrows():
        pid = proj["project_id"]
        p_cfg = next(p for p in PROJECTS_CONFIG if p["id"] == pid)
        profile = p_cfg["perf_profile"]
        
        # Get WBS for this project
        project_wbs = activities_df[activities_df["project_id"] == pid]["wbs_id"].unique()
        
        for wbs in project_wbs:
            # Random total budget for this WBS
            bac_total = random.randint(100000, 500000) * p_cfg["budget_factor"]
            
            # Simulate S-curve for PV
            cum_pv_pct = 0.0
            cum_ev = 0.0
            cum_ac = 0.0
            
            for i, week_date in enumerate(week_endings):
                # Simple S-Curve logic for PV
                week_num = i + 1
                progress_step = 0.0
                
                # Determine active period for this WBS (simplified)
                if "1.1" in wbs: # Design - early
                   if week_num < 30: progress_step = random.uniform(0.02, 0.05)
                elif "1.2" in wbs: # Build - mid
                   if 10 < week_num < 80: progress_step = random.uniform(0.01, 0.03)
                else: # Test - late
                   if week_num > 50: progress_step = random.uniform(0.02, 0.05)
                
                # PV is cumulative percent * BAC
                prev_pv_pct = cum_pv_pct
                cum_pv_pct = min(1.0, cum_pv_pct + progress_step)
                pv = bac_total * cum_pv_pct
                
                # Calculate Incremental PV
                delta_pv = pv - (bac_total * prev_pv_pct)
                
                # EV calculation (Incremental)
                # Performance profile affects how much of that delta_pv we earn
                if profile == "stable":
                    cpi_factor = random.uniform(0.95, 1.05)
                    spi_factor = random.uniform(0.95, 1.05)
                elif profile == "good":
                    cpi_factor = random.uniform(1.0, 1.1)
                    spi_factor = random.uniform(1.0, 1.1)
                else: # deteriorating
                    degrade = min(0.3, (i / WEEKS) * 0.5)
                    cpi_factor = random.uniform(0.9 - degrade, 1.0)
                    spi_factor = random.uniform(0.8 - degrade, 1.0) # SPI lags too
                
                delta_ev = delta_pv * spi_factor
                
                # Occasional "stops" or "jumps"
                if random.random() < 0.05: delta_ev = 0 # Stalled
                
                
                # Force completion if we are nearing the end of the simulation and it should be done
                if cum_pv_pct >= 0.99 and delta_pv == 0:
                     # If plan is done, we eventually finish the work
                     if cum_ev < bac_total:
                         delta_ev += random.uniform(500, 2000) # Late finish "catch up"
                
                cum_ev += delta_ev
                cum_ev = min(cum_ev, bac_total) # Cap at BAC
                
                # AC calculation (Incremental)
                # AC = EV / CPI (roughly)
                # So delta_ac = delta_ev / cpi_factor
                if cpi_factor > 0.1:
                    delta_ac = delta_ev / cpi_factor
                else:
                    delta_ac = delta_ev # deeply troubled
                
                # Add some noise to AC independent of EV (e.g. fixed costs running while stalled)
                if delta_ev == 0 and cum_pv_pct < 1.0 and cum_pv_pct > 0:
                     delta_ac += random.uniform(100, 500) # Burn rate while stalled
                
                # If EV is catching up late, AC is also burned
                if cum_pv_pct >= 0.99 and delta_ev > 0:
                    delta_ac += delta_ev / random.uniform(0.8, 1.0) # Inefficient late work
                
                cum_ac += delta_ac
                
                cost_records.append({
                    "project_id": pid,
                    "wbs_id": wbs,
                    "week_ending": week_date.strftime("%Y-%m-%d"),
                    "bac": bac_total,
                    "pv": pv,
                    "ev": cum_ev,
                    "ac": cum_ac
                })

    # Progress Data by Activity
    # The requirement: timephased_progress (project_id, activity_id, week_ending, planned_pct, actual_pct)
    for _, act in activities_df.iterrows():
        # Derive progress from the cost logic or just separate coherent simulation
        # Let's simple simulate linear progress between start/finish for planned
        start_dt = datetime.strptime(act["baseline_start"], "%Y-%m-%d")
        finish_dt = datetime.strptime(act["baseline_finish"], "%Y-%m-%d")
        total_days = (finish_dt - start_dt).days
        
        p_cfg = next(p for p in PROJECTS_CONFIG if p["id"] == act["project_id"])
        profile = p_cfg["perf_profile"]
        
        # Initialize actuals
        current_actual_pct = 0.0
        
        # Determine a base performance factor for this activity
        if profile == "deteriorating":
            perf_factor = random.uniform(0.7, 0.9)
        elif profile == "good":
            perf_factor = random.uniform(1.0, 1.1)
        else:
            perf_factor = random.uniform(0.9, 1.05)
            
        prev_planned = 0.0

        for week_date in week_endings:
            # Planned Calculation
            days_passed = (week_date - start_dt).days
            if days_passed <= 0:
                planned_pct = 0.0
            elif days_passed >= total_days:
                planned_pct = 1.0
            else:
                planned_pct = days_passed / total_days
            
            # Actual Calculation (Incremental)
            delta_planned = max(0.0, planned_pct - prev_planned)
            
            # Apply performance factor with slight random walk drift
            perf_factor *= random.uniform(0.98, 1.02)
            
            # Calculate actual increment
            delta_actual = delta_planned * perf_factor
            
            # Add noise to the increment (sometimes we halt, sometimes we jump, but never negative)
            if random.random() < 0.1: # 10% chance of no progress (blocker)
                delta_actual = 0.0
            
            current_actual_pct += delta_actual
            current_actual_pct = min(1.0, current_actual_pct)
            
            # Sanity check: if planned is 0, actual should likely be 0 unless started early
            # For simplicity, let's allow early starts if we modeled them, but here we clamped delta_planned
            # logic relies on planned start.
             
            progress_records.append({
                "project_id": act["project_id"],
                "activity_id": act["activity_id"],
                "week_ending": week_date.strftime("%Y-%m-%d"),
                "planned_pct": planned_pct,
                "actual_pct": current_actual_pct
            })
            
            prev_planned = planned_pct
            
    return pd.DataFrame(cost_records), pd.DataFrame(progress_records)

def generate_changes(projects_df):
    changes = []
    week_endings = generate_dates(START_DATE, WEEKS)
    
    for _, proj in projects_df.iterrows():
        # Generate 5-10 rand changes per project
        num_changes = random.randint(5, 10)
        for k in range(num_changes):
             week = random.choice(week_endings)
             changes.append({
                 "project_id": proj["project_id"],
                 "change_id": f"CHG-{k+1:03d}",
                 "week_ending": week.strftime("%Y-%m-%d"),
                 "change_type": random.choice(["Scope Add", "Re-baseline", "Budget Transfer"]),
                 "delta_bac": random.randint(-5000, 20000),
                 "delta_finish_days": random.randint(-5, 15),
                 "reason": "Client Request"
             })
    return pd.DataFrame(changes)

def main():
    print("Generating Projects...")
    projects = generate_projects()
    projects.to_csv(f"{DATA_DIR}/projects.csv", index=False)
    
    print("Generating WBS...")
    wbs = generate_wbs(projects["project_id"].unique())
    wbs.to_csv(f"{DATA_DIR}/wbs.csv", index=False)
    
    print("Generating Activities...")
    activities = generate_activities(wbs)
    activities.to_csv(f"{DATA_DIR}/activities.csv", index=False)
    
    print("Generating Timephased Data...")
    cost, progress = generate_timephased(projects, activities)
    cost.to_csv(f"{DATA_DIR}/timephased_cost.csv", index=False)
    progress.to_csv(f"{DATA_DIR}/timephased_progress.csv", index=False)
    
    print("Generating Changes...")
    changes = generate_changes(projects)
    changes.to_csv(f"{DATA_DIR}/changes.csv", index=False)
    
    print("Data generation complete.")

if __name__ == "__main__":
    main()


import pandas as pd
import sqlite3

class QualityCheckException(Exception):
    pass

def check_negative_values(conn):
    query = """
    SELECT count(*) as cnt FROM timephased_cost 
    WHERE pv < 0 OR ev < 0 OR ac < 0
    """
    cursor = conn.cursor()
    count = cursor.execute(query).fetchone()[0]
    if count > 0:
        raise QualityCheckException(f"Found {count} records with negative PV, EV, or AC.")
    print("PASS: No negative cost values.")

def check_percent_complete(conn):
    query = """
    SELECT count(*) as cnt FROM timephased_progress 
    WHERE planned_pct < 0 OR planned_pct > 1.0 OR actual_pct < 0 OR actual_pct > 1.0
    """
    cursor = conn.cursor()
    count = cursor.execute(query).fetchone()[0]
    if count > 0:
        raise QualityCheckException(f"Found {count} records with invalid percent complete (not between 0 and 1).")
    print("PASS: Percent complete within range.")

def check_start_finish_dates(conn):
    query = """
    SELECT count(*) as cnt FROM activities 
    WHERE start > finish OR baseline_start > baseline_finish
    """
    cursor = conn.cursor()
    count = cursor.execute(query).fetchone()[0]
    if count > 0:
        raise QualityCheckException(f"Found {count} activities with inverted dates.")
    print("PASS: Activity dates valid.")

def run_all_checks(db_path):
    conn = sqlite3.connect(db_path)
    try:
        check_negative_values(conn)
        check_percent_complete(conn)
        check_start_finish_dates(conn)
        print("All data quality checks passed.")
    except QualityCheckException as e:
        print(f"QUALITY CHECK FAILED: {e}")
        # sys.exit(1) # Optional: fail the build
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    run_all_checks("data/processed/pc_intel.db")

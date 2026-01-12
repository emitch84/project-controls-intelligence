
import sqlite3
import pandas as pd
import os
import sys

DB_PATH = "data/processed/pc_intel.db"
RAW_DIR = "data/raw"
SQL_DIR = "sql"

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    with open(f"{SQL_DIR}/schema.sql", 'r') as f:
        conn.executescript(f.read())
    with open(f"{SQL_DIR}/views.sql", 'r') as f:
        conn.executescript(f.read())
    conn.close()
    print("Database initialized.")

def load_data():
    conn = sqlite3.connect(DB_PATH)
    
    files_map = {
        "projects.csv": "projects",
        "wbs.csv": "wbs",
        "activities.csv": "activities",
        "timephased_progress.csv": "timephased_progress",
        "timephased_cost.csv": "timephased_cost",
        "changes.csv": "changes"
    }
    
    for filename, table_name in files_map.items():
        file_path = os.path.join(RAW_DIR, filename)
        if os.path.exists(file_path):
            print(f"Loading {filename} into {table_name}...")
            df = pd.read_csv(file_path)
            df.to_sql(table_name, conn, if_exists='append', index=False)
        else:
            print(f"Warning: {filename} not found.")
    
    conn.close()
    print("Data loading complete.")

if __name__ == "__main__":
    init_db()
    load_data()

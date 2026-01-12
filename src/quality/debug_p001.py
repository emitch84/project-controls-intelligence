
import sqlite3
import pandas as pd
from src.metrics.engine import calculate_kpis

def debug_p001():
    conn = sqlite3.connect("data/processed/pc_intel.db")
    df = pd.read_sql("SELECT * FROM vw_ev_weekly WHERE project_id='P001'", conn)
    conn.close()
    
    df = calculate_kpis(df)
    
    # Filter for Sept-Dec (Weeks 35-52 approx, and 87-104)
    # Actually just string match the date
    df['month'] = df['week_ending'].str[5:7]
    df_q4 = df[df['month'].isin(['09', '10', '11', '12'])]
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print("\n--- P001 Q4 Data (First 10 rows) ---")
    print(df_q4[['week_ending', 'pv', 'ev', 'ac', 'cpi', 'spi']].head(10))
    
    print("\n--- P001 Q4 Data (Last 10 rows) ---")
    print(df_q4[['week_ending', 'pv', 'ev', 'ac', 'cpi', 'spi']].tail(10))

if __name__ == "__main__":
    debug_p001()

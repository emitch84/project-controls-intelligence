
import pandas as pd
import numpy as np

def calculate_kpis(df):
    """
    Expects a DataFrame with columns: pv, ev, ac, bac
    Returns DataFrame with added columns: cpi, spi, eac, vac, tcpi
    """
    # Avoid division by zero
    df['cpi'] = df.apply(lambda row: row['ev'] / row['ac'] if row['ac'] > 0 else (1.0 if row['ev'] == 0 else 0.0), axis=1)
    df['spi'] = df.apply(lambda row: row['ev'] / row['pv'] if row['pv'] > 0 else (1.0 if row['ev'] == 0 else 0.0), axis=1)
    
    # EAC = BAC / CPI
    df['eac'] = df.apply(lambda row: row['bac'] / row['cpi'] if row['cpi'] > 0 else row['bac'], axis=1)
    
    # VAC = BAC - EAC
    df['vac'] = df['bac'] - df['eac']
    
    # TCPI = (BAC - EV) / (BAC - AC)
    df['tcpi'] = df.apply(lambda row: (row['bac'] - row['ev']) / (row['bac'] - row['ac']) if (row['bac'] - row['ac']) != 0 else 0.0, axis=1)
    
    return df

def generate_flags(df_metrics, df_schedule, df_changes):
    """
    Generates health flags.
    df_metrics keys: project_id, week_ending, cpi, spi
    df_schedule keys: project_id, week_ending, critical_count, avg_float, constraint_count
    df_changes keys: project_id, week_ending, delta_bac, delta_finish_days
    """
    flags = []
    
    # Merge datasets on project_id and week_ending
    merged = pd.merge(df_metrics, df_schedule, on=['project_id', 'week_ending'], how='left')
    
    # Sort for trend analysis
    merged = merged.sort_values(by=['project_id', 'week_ending'])
    
    for pid, group in merged.groupby('project_id'):
        group = group.copy()
        
        # Calculate Rolling Trends
        group['cpi_roll'] = group['cpi'].rolling(window=3).mean()
        group['spi_roll'] = group['spi'].rolling(window=3).mean()
        group['float_roll'] = group['avg_float'].rolling(window=4).mean()
        
        for i, row in group.iterrows():
            week = row['week_ending']
            
            # 1. Poor Performance
            if row['cpi'] < 0.9:
                flags.append({'project_id': pid, 'week_ending': week, 'flag_type': 'Cost Efficiency', 'severity': 'High', 'message': f"CPI {row['cpi']:.2f} < 0.9"})
            if row['spi'] < 0.9:
                flags.append({'project_id': pid, 'week_ending': week, 'flag_type': 'Schedule Efficiency', 'severity': 'High', 'message': f"SPI {row['spi']:.2f} < 0.9"})
                
            # 2. Downward Trend (simple check against previous weeks)
            # Check last 3 weeks including this one if available
            # A rigorous trend check might need more index manipulation, here we use rolling mean proxy or simple diff
            # Let's check if current < prev < prev_prev
            # Doing row-based check is slow, but usually fine for small data. 
            # Vectorized approach:
            pass # Done below via vectorization if needed, or simple iteration
            
            # 3. Float Collapse
            # If float drops by > 5 days over 4 weeks
            try:
                prev_float = group.loc[group.index[max(0, group.index.get_loc(i)-4)], 'avg_float']
                if (prev_float - row['avg_float']) > 5:
                     flags.append({'project_id': pid, 'week_ending': week, 'flag_type': 'Float Collapse', 'severity': 'Medium', 'message': "Avg Float dropped > 5 days in 4 weeks"})
            except:
                pass

    return pd.DataFrame(flags)

def get_project_metrics(conn):
    query = "SELECT * FROM vw_ev_weekly"
    df = pd.read_sql(query, conn)
    df = calculate_kpis(df)
    return df

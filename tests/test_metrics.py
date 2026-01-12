
import pytest
import pandas as pd
from src.metrics.engine import calculate_kpis

def test_cpi_calculation():
    data = {
        'ev': [100.0, 50.0, 0.0],
        'ac': [100.0, 100.0, 0.0],
        'pv': [100.0, 50.0, 0.0],
        'bac': [1000.0, 1000.0, 1000.0]
    }
    df = pd.DataFrame(data)
    result = calculate_kpis(df)
    
    assert result.iloc[0]['cpi'] == 1.0
    assert result.iloc[1]['cpi'] == 0.5
    assert result.iloc[2]['cpi'] == 0.0 # Handle div/0

def test_spi_calculation():
    data = {
        'ev': [80.0],
        'pv': [100.0],
        'ac': [80.0],
        'bac': [1000.0]
    }
    df = pd.DataFrame(data)
    result = calculate_kpis(df)
    
    assert result.iloc[0]['spi'] == 0.8

def test_vac_calculation():
    # VAC = BAC - EAC; EAC = BAC/CPI
    data = {
        'ev': [50.0],
        'ac': [100.0], # CPI = 0.5
        'pv': [50.0],
        'bac': [1000.0]
    }
    # EAC should be 1000 / 0.5 = 2000
    # VAC should be 1000 - 2000 = -1000
    df = pd.DataFrame(data)
    result = calculate_kpis(df)
    
    assert result.iloc[0]['eac'] == 2000.0
    assert result.iloc[0]['vac'] == -1000.0

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from oficial import ajustar_para_horario_comercial, calcular_tempo_trabalho, calcular_tempo_medio

def run_tests():
    print("--- Running Logic Tests ---")
    
    # 1. Test ajustar_para_horario_comercial
    tests = [
        ("Monday 10:00 (inside)", datetime(2026, 8, 24, 10, 0), datetime(2026, 8, 24, 10, 0)),
        ("Monday 20:00 (after work Mon-Thu)", datetime(2026, 8, 24, 20, 0), datetime(2026, 8, 25, 8, 0)),
        ("Friday 18:00 (after work Fri)", datetime(2026, 8, 28, 18, 0), datetime(2026, 8, 31, 8, 0)), # Friday after 17:00 goes to Monday 8:00
        ("Saturday 14:00 (weekend)", datetime(2026, 8, 29, 14, 0), datetime(2026, 8, 31, 8, 0)),
        ("Sunday 10:00 (weekend)", datetime(2026, 8, 30, 10, 0), datetime(2026, 8, 31, 8, 0)),
    ]
    
    for label, inp, expected in tests:
        res = ajustar_para_horario_comercial(inp)
        assert res == expected, f"Failed {label}: expected {expected}, got {res}"
        print(f"Passed: {label} -> {res}")
        
    # 2. Test calcular_tempo_trabalho
    # Mon 10:00 to Mon 12:00 -> 2 hours
    assert calcular_tempo_trabalho(datetime(2026, 8, 24, 10, 0), datetime(2026, 8, 24, 12, 0)) == pd.Timedelta(hours=2)
    
    # Mon 20:00 to Tue 10:00 -> 2 hours (Tue 8:00 to 10:00)
    assert calcular_tempo_trabalho(datetime(2026, 8, 24, 20, 0), datetime(2026, 8, 25, 10, 0)) == pd.Timedelta(hours=2)
    
    print("Passed: calcular_tempo_trabalho checks")
    
    # 3. Test calcular_tempo_medio
    df_mock = pd.DataFrame([
        {"Pedido": 1, "DataEntradaSeparacao": "2026-08-24 10:00:00", "DataFaturamento": "2026-08-24 12:00:00"}, # 2h
        {"Pedido": 2, "DataEntradaSeparacao": "2026-08-24 20:00:00", "DataFaturamento": "2026-08-25 10:00:00"}, # 2h (after work)
    ])
    
    avg = calcular_tempo_medio(df_mock, 'DataEntradaSeparacao', 'DataFaturamento')
    print(f"Calculated average: {avg}")
    assert avg == "2h 0m", f"Expected '2h 0m', got '{avg}'"
    print("Passed: calcular_tempo_medio checks")
    
    print("--- All Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()

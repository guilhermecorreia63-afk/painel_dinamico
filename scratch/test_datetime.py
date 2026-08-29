import pandas as pd
from pathlib import Path

historico_pedidos_file = Path("data/historico_pedidos.csv")
df = pd.read_csv(historico_pedidos_file)
val = df.loc[162, 'DataEntradaSeparacao']
print("val:", repr(val))

try:
    print("Default parsing:", pd.to_datetime(val))
except Exception as e:
    print("Default parsing error:", e)

try:
    print("Format mixed:", pd.to_datetime(val, format='mixed'))
except Exception as e:
    print("Format mixed error:", e)

try:
    print("Format ISO8601:", pd.to_datetime(val, format='ISO8601'))
except Exception as e:
    print("Format ISO8601 error:", e)

try:
    print("Custom format:", pd.to_datetime(val, format='%Y-%m-%d %H:%M:%S'))
except Exception as e:
    print("Custom format error:", e)

# Test column-wide parsing options
print("\nColumn-wide format='mixed':")
try:
    print(pd.to_datetime(df['DataEntradaSeparacao'], errors='coerce', format='mixed').tail(10))
except Exception as e:
    print("Error:", e)

print("\nColumn-wide format='ISO8601':")
try:
    print(pd.to_datetime(df['DataEntradaSeparacao'], errors='coerce', format='ISO8601').tail(10))
except Exception as e:
    print("Error:", e)

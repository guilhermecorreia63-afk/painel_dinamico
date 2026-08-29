import pandas as pd
from pathlib import Path
from datetime import datetime

historico_pedidos_file = Path("data/historico_pedidos.csv")
df = pd.read_csv(historico_pedidos_file)
print("Columns:", df.columns)
print("Data Types:\n", df.dtypes)
print("\nLast 10 rows:")
print(df.tail(10))

if 'DataEntradaSeparacao' in df.columns:
    parsed_date = pd.to_datetime(df['DataEntradaSeparacao'], errors='coerce').dt.date
    print("\nParsed Dates (last 10):")
    print(parsed_date.tail(10))
    print("Parsed Date Types:", [type(x) for x in parsed_date.tail(10)])

data_selecionada = datetime(2026, 8, 24).date()
print("\ndata_selecionada:", data_selecionada, type(data_selecionada))
matching = df[parsed_date == data_selecionada]
print("Matching rows count:", len(matching))
print(matching)

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Load csv
csv_path = Path("data/historico_pedidos.csv")
if not csv_path.exists():
    print("CSV does not exist.")
    exit()

df_csv = pd.read_csv(csv_path)

# Load json
with open("dados_pedidos.json", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

if lines[0].strip().startswith("Resultado da API:"):
    json_str = "".join(lines[1:])
else:
    json_str = "".join(lines)

data = json.loads(json_str)
orders = data.get("pedido_venda_produto", [])

# Map of order_number -> (dInc, hInc)
order_inc_times = {}
for p in orders:
    num = p.get("cabecalho", {}).get("numero_pedido")
    info = p.get("infoCadastro", {})
    dInc = info.get("dInc")
    hInc = info.get("hInc")
    if num and dInc and hInc:
        order_inc_times[int(num)] = (dInc, hInc)

# Function to adjust to business hours
def ajustar_para_horario_comercial(dt):
    while True:
        wd = dt.weekday()
        if wd <= 3:  # Segunda a Quinta (08:00 às 18:00)
            start_work = dt.replace(hour=8, minute=0, second=0, microsecond=0)
            end_work = dt.replace(hour=18, minute=0, second=0, microsecond=0)
            if dt < start_work:
                return start_work
            elif dt >= end_work:
                dt = (dt + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                continue
            else:
                return dt
        elif wd == 4:  # Sexta-feira (08:00 às 17:00)
            start_work = dt.replace(hour=8, minute=0, second=0, microsecond=0)
            end_work = dt.replace(hour=17, minute=0, second=0, microsecond=0)
            if dt < start_work:
                return start_work
            elif dt >= end_work:
                dt = (dt + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                continue
            else:
                return dt
        else:  # Sábado e Domingo
            dt = (dt + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
            continue

def parse_and_adjust_datetime(data_str, hora_str):
    try:
        dt = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M:%S")
    except Exception:
        dt = datetime.now()
    dt_adjusted = ajustar_para_horario_comercial(dt)
    return dt_adjusted.strftime("%Y-%m-%d %H:%M:%S")

# Fix NaN values in DataEntradaSeparacao
fixed_count = 0
for idx, row in df_csv.iterrows():
    pedido = int(row['Pedido'])
    if pd.isna(row['DataEntradaSeparacao']):
        if pedido in order_inc_times:
            dInc, hInc = order_inc_times[pedido]
            ts_separacao = parse_and_adjust_datetime(dInc, hInc)
            df_csv.loc[idx, 'DataEntradaSeparacao'] = ts_separacao
            print(f"Fixed Pedido {pedido}: Set Entrada Separação to {ts_separacao}")
            fixed_count += 1

if fixed_count > 0:
    df_csv.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"Saved CSV with {fixed_count} fixed rows.")
else:
    print("No rows needed fixing or could be found in json.")

import pandas as pd
from pathlib import Path
from datetime import datetime

historico_pedidos_file = Path("data/historico_pedidos.csv")
df_historico_pedidos = pd.read_csv(historico_pedidos_file)

# Parse with format='mixed'
df_historico_pedidos['DataEntradaSeparacao_Parsed'] = pd.to_datetime(
    df_historico_pedidos['DataEntradaSeparacao'], errors='coerce', format='mixed'
).dt.date

df_historico_pedidos['DataFaturamento_Parsed'] = pd.to_datetime(
    df_historico_pedidos['DataFaturamento'], errors='coerce', format='mixed'
).dt.date

data_selecionada = datetime(2026, 8, 24).date()

# Count
entraram_hoje = df_historico_pedidos[df_historico_pedidos['DataEntradaSeparacao_Parsed'] == data_selecionada]
total_entrou_separacao = int(entraram_hoje['Pedido'].nunique())

faturados_hoje = df_historico_pedidos[df_historico_pedidos['DataFaturamento_Parsed'] == data_selecionada]
total_faturado_dia = int(faturados_hoje['Pedido'].nunique())

print("For date 2026-08-24:")
print("Entraram em Separação:", total_entrou_separacao)
print("Total Faturados no Dia:", total_faturado_dia)
print("\nOrders that entered separation today:")
print(entraram_hoje[['Pedido', 'DataEntradaSeparacao', 'DataFaturamento']])
print("\nOrders that were faturados today:")
print(faturados_hoje[['Pedido', 'DataEntradaSeparacao', 'DataFaturamento']])

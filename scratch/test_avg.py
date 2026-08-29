import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Copy the calcular_tempo_trabalho logic
def calcular_tempo_trabalho(t_start, t_end):
    if pd.isna(t_start) or pd.isna(t_end):
        return pd.Timedelta(0)
    
    t_start = pd.to_datetime(t_start)
    t_end = pd.to_datetime(t_end)
    
    if t_start > t_end:
        return pd.Timedelta(0)
    
    total_working_time = pd.Timedelta(0)
    current_date = t_start.date()
    end_date = t_end.date()
    
    while current_date <= end_date:
        weekday = current_date.weekday() # Monday = 0, ..., Sunday = 6
        
        # Define os limites do expediente do dia
        if weekday <= 3:  # Segunda a Quinta (08:00 às 18:00)
            work_start_time = datetime.combine(current_date, datetime.strptime("08:00:00", "%H:%M:%S").time())
            work_end_time = datetime.combine(current_date, datetime.strptime("18:00:00", "%H:%M:%S").time())
            is_working_day = True
        elif weekday == 4:  # Sexta-feira (08:00 às 17:00)
            work_start_time = datetime.combine(current_date, datetime.strptime("08:00:00", "%H:%M:%S").time())
            work_end_time = datetime.combine(current_date, datetime.strptime("17:00:00", "%H:%M:%S").time())
            is_working_day = True
        else:  # Sábado e Domingo (sem expediente)
            is_working_day = False
            
        if is_working_day:
            # Interseção do período com o expediente do dia
            int_start = max(t_start, work_start_time)
            int_end = min(t_end, work_end_time)
            if int_start < int_end:
                total_working_time += (int_end - int_start)
                
        current_date += timedelta(days=1)
        
    return total_working_time

historico_pedidos_file = Path("data/historico_pedidos.csv")
df_historico_pedidos = pd.read_csv(historico_pedidos_file)

df_historico_pedidos['DataEntradaSeparacao_Parsed'] = pd.to_datetime(df_historico_pedidos['DataEntradaSeparacao'], errors='coerce', format='mixed').dt.date
df_historico_pedidos['DataFaturamento_Parsed'] = pd.to_datetime(df_historico_pedidos['DataFaturamento'], errors='coerce', format='mixed').dt.date

data_selecionada = datetime(2026, 8, 24).date()
faturados_hoje = df_historico_pedidos[df_historico_pedidos['DataFaturamento_Parsed'] == data_selecionada].copy()

df_valid_dia = faturados_hoje[faturados_hoje['DataEntradaSeparacao'].notna() & faturados_hoje['DataFaturamento'].notna()].copy()
if not df_valid_dia.empty:
    diff_dia = df_valid_dia.apply(lambda row: calcular_tempo_trabalho(row['DataEntradaSeparacao'], row['DataFaturamento']), axis=1)
    diff_dia = diff_dia[diff_dia > pd.Timedelta(0)]
    if not diff_dia.empty:
        mean_diff_dia = diff_dia.mean()
        total_seconds_dia = int(mean_diff_dia.total_seconds())
        dias_dia = total_seconds_dia // 86400
        horas_dia = (total_seconds_dia % 86400) // 3600
        minutos_dia = (total_seconds_dia % 3600) // 60
        
        parts_dia = []
        if dias_dia > 0:
            parts_dia.append(f"{dias_dia}d")
        if horas_dia > 0 or dias_dia > 0:
            parts_dia.append(f"{horas_dia}h")
        parts_dia.append(f"{minutos_dia}m")
        tempo_medio_dia = " ".join(parts_dia)
        print("Average time for faturados on 2026-08-24:", tempo_medio_dia)
    else:
        print("No diffs > 0")
else:
    print("No valid rows")

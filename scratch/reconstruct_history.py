import os
import re
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

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

def parse_and_adjust_datetime(data_str, hora_str, fallback_date_dmy=None):
    # Clean data_str
    if not data_str or str(data_str).strip() in ('', '-', 'nan'):
        if fallback_date_dmy:
            data_str = fallback_date_dmy
        else:
            return None
    else:
        data_str = str(data_str).strip()

    # Clean hora_str
    if not hora_str or str(hora_str).strip() in ('', '-', 'nan'):
        hora_str = "08:00:00"
    else:
        hora_str = str(hora_str).strip()

    # Try parsing
    try:
        # Standard format DD/MM/YYYY HH:MM:SS
        dt = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M:%S")
    except Exception:
        try:
            # Maybe date has different format or just DD/MM/YYYY
            dt = datetime.strptime(data_str, "%d/%m/%Y")
            # Set time from hora_str
            time_parts = hora_str.split(":")
            h = int(time_parts[0]) if len(time_parts) > 0 else 8
            m = int(time_parts[1]) if len(time_parts) > 1 else 0
            s = int(time_parts[2]) if len(time_parts) > 2 else 0
            dt = dt.replace(hour=h, minute=m, second=s)
        except Exception:
            return None

    dt_adjusted = ajustar_para_horario_comercial(dt)
    return dt_adjusted.strftime("%Y-%m-%d %H:%M:%S")

def main():
    data_dir = Path("data")
    if not data_dir.exists():
        print("Data directory not found.")
        return

    # Find all detailed files: pedidos_detalhados_YYYY-MM-DD.csv
    pattern = re.compile(r"pedidos_detalhados_(\d{4}-\d{2}-\d{2})\.csv")
    files = []
    for f in data_dir.glob("pedidos_detalhados_*.csv"):
        m = pattern.match(f.name)
        if m:
            date_str = m.group(1)
            files.append((date_str, f))
            
    # Sort files chronologically
    files.sort(key=lambda x: x[0])
    
    if not files:
        print("No detailed CSV files found.")
        return

    print(f"Found {len(files)} detailed files. Processing in chronological order...")
    
    # Structure: {Pedido: {'Pedido': int, 'DataEntradaSeparacao': str, 'DataEntradaFaturar': str, 'DataFaturamento': str}}
    historico = {}

    for date_str, fpath in files:
        # Convert YYYY-MM-DD from filename to DD/MM/YYYY for fallback
        dt_file = datetime.strptime(date_str, "%Y-%m-%d")
        fallback_date_dmy = dt_file.strftime("%d/%m/%Y")

        try:
            df = pd.read_csv(fpath)
        except Exception as e:
            print(f"Error reading {fpath.name}: {e}")
            continue

        for _, row in df.iterrows():
            try:
                pedido_val = row.get("Pedido")
                if pd.isna(pedido_val):
                    continue
                pedido_id = int(pedido_val)
                etapa_atual = str(row.get("Etapa", "")).strip()

                # Get columns if present, otherwise default to None
                data_inc = row.get("Data Inclusao") if "Data Inclusao" in df.columns else None
                hora_inc = row.get("Hora Inclusao") if "Hora Inclusao" in df.columns else None
                data_alt = row.get("Data Alteração") if "Data Alteração" in df.columns else None
                hora_alt = row.get("Hora Alteração") if "Hora Alteração" in df.columns else None
                data_fat = row.get("Data Faturamento") if "Data Faturamento" in df.columns else None
                hora_fat = row.get("Hora Faturamento") if "Hora Faturamento" in df.columns else None

                # Compute potential timestamps
                # 1. Separation
                ts_separacao = parse_and_adjust_datetime(data_inc, hora_inc)
                if ts_separacao is None:
                    # Fallback to alteration or filename date
                    ts_separacao = parse_and_adjust_datetime(data_alt, hora_alt, fallback_date_dmy)

                # 2. Faturar
                ts_faturar = parse_and_adjust_datetime(data_alt, hora_alt, fallback_date_dmy)

                # 3. Faturamento
                ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)
                if ts_faturamento is None and etapa_atual == "Faturado":
                    ts_faturamento = parse_and_adjust_datetime(data_alt, hora_alt, fallback_date_dmy)

                if pedido_id not in historico:
                    historico[pedido_id] = {
                        "Pedido": pedido_id,
                        "DataEntradaSeparacao": ts_separacao,
                        "DataEntradaFaturar": None,
                        "DataFaturamento": None
                    }

                # Update DataEntradaSeparacao if not set
                if historico[pedido_id]["DataEntradaSeparacao"] is None and ts_separacao is not None:
                    historico[pedido_id]["DataEntradaSeparacao"] = ts_separacao

                # Rules based on stage
                if etapa_atual in ("Separar Estoque", "Em Processo", "10", "20", "80"):
                    # These are early stages
                    pass

                elif etapa_atual in ("Faturar", "50"):
                    if historico[pedido_id]["DataEntradaFaturar"] is None and ts_faturar is not None:
                        historico[pedido_id]["DataEntradaFaturar"] = ts_faturar

                elif etapa_atual in ("Faturado", "60"):
                    if ts_faturamento is not None:
                        if historico[pedido_id]["DataFaturamento"] is None:
                            historico[pedido_id]["DataFaturamento"] = ts_faturamento
                        
                        # If DataEntradaFaturar is not set, try to fill it
                        if historico[pedido_id]["DataEntradaFaturar"] is None:
                            if ts_faturar is not None and ts_faturar < ts_faturamento:
                                historico[pedido_id]["DataEntradaFaturar"] = ts_faturar
                            else:
                                historico[pedido_id]["DataEntradaFaturar"] = ts_faturamento

            except Exception as e:
                continue

    # Final checks: if DataEntradaSeparacao is still null, set to DataEntradaFaturar or DataFaturamento
    for ped, val in historico.items():
        if val["DataEntradaSeparacao"] is None:
            if val["DataEntradaFaturar"] is not None:
                val["DataEntradaSeparacao"] = val["DataEntradaFaturar"]
            elif val["DataFaturamento"] is not None:
                val["DataEntradaSeparacao"] = val["DataFaturamento"]

    # Convert to DataFrame
    df_new = pd.DataFrame(list(historico.values()))
    
    # Sort by Pedido ascending
    df_new = df_new.sort_values(by="Pedido").reset_index(drop=True)
    
    # Check null counts
    nulls = df_new.isna().sum()
    print("Null counts in reconstructed history:")
    print(nulls)
    
    print(f"Total reconstructed orders: {len(df_new)}")
    
    # Save to data/historico_pedidos.csv (overwriting)
    out_path = data_dir / "historico_pedidos.csv"
    
    # Backup existing if any
    if out_path.exists():
        backup_path = data_dir / f"historico_pedidos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        out_path.rename(backup_path)
        print(f"Backed up old CSV to {backup_path.name}")
        
    df_new.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"Reconstructed history saved successfully to {out_path.name}!")

if __name__ == "__main__":
    main()

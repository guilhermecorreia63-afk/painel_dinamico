import os
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np
import sqlite3

def carregar_secrets():
    secrets = {}
    
    # 1. Tenta carregar do .env (local)
    caminho_env = Path(".env")
    if caminho_env.exists():
        try:
            with open(caminho_env, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        parts = line.split("=", 1)
                        key = parts[0].strip()
                        val = parts[1].strip()
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        secrets[key] = val
        except Exception:
            pass
            
    # 2. Tenta carregar do .streamlit/secrets.toml
    caminho_toml = Path(".streamlit/secrets.toml")
    if caminho_toml.exists():
        try:
            with open(caminho_toml, "rb") as f:
                import tomllib
                secrets.update(tomllib.load(f))
        except Exception:
            pass
            
    return secrets

def executar_batch_chunked(statements, chunk_size=200):
    if not statements:
        return
    secrets = carregar_secrets()
    url = secrets.get("TURSO_DATABASE_URL")
    token = secrets.get("TURSO_AUTH_TOKEN")
    
    if url and token:
        if url.startswith("libsql://"):
            url = "https://" + url[9:]
        import libsql_client
        print(f"Connecting to Turso: {url}")
        with libsql_client.create_client_sync(url=url, auth_token=token) as client:
            for i in range(0, len(statements), chunk_size):
                chunk = statements[i:i+chunk_size]
                client.batch(chunk)
                print(f"  Sent chunk of {len(chunk)} queries...")
    else:
        print("Connecting to local SQLite database (data/database_local.db)...")
        conn = sqlite3.connect("data/database_local.db")
        try:
            cursor = conn.cursor()
            for query, params in statements:
                cursor.execute(query, params or ())
            conn.commit()
        finally:
            conn.close()

def main():
    print("Ensuring tables are initialized...")
    init_statements = [
        ("""
            CREATE TABLE IF NOT EXISTS historico_pedidos (
                Pedido INTEGER PRIMARY KEY,
                DataEntradaSeparacao TEXT,
                DataEntradaFaturar TEXT,
                DataFaturamento TEXT
            )
        """, ()),
        ("""
            CREATE TABLE IF NOT EXISTS pedidos_detalhados (
                Data TEXT,
                Pedido INTEGER,
                Etapa TEXT,
                DataFaturamento TEXT,
                HoraFaturamento TEXT,
                DataAlteracao TEXT,
                HoraAlteracao TEXT,
                DataInclusao TEXT,
                HoraInclusao TEXT,
                Departamento TEXT,
                Transportadora TEXT,
                ValorTotal REAL,
                PesoBruto REAL,
                PRIMARY KEY (Data, Pedido)
            )
        """, ()),
        ("""
            CREATE TABLE IF NOT EXISTS historico_diario_resumo (
                Data TEXT PRIMARY KEY,
                TotalPendentes INTEGER,
                TotalFaturados INTEGER
            )
        """, ())
    ]
    executar_batch_chunked(init_statements)
    
    data_dir = Path("data")
    statements_to_run = []

    # 1. Prepare historico_pedidos.csv
    hist_file = data_dir / "historico_pedidos.csv"
    if hist_file.exists():
        print(f"Loading {hist_file.name}...")
        try:
            df = pd.read_csv(hist_file)
            df = df.replace({np.nan: None})
            for _, row in df.iterrows():
                statements_to_run.append((
                    "INSERT OR REPLACE INTO historico_pedidos (Pedido, DataEntradaSeparacao, DataEntradaFaturar, DataFaturamento) VALUES (?, ?, ?, ?)",
                    (int(row['Pedido']), row['DataEntradaSeparacao'], row['DataEntradaFaturar'], row['DataFaturamento'])
                ))
            print(f"  Added {len(df)} orders to queue.")
        except Exception as e:
            print(f"Error reading historico_pedidos.csv: {e}")
    else:
        print("historico_pedidos.csv not found, skipping.")
        
    # 2. Prepare historico_diario_resumo.csv
    resumo_file = data_dir / "historico_diario_resumo.csv"
    if resumo_file.exists():
        print(f"Loading {resumo_file.name}...")
        try:
            df = pd.read_csv(resumo_file)
            df = df.replace({np.nan: None})
            for _, row in df.iterrows():
                statements_to_run.append((
                    "INSERT OR REPLACE INTO historico_diario_resumo (Data, TotalPendentes, TotalFaturados) VALUES (?, ?, ?)",
                    (str(row['Data']), int(row['Total Pendentes']), int(row['Total Faturados']))
                ))
            print(f"  Added {len(df)} daily summaries to queue.")
        except Exception as e:
            print(f"Error reading historico_diario_resumo.csv: {e}")
    else:
        print("historico_diario_resumo.csv not found, skipping.")

    # 3. Prepare all pedidos_detalhados_YYYY-MM-DD.csv
    pattern = re.compile(r"pedidos_detalhados_(\d{4}-\d{2}-\d{2})\.csv")
    detalhados_files = []
    for f in data_dir.glob("pedidos_detalhados_*.csv"):
        m = pattern.match(f.name)
        if m:
            detalhados_files.append((m.group(1), f))
            
    if detalhados_files:
        print(f"Found {len(detalhados_files)} detailed daily CSV snapshots. Loading...")
        for date_str, fpath in detalhados_files:
            try:
                df = pd.read_csv(fpath)
                df = df.replace({np.nan: None})
                
                has_hora_fat = "Hora Faturamento" in df.columns
                has_hora_alt = "Hora Alteração" in df.columns
                has_data_inc = "Data Inclusao" in df.columns
                has_hora_inc = "Hora Inclusao" in df.columns
                
                for _, row in df.iterrows():
                    statements_to_run.append((
                        """
                        INSERT OR REPLACE INTO pedidos_detalhados (
                            Data, Pedido, Etapa, DataFaturamento, HoraFaturamento,
                            DataAlteracao, HoraAlteracao, DataInclusao, HoraInclusao,
                            Departamento, Transportadora, ValorTotal, PesoBruto
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            date_str,
                            int(row.get('Pedido', 0)),
                            row.get('Etapa'),
                            row.get('Data Faturamento'),
                            row.get('Hora Faturamento') if has_hora_fat else None,
                            row.get('Data Alteração'),
                            row.get('Hora Alteração') if has_hora_alt else None,
                            row.get('Data Inclusao') if has_data_inc else None,
                            row.get('Hora Inclusao') if has_hora_inc else None,
                            row.get('Departamento'),
                            row.get('Transportadora'),
                            float(row.get('Valor Total', 0.0)) if row.get('Valor Total') is not None else 0.0,
                            float(row.get('Peso Bruto (kg)', 0.0)) if row.get('Peso Bruto (kg)') is not None else 0.0
                        )
                    ))
                print(f"  Added rows from {fpath.name} to queue.")
            except Exception as e:
                print(f"Error reading {fpath.name}: {e}")
    else:
        print("No detailed daily CSV snapshots found, skipping.")
        
    # Execute all queued queries
    if statements_to_run:
        print(f"Executing migration batch of {len(statements_to_run)} operations...")
        executar_batch_chunked(statements_to_run)
        print("Database migration completed successfully!")
    else:
        print("No data found to migrate.")

if __name__ == "__main__":
    main()

import sqlite3
import pandas as pd

# Conecta ao banco de dados local
db_path = "data/database_local.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Descobrir as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tabelas encontradas:")
for t in tables:
    print(f"- {t[0]}")

# Identificar a tabela de histórico
tabela_historico = "historico_pedidos"

print(f"\nTabela selecionada: {tabela_historico}")
# 2. Trazer as últimas 10 linhas
df = pd.read_sql_query(f"SELECT * FROM {tabela_historico} ORDER BY rowid DESC LIMIT 10", conn)
# Reverter para ordem cronológica de inserção (o mais recente por último na tabela do chat)
df = df.iloc[::-1]

# Exibir no formato Markdown de forma manual para evitar a dependência de 'tabulate'
headers = df.columns.tolist()
markdown_table = "| " + " | ".join(headers) + " |\n"
markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
for _, row in df.iterrows():
    markdown_table += "| " + " | ".join(str(val).replace("\n", " ") for val in row.values) + " |\n"

print("\nÚltimas 10 linhas em formato de tabela Markdown:")
print(markdown_table)

conn.close()

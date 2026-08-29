# -*- coding: utf-8 -*-
with open("oficial_turso.py", "r", encoding="utf-8") as f:
    codigo = f.read()

# Substitui a indexação incorreta pela correta usando idx[0]
codigo_corrigido = codigo.replace("loc[idx, 'DataFaturamento']", "loc[idx[0], 'DataFaturamento']")

with open("oficial_turso.py", "w", encoding="utf-8") as f:
    f.write(codigo_corrigido)

print("[AGENTE] Variavel de indexacao idx[0] corrigida com sucesso!")

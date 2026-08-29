# -*- coding: utf-8 -*-
import re

with open("oficial.py", "r", encoding="utf-8") as f:
    codigo = f.read()

# 1. Localiza a assinatura original da etapa Faturado no arquivo bom
match = re.search(r"(\s*elif\s+etapa_atual\s*==\s*['\"]Faturado['\"]:.*?)(?=elif|if\s+pedido_id|def|class|\Z)", codigo, re.DOTALL)

if not match:
    print("Erro: Estrutura padrão de etapas não encontrada no oficial.py.")
    exit(1)

bloco_antigo = match.group(1)

# 2. Reconstrói o bloco mantendo a indentação correta padrão de 20 espaços do oficial.py, 
# removendo a gravação do DataEntradaFaturar e usando o payload nativo
bloco_novo = (
    "elif etapa_atual == 'Faturado':\n"
    "                    # REGRA CORRIGIDA: Captura apenas o horario nativo de faturamento da API e nao altera a entrada\n"
    "                    data_fat = payload.get('data_faturamento')\n"
    "                    hora_fat = payload.get('hora_faturamento', '00:00:00')\n"
    "                    if data_fat:\n"
    "                        ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)\n"
    "                        if pd.isna(df_historico.loc[idx[0], 'DataFaturamento']):\n"
    "                            df_historico.loc[idx[0], 'DataFaturamento'] = ts_faturamento\n"
    "                            houve_alteracao = True\n"
)

codigo_final = codigo.replace(bloco_antigo, bloco_novo)

with open("oficial.py", "w", encoding="utf-8") as f:
    f.write(codigo_final)

print("[AGENTE LOCAL] Arquivo oficial.py atualizado com sucesso e livre de bugs!")

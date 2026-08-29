# -*- coding: utf-8 -*-
import re

with open("oficial_turso.py", "r", encoding="utf-8") as f:
    codigo = f.read()

# Trecho que contem o desalinhamento gerado pelos replaces anteriores
padrao_errado = (
    "            # REGRA 3: Pedidos Faturados\n"
    "            elif etapa_atual == 'Faturado':\n"
    "                        # REGRA 3: Captura apenas o horario nativo de faturamento da API\n"
    "                        data_fat = payload.get('data_faturamento')\n"
    "                        hora_fat = payload.get('hora_faturamento', '00:00:00')\n"
    "                        if data_fat:\n"
    "                            ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)\n"
    "                            if pd.isna(df_historico.loc[idx[0], 'DataFaturamento']):\n"
    "                                df_historico.loc[idx[0], 'DataFaturamento'] = ts_faturamento\n"
    "                                houve_alteracao = True\n\n"
    "                    if pedido_id in df_historico['Pedido'].values:"
)

# Bloco perfeitamente alinhado com 24 espacos internos e 12 espacos nos blocos principais
padrao_corrigido = (
    "            # REGRA 3: Pedidos Faturados\n"
    "            elif etapa_atual == 'Faturado':\n"
    "                        # REGRA 3: Captura apenas o horario nativo de faturamento da API\n"
    "                        data_fat = payload.get('data_faturamento')\n"
    "                        hora_fat = payload.get('hora_faturamento', '00:00:00')\n"
    "                        if data_fat:\n"
    "                            ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)\n"
    "                            if pd.isna(df_historico.loc[idx[0], 'DataFaturamento']):\n"
    "                                df_historico.loc[idx[0], 'DataFaturamento'] = ts_faturamento\n"
    "                                houve_alteracao = True\n\n"
    "                    if pedido_id in df_historico['Pedido'].values:"
)

# Se não achar o casamento exato de string devido a espacos invisiveis, vamos forçar uma limpeza via Regex
codigo_ajustado = re.sub(
    r"(\s*#\s*REGRA\s*3:.*?)(if\s+pedido_id\s+in\s+df_historico)",
    r"            # REGRA 3: Pedidos Faturados\n            elif etapa_atual == 'Faturado':\n                        data_fat = payload.get('data_faturamento')\n                        hora_fat = payload.get('hora_faturamento', '00:00:00')\n                        if data_fat:\n                            ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)\n                            if pd.isna(df_historico.loc[idx[0], 'DataFaturamento']):\n                                df_historico.loc[idx[0], 'DataFaturamento'] = ts_faturamento\n                                houve_alteracao = True\n\n                    \2",
    codigo,
    flags=re.DOTALL
)

with open("oficial_turso.py", "w", encoding="utf-8") as f:
    f.write(codigo_ajustado)

print("[AGENTE] Alinhamento estrutural executado!")

# -*- coding: utf-8 -*-
with open("oficial_turso.py", "r", encoding="utf-8") as f:
    linhas = f.readlines()

novas_linhas = []
for linha in linhas:
    # 1. Corrige a fusão do comentário com o elif
    if "# REGRA 3: Pedidos Faturadoselif etapa_atual" in linha:
        novas_linhas.append("            # REGRA 3: Pedidos Faturados\n")
        novas_linhas.append("            elif etapa_atual == 'Faturado':\n")
        continue

    # 2. Corrige o desalinhamento das regras internas do bloco faturado
    if "data_fat = payload.get" in linha:
        novas_linhas.append("                        data_fat = payload.get('data_faturamento')\n")
        continue
    if "hora_fat = payload.get" in linha:
        novas_linhas.append("                        hora_fat = payload.get('hora_faturamento', '00:00:00')\n")
        continue
    if "if data_fat:" in linha and "if data_fat == hoje" not in linha:
        novas_linhas.append("                        if data_fat:\n")
        continue
    if "ts_faturamento = parse_and_adjust_datetime" in linha:
        novas_linhas.append("                            ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)\n")
        continue
    if "if pd.isna(df_historico.loc[idx" in linha and "DataFaturamento" in linha:
        novas_linhas.append("                            if pd.isna(df_historico.loc[idx[0], 'DataFaturamento']):\n")
        continue
    if "df_historico.loc[idx" in linha and "DataFaturamento" in linha and "=" in linha:
        novas_linhas.append("                                df_historico.loc[idx[0], 'DataFaturamento'] = ts_faturamento\n")
        continue
    if "houve_alteracao = True" in linha and len(linha) - len(linha.lstrip()) == 24:
        novas_linhas.append("                                houve_alteracao = True\n")
        continue

    # 3. Corrige o if que perdeu a indentação e foi para o canto da tela
    if linha.startswith("if pedido_id in df_historico"):
        novas_linhas.append("                    if pedido_id in df_historico['Pedido'].values:\n")
        continue

    # Pula linhas residuais da quebra de texto anterior
    if "entrada" in linha and len(linha.strip()) == 7:
        continue
    if "# REGRA 3: Captura apenas o" in list(linha) or "horario nativo de faturamento" in linha:
        continue

    novas_linhas.append(linha)

with open("oficial_turso.py", "w", encoding="utf-8") as f:
    f.writelines(novas_linhas)

print("[AGENTE LOCAL] Arquivo oficial_turso.py higienizado linha por linha!")

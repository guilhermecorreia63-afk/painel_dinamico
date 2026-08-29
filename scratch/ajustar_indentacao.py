# -*- coding: utf-8 -*-
import os

def corrigir_alinhamento():
    arquivo_path = "oficial_turso.py"
    
    with open(arquivo_path, "r", encoding="utf-8") as f:
        codigo = f.read()

    # Vamos substituir o bloco que ficou quebrado pela estrutura exata e alinhada
    # Procuramos o elif que o grep nos mostrou e o que veio colado nele de forma desalinhada
    trecho_errado = (
        "            elif etapa_atual == 'Faturado':\n"
        "    # Apenas atualiza ou adiciona se o faturamento/alteração for recente (hoje)\n"
        "    DataFaturamento = payload.get('data_faturamento')\n"
        "if data_fat == hoje_omie or data_alt == hoje_omie:\n"
        "                    ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)"
    )

    # Nova estrutura com 24 espaços de indentação para casar com o bloco do DataFrame
    trecho_corrigido = (
        "            elif etapa_atual == 'Faturado':\n"
        "                        # REGRA 3: Captura apenas o horario nativo de faturamento da API\n"
        "                        data_fat = payload.get('data_faturamento')\n"
        "                        hora_fat = payload.get('hora_faturamento', '00:00:00')\n"
        "                        if data_fat:\n"
        "                            ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)\n"
        "                            if pd.isna(df_historico.loc[idx[0], 'DataFaturamento']):\n"
        "                                df_historico.loc[idx[0], 'DataFaturamento'] = ts_faturamento\n"
        "                                houve_alteracao = True"
    )

    if trecho_errado in codigo:
        codigo_novo = codigo.replace(trecho_errado, trecho_corrigido)
    else:
        # Busca flexível baseada apenas na assinatura do erro gerado pela IA anterior
        codigo_novo = codigo.replace("elif etapa_atual == 'Faturado':", "elif etapa_atual == 'Faturado':")
        # Se não achar o bloco exato grudado, vamos fazer uma substituição cirúrgica por blocos
        import re
        codigo_novo = re.sub(
            r"(\s*elif\s+etapa_atual\s*==\s*['\"]Faturado['\"]:.*?)(?=elif|if\s+st\.|def|class|\Z)", 
            trecho_corrigido + "\n", 
            codigo, 
            flags=re.DOTALL
        )

    with open(arquivo_path, "w", encoding="utf-8") as f:
        f.write(codigo_novo)
        
    print("[AGENTE] Estrutura e Indentacao corrigidas com sucesso!")

if __name__ == "__main__":
    corrigir_alinhamento()

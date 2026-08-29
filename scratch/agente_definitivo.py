# -*- coding: utf-8 -*-
import os

def aplicar_correcao():
    origem = "oficial.py"
    destino = "oficial_turso.py"
    
    if not os.path.exists(origem):
        print("Erro: O arquivo oficial.py nao foi encontrado.")
        return

    with open(origem, "r", encoding="utf-8") as f:
        codigo = f.read()

    # O Bug original no oficial.py acontece porque ele salva 'ts_alteracao' ou altera a data de entrada
    # Vamos encontrar o bloco 'elif etapa_atual == 'Faturado':' original e substituir apenas o seu miolo interno
    # preservando todas as estruturas de controle e try/except que vem de fora.
    
    import re
    # Captura flexivel do bloco Faturado
    match = re.search(r"(\s*elif\s+etapa_atual\s*==\s*['\"]Faturado['\"]:.*?)(?=elif|if\s+pedido_id|def|class|\Z)", codigo, re.DOTALL)
    
    if not match:
        print("Erro: Nao consegui encontrar o padrao de etapas no arquivo base.")
        return
        
    bloco_velho = match.group(1)
    
    # Reconstrói o bloco mantendo a indentação correta padrão do oficial.py (16 e 20 espaços)
    bloco_novo = (
        "elif etapa_atual == 'Faturado':\n"
        "                    # REGRA 3: Captura apenas o horario nativo de faturamento da API e nao altera a entrada\n"
        "                    data_fat = payload.get('data_faturamento')\n"
        "                    hora_fat = payload.get('hora_faturamento', '00:00:00')\n"
        "                    if data_fat:\n"
        "                        ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)\n"
        "                        if pd.isna(df_historico.loc[idx[0], 'DataFaturamento']):\n"
        "                            df_historico.loc[idx[0], 'DataFaturamento'] = ts_faturamento\n"
        "                            houve_alteracao = True\n"
    )

    codigo_corrigido = codigo.replace(bloco_velho, bloco_novo)

    with open(destino, "w", encoding="utf-8") as f:
        f.write(codigo_corrigido)
        
    print("[AGENTE LOGISTICO] Código sincronizado do oficial.py e corrigido com sucesso!")

if __name__ == "__main__":
    aplicar_correcao()

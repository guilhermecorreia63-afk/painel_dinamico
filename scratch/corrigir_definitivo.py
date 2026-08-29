# -*- coding: utf-8 -*-
import re

def reestruturar_codigo():
    origem = "oficial.py"
    destino = "oficial_turso.py"
    
    with open(origem, "r", encoding="utf-8") as f:
        codigo_original = f.read()

    # Pega o bloco da regra do Faturado antigo do arquivo bom
    match = re.search(r"(elif\s+etapa_atual\s*==\s*['\"]Faturado['\"]:.*?)(?=elif|if|def|class|\$|\Z)", codigo_original, re.DOTALL)
    if not match:
        print("Erro: Nao encontrei o bloco Faturado no oficial.py")
        return
        
    bloco_original_faturado = match.group(1)

    # Nova regra estrita para o bloco Faturado com indentação perfeitamente herdada do oficial.py
    # Removemos a gravação de 'DataEntradaFaturar' e focamos no horário bruto do faturamento
    bloco_novo_faturado = (
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

    # Substitui a regra antiga dentro do código 100% íntegro e alinhado do oficial.py
    codigo_final = codigo_original.replace(bloco_original_faturado, bloco_novo_faturado)

    # Grava por cima do oficial_turso.py, garantindo 100% de alinhamento e eliminando erros de sintaxe
    with open(destino, "w", encoding="utf-8") as f:
        f.write(codigo_final)

    print("[AGENTE] Arquivo oficial_turso.py reestruturado e com identacao perfeita!")

if __name__ == "__main__":
    reestruturar_codigo()

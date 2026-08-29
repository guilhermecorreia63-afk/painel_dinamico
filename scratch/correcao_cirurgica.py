import os

def aplicar_ajuste():
    arquivo_path = "oficial_turso.py"
    
    if not os.path.exists(arquivo_path):
        print(f"Erro: O arquivo {arquivo_path} não foi encontrado!")
        return

    with open(arquivo_path, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    codigo_alterado = False
    novas_linhas = []
    pulando_antigo = False

    for i, linha in enumerate(linhas):
        # Localiza o bloco exato do bug que você me enviou
        if "elif etapa_atual == 'Faturado':" in linha or 'elif etapa_atual == "Faturado":' in linha:
            novas_linhas.append(linha)
            # Injeta a regra correta: remove a DataEntradaFaturar e busca apenas o horario de faturamento bruto
            novas_linhas.append("    # REGRA 3: Captura apenas o horário nativo de faturamento da API e nunca altera a entrada\n")
            novas_linhas.append("    dados['DataFaturamento'] = payload.get('data_faturamento')\n")
            pulando_antigo = True
            codigo_alterado = True
            continue
        
        # Se estamos dentro do bloco antigo do Faturado, pula as linhas antigas que geravam o bug de < 1m
        if pulando_antigo:
            # Se a linha atual pertence a outro bloco condicional ou finalizou a indentação, paramos de pular
            if (linha.strip().startswith("elif ") or linha.strip().startswith("if ") or 
                linha.strip().startswith("else:") or (linha.strip() and not linha.startswith("    "))):
                pulando_antigo = False
            else:
                continue # Pula a linha antiga (DataEntradaFaturar que estava aqui dentro)

        novas_linhas.append(linha)

    if codigo_alterado:
        with open(arquivo_path, "w", encoding="utf-8") as f:
            f.writelines(novas_linhas)
        print("Sucesso! O bloco 'Faturado' foi corrigido cirurgicamente sem alterar o resto do projeto.")
    else:
        print("Aviso: O bloco 'elif etapa_atual == 'Faturado':' não foi encontrado ou já foi alterado.")

if __name__ == "__main__":
    aplicar_ajuste()

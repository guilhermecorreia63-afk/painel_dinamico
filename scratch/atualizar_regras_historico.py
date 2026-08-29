# -*- coding: utf-8 -*-
import os

def aplicar_correcao_cirurgica(filename):
    if not os.path.exists(filename):
        print(f"[ATUALIZADOR] Arquivo {filename} não encontrado.")
        return

    print(f"[ATUALIZADOR] Lendo {filename}...")
    with open(filename, "r", encoding="utf-8") as f:
        codigo = f.read()

    # 1. Adiciona a função parse_datetime_real caso ela não exista
    funcao_real = (
        "def parse_datetime_real(data_str, hora_str):\n"
        "    if not data_str or data_str == '-' or not hora_str or hora_str == '-':\n"
        "        dt = datetime.now()\n"
        "    else:\n"
        "        try:\n"
        "            dt = datetime.strptime(f\"{data_str} {hora_str}\", \"%d/%m/%Y %H:%M:%S\")\n"
        "        except Exception:\n"
        "            dt = datetime.now()\n"
        "    return dt.strftime(\"%Y-%m-%d %H:%M:%S\")\n"
    )

    if "def parse_datetime_real" not in codigo:
        # Insere logo após a definição de parse_and_adjust_datetime
        ancora = "    return dt_adjusted.strftime(\"%Y-%m-%d %H:%M:%S\")"
        if ancora in codigo:
            codigo = codigo.replace(ancora, ancora + "\n\n" + funcao_real)
            print(f"[ATUALIZADOR] Função parse_datetime_real inserida no arquivo {filename}.")
        else:
            # Fallback de inserção
            codigo = funcao_real + "\n" + codigo
            print(f"[ATUALIZADOR] Função parse_datetime_real adicionada no início de {filename}.")

    # 2. Modifica a Regra 3 para usar a nova função
    alvo_original = "ts_faturamento = parse_and_adjust_datetime(data_fat, hora_fat)"
    alvo_corrigido = "ts_faturamento = parse_datetime_real(data_fat, hora_fat)"

    if alvo_original in codigo:
        codigo = codigo.replace(alvo_original, alvo_corrigido)
        print(f"[ATUALIZADOR] Regra 3 modificada para usar o horário real em {filename}.")
    else:
        print(f"[ATUALIZADOR] Alvo de substituição não encontrado ou já alterado em {filename}.")

    # Salva o código corrigido
    with open(filename, "w", encoding="utf-8") as f:
        f.write(codigo)
    print(f"[ATUALIZADOR] {filename} atualizado com sucesso!")

print("[ATUALIZADOR] Iniciando atualizações cirúrgicas locais para corrigir as regras do histórico...")
aplicar_correcao_cirurgica("oficial.py")
aplicar_correcao_cirurgica("oficial_turso.py")
print("[ATUALIZADOR] Concluído com sucesso.")

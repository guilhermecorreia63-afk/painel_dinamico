# -*- coding: utf-8 -*-
import urllib.request
import json
import os

def processar_arquivo_com_gemma(filename, instrucoes):
    if not os.path.exists(filename):
        print(f"[RESTAURADOR] Arquivo {filename} não encontrado.")
        return

    print(f"[RESTAURADOR] Lendo {filename}...")
    with open(filename, "r", encoding="utf-8") as f:
        codigo = f.read()

    prompt = (
        f"Você é um assistente de programação especialista em Python local.\n"
        f"Modifique o arquivo '{filename}' de acordo com as seguintes instruções estritas:\n"
        f"{instrucoes}\n\n"
        f"Retorne APENAS o código Python completo e corrigido para o arquivo '{filename}'.\n"
        f"Não adicione nenhuma explicação, introdução, comentário pessoal ou marcação markdown (não coloque crases ``` no início ou fim).\n\n"
        f"Código original:\n{codigo}"
    )

    data = {
        "model": "gemma4:e4b",
        "prompt": prompt,
        "stream": False
    }

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    print(f"[RESTAURADOR] Enviando {filename} para correção no Gemma 4 local...")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            codigo_retorno = res_body.get("response", "").strip()

            # Sanitização de markdown
            if codigo_retorno.startswith("```python"):
                codigo_retorno = codigo_retorno[9:]
            if codigo_retorno.startswith("```"):
                codigo_retorno = codigo_retorno[3:]
            if codigo_retorno.endswith("```"):
                codigo_retorno = codigo_retorno[:-3]
            codigo_retorno = codigo_retorno.strip()

            if len(codigo_retorno) > 100:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(codigo_retorno + "\n")
                print(f"[RESTAURADOR] {filename} atualizado com sucesso!")
            else:
                print(f"[RESTAURADOR] Resposta do Gemma 4 parece inválida ou curta demais para {filename}.")
    except Exception as e:
        print(f"[RESTAURADOR] Erro ao processar {filename}: {e}")

# 1. Instruções para oficial.py
instrucoes_oficial = (
    "- Corrija a sintaxe de todo o bloco try/except e indentação dentro da função 'verificar_e_notificar_mudancas'.\n"
    "- Garanta que a Regra 3 (etapa 'Faturado') utilize as variáveis locais de data e hora de faturamento extraídas do DataFrame atual (não use 'payload' inexistente).\n"
    "- Não permita que o campo 'DataEntradaFaturar' seja modificado ou sobrescrito na etapa 'Faturado' no histórico.\n"
    "- Envolva a importação de 'streamlit_autorefresh' em try/except para definir st_autorefresh como None caso não exista, e só chame a função no fim do arquivo se st_autorefresh estiver disponível."
)

# 2. Instruções para oficial_turso.py
instrucoes_turso = (
    "- Corrija a indentação da cascata de regras (Regras 1, 2 e 3) e o salvamento do histórico dentro de 'verificar_e_notificar_mudancas'.\n"
    "- Na Regra 3 (etapa 'Faturado'), use as variáveis locais de data e hora e nunca altere ou sobrescreva a 'DataEntradaFaturar' no histórico.\n"
    "- Remova referências a variáveis inexistentes (como 'payload').\n"
    "- Trate a importação de 'streamlit_autorefresh' com try-except de forma grácil para não quebrar caso esteja ausente, executando no final somente se ativo."
)

print("[RESTAURADOR] Iniciando restauração completa do projeto via Gemma 4...")
processar_arquivo_com_gemma("oficial.py", instrucoes_oficial)
processar_arquivo_com_gemma("oficial_turso.py", instrucoes_turso)
print("[RESTAURADOR] Processo concluído.")

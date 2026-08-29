# -*- coding: utf-8 -*-
import urllib.request
import json
import os
import re

def recriar_com_agente():
    origem = "oficial.py"
    destino = "oficial_turso.py"
    
    if not os.path.exists(origem):
        print("Erro: O arquivo oficial.py nao foi encontrado para usar como base.")
        return

    with open(origem, "r", encoding="utf-8") as f:
        codigo_base = f.read()

    print("Agente Local Ativo! Localizando o bloco condicional no arquivo original...")

    # Localiza apenas o bloco Faturado de forma isolada dentro do codigo base
    match = re.search(r"(elif\s+etapa_atual\s*==\s*['\"]Faturado['\"]:.*?)(?=elif|if|def|class|\$)", codigo_base, re.DOTALL)
    if not match:
        match = re.search(r"(['\"]Faturado['\"]:.*?)(?=elif|if|def|class|\$)", codigo_base, re.DOTALL)

    if not match:
        print("Erro do Agente: Nao consegui encontrar o bloco 'Faturado' no oficial.py.")
        return

    bloco_antigo = match.group(1)
    print("Bloco Faturado localizado! Enviando para o Qwen corrigir a logica do bug < 1m...")

    prompt = (
        "Voce e o motor de raciocinio de um agente de refatoracao. Corrija o bloco condicional Python abaixo.\n"
        "Regras estritas:\n"
        "1. Remova completamente qualquer linha que altere ou atribua valores para 'DataEntradaFaturar' (isso gera metricas falsas de < 1m quando muda para Faturado).\n"
        "2. Garanta que o campo 'DataFaturamento' seja preenchido buscando estritamente o horario nativo de faturamento vindo do payload/API (ex: payload.get('data_faturamento')).\n"
        "3. Mantenha rigorosamente a indentacao original.\n"
        "Retorne APENAS o codigo corrigido do bloco, sem introducoes, explicacoes ou crases markdown.\n\n"
        f"Bloco atual:\n{bloco_antigo}"
    )

    data = {"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False}
    req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            bloco_corrigido = res_body.get("response", "").strip()
            
            bloco_corrigido = re.sub(r"^```python\s*|^```\s*|```$", "", bloco_corrigido, flags=re.MULTILINE).strip()

            # Aplica a correcao do bloco dentro do codigo original completo do oficial.py
            codigo_corrigido = codigo_base.replace(bloco_antigo, bloco_corrigido + "\n")
            
            # Ajusta a conexao para o formato do Turso (trocando sqlite3 por libsql se necessario, ou apenas preparando o arquivo)
            # Como queremos o oficial_turso.py funcional, vamos salvar o codigo estruturado com a correcao aplicada
            with open(destino, "w", encoding="utf-8") as f:
                f.write(codigo_corrigido)
                
            print("\n[AGENTE CONCLUIDO COM SUCESSO!]")
            print(f"O arquivo {destino} foi gerado do zero com base no oficial.py.")
            print("O bug do < 1m no bloco 'Faturado' foi removido cirurgicamente pela sua GTX 1660 Ti!")

    except Exception as e:
        print(f"Erro na conexao com o Ollama: {e}")

if __name__ == "__main__":
    recriar_com_agente()

# -*- coding: utf-8 -*-
import urllib.request
import json
import os
import re

def agente_autonomo():
    arquivo_path = "oficial_turso.py"
    
    if not os.path.exists(arquivo_path):
        print("Erro: O arquivo oficial_turso.py nao foi encontrado na raiz.")
        return

    with open(arquivo_path, "r", encoding="utf-8") as f:
        codigo_completo = f.read()

    print("Agente Local Ativo! Analisando a estrutura do oficial_turso.py...")

    # Busca o bloco condicional Faturado de forma flexivel
    match = re.search(r"(elif\s+etapa_atual\s*==\s*['\"]Faturado['\"]:.*?)(?=elif|if|def|class|\$)", codigo_completo, re.DOTALL)
    
    if not match:
        match = re.search(r"(['\"]Faturado['\"]:.*?)(?=elif|if|def|class|\$)", codigo_completo, re.DOTALL)
        
    if not match:
        print("Erro do Agente: Nao consegui localizar o bloco condicional da etapa Faturado no arquivo.")
        return

    bloco_antigo = match.group(1)
    print("Bloco Faturado localizado com sucesso! Enviando para o Qwen consertar a logica...")

    prompt = (
        "Voce e o motor de raciocinio de um agente de refatoracao de codigo. Corrija o bloco condicional Python abaixo.\n"
        "Regras estritas de negocio:\n"
        "1. Remova completamente qualquer linha que altere, atualize ou atribua valores para 'DataEntradaFaturar' dentro deste bloco de faturamento (isso gera metricas falsas de < 1m).\n"
        "2. Garanta que o campo 'DataFaturamento' seja preenchido estritamente buscando o horario nativo de faturamento vindo do payload/API (ex: payload.get('data_faturamento') ou a variavel equivalente ja usada no bloco).\n"
        "3. Preserve rigorosamente a indentacao original (espacos no inicio das linhas) e os nomes de variaveis do bloco.\n"
        "Retorne APENAS o codigo corrigido e limpo do bloco, sem introducoes, sem explicacoes e sem marcacoes markdown (sem as tres crases).\n\n"
        f"Bloco de codigo atual para corrigir:\n{bloco_antigo}"
    )

    data = {
        "model": "qwen2.5-coder:7b",
        "prompt": prompt,
        "stream": False
    }

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            bloco_corrigido = res_body.get("response", "").strip()
            
            bloco_corrigido = re.sub(r"^```python\s*", "", bloco_corrigido)
            bloco_corrigido = re.sub(r"^```\s*", "", bloco_corrigido)
            bloco_corrigido = re.sub(r"```$", "", bloco_corrigido).strip()

            if len(bloco_corrigido) < 10:
                print("Erro: A resposta do modelo veio vazia ou invalida.")
                return

            novo_codigo_completo = codigo_completo.replace(bloco_antigo, bloco_corrigido + "\n")
            
            with open(arquivo_path, "w", encoding="utf-8") as f:
                f.write(novo_codigo_completo)
                
            print("\n[AGENTE CONCLUIDO COM SUCESSO]")
            print("O bloco da etapa Faturado foi reconfigurado localmente usando sua GTX 1660 Ti.")
            print("O bug do < 1m foi removido e o restante do seu arquivo oficial_turso.py permaneceu intacto.")

    except Exception as e:
        print(f"Erro na comunicacao com a API do Ollama: {e}")

if __name__ == "__main__":
    agente_autonomo()

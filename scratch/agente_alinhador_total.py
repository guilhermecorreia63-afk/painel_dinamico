# -*- coding: utf-8 -*-
import urllib.request
import json
import re

with open("oficial_turso.py", "r", encoding="utf-8") as f:
    codigo_completo = f.read()

with open("scratch/bloco_quebrado.txt", "r", encoding="utf-8") as f:
    bloco_quebrado = f.read()

prompt = (
    "Você é um agente especialista em Python. Corrija rigorosamente a indentação de todas as linhas do bloco de código abaixo.\n"
    "Certifique-se de que cada 'if', 'elif', 'else' e atribuições em DataFrames (como df_historico.loc) estejam perfeitamente alinhados com seus blocos correspondentes.\n"
    "Lembre-se da regra de negócio: no bloco 'Faturado', não deve haver nenhuma atribuição para 'DataEntradaFaturar'.\n"
    "Me retorne APENAS o código corrigido e identado, sem introduções, explicações ou crases de marcação markdown.\n\n"
    f"Bloco para alinhar:\n{bloco_quebrado}"
)

data = {"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False}
req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as response:
        res_body = json.loads(response.read().decode("utf-8"))
        bloco_corrigido = res_body.get("response", "").strip()
        bloco_corrigido = re.sub(r"^```python\s*|^```\s*|```$", "", bloco_corrigido, flags=re.MULTILINE).strip()
        
        # Substitui o bloco desalinhado pelo bloco com a cascata perfeita de espaços
        codigo_final = codigo_completo.replace(bloco_quebrado, bloco_corrigido + "\n")
        
        with open("oficial_turso.py", "w", encoding="utf-8") as f:
            f.write(codigo_final)
        print("[AGENTE] Cascata de indentação reestruturada com sucesso pelo Qwen!")
except Exception as e:
    print(f"Erro: {e}")

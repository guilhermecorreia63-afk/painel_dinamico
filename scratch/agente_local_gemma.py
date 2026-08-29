# -*- coding: utf-8 -*-
import urllib.request
import json

# Caminhos dos arquivos
alvo_file = "oficial_turso.py"

with open(alvo_file, "r", encoding="utf-8") as f:
    codigo_completo = f.read()

prompt = (
    "Você é um assistente de programação Python local. Faça as seguintes alterações no código fornecido abaixo:\n"
    "1. Na importação de 'streamlit_autorefresh' (linha 9), envolva o import em um bloco try-except ImportError para que se o módulo não estiver instalado, st_autorefresh seja definido como None.\n"
    "2. Na chamada de 'st_autorefresh(interval=1000, key=\"visual_refresher\")' (linha 773), verifique se st_autorefresh não é None antes de chamá-lo. Caso seja None, execute st.caption('Auto-refresh desativado (pacote ausente).') em vez disso.\n"
    "Me retorne APENAS o código Python completo corrigido, sem qualquer introdução, explicação ou marcação markdown (não coloque crases ``` no início ou fim).\n\n"
    f"Código para modificar:\n{codigo_completo}"
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

print("[AGENTE LOCAL] Enviando código do oficial_turso.py para o Gemma 4 no Ollama local...")
try:
    with urllib.request.urlopen(req) as response:
        res_body = json.loads(response.read().decode("utf-8"))
        codigo_corrigido = res_body.get("response", "").strip()
        
        # Remove eventuais marcações markdown se o modelo insistir nelas
        if codigo_corrigido.startswith("```python"):
            codigo_corrigido = codigo_corrigido[9:]
        if codigo_corrigido.startswith("```"):
            codigo_corrigido = codigo_corrigido[3:]
        if codigo_corrigido.endswith("```"):
            codigo_corrigido = codigo_corrigido[:-3]
        
        codigo_corrigido = codigo_corrigido.strip()
        
        if len(codigo_corrigido) > 100:  # Garante que não salvou resposta em branco ou erro simples
            with open(alvo_file, "w", encoding="utf-8") as f:
                f.write(codigo_corrigido + "\n")
            print("[AGENTE LOCAL] Arquivo oficial_turso.py atualizado localmente com sucesso pelo Gemma 4!")
        else:
            print("[AGENTE LOCAL] Erro: A resposta retornada pelo modelo local parece muito curta ou inválida.")
            print(f"Resposta do modelo:\n{codigo_corrigido}")
except Exception as e:
    print(f"[AGENTE LOCAL] Erro ao conectar com o Ollama local: {e}")

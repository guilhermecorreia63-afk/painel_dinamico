import json
import os
import re
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "gemma4:e4b"

files_to_analyze = [
    {"path": "consulta_etapas.py", "type": "python"},
    {"path": "processar_pedidos.py", "type": "python"},
    {"path": "teste_mapeamento.py", "type": "python"},
    {"path": "app.py", "type": "python"},
    {"path": "dashboard.py", "type": "python"},
    {"path": "historico.py", "type": "python"},
    {"path": "historico_turso.py", "type": "python"},
    {"path": "oficial.py", "type": "python"},
    {"path": "oficial_turso.py", "type": "python"},
    {"path": "dados_pedidos.json", "type": "json_sample"},
]

def query_ollama(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Erro ao chamar Ollama: {e}"

def main():
    print("Iniciando análise do projeto através do Ollama...")
    results = {}
    
    for item in files_to_analyze:
        path = item["path"]
        ftype = item["type"]
        
        if not os.path.exists(path):
            results[path] = "Arquivo não existe no diretório atual."
            continue
            
        print(f"Analisando arquivo: {path}...")
        
        if ftype == "python":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # If the file is extremely long, we take the top/important parts (classes and function signatures)
            # or send it in chunks. But for these sizes, let's send the content, limiting to first 250 lines if it's too long.
            lines = content.split("\n")
            if len(lines) > 250:
                print(f" -> Arquivo longo ({len(lines)} linhas). Resumindo estrutura.")
                # Extract imports, class definitions, function definitions
                structure = []
                for line in lines:
                    if line.startswith("import ") or line.startswith("from ") or line.startswith("def ") or line.startswith("class "):
                        structure.append(line)
                code_summary = "\n".join(structure)
                prompt = (
                    f"Você é um engenheiro de software experiente. Analise a seguinte estrutura do arquivo Python '{path}':\n\n"
                    f"```python\n{code_summary}\n```\n\n"
                    f"Por favor, explique o propósito principal deste arquivo no projeto e resuma brevemente o que suas principais funções/classes fazem. Escreva em Português do Brasil de forma concisa."
                )
            else:
                prompt = (
                    f"Você é um engenheiro de software experiente. Analise o seguinte código do arquivo Python '{path}':\n\n"
                    f"```python\n{content}\n```\n\n"
                    f"Por favor, explique o propósito principal deste arquivo no projeto e o que suas principais funções/classes fazem. Escreva em Português do Brasil de forma concisa."
                )
                
            results[path] = query_ollama(prompt)
            
        elif ftype == "json_sample":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                # Load first few characters or read sample structure
                try:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        sample = data[0]
                    elif isinstance(data, dict):
                        sample = {k: data[k] for k in list(data.keys())[:2]}
                    else:
                        sample = str(data)[:1000]
                    sample_str = json.dumps(sample, indent=2, ensure_ascii=False)[:3000]
                except Exception:
                    f.seek(0)
                    sample_str = f.read(1000)
                    
                prompt = (
                    f"Analise esta amostra do arquivo de dados JSON '{path}':\n\n"
                    f"```json\n{sample_str}\n```\n\n"
                    f"Explique o propósito geral deste arquivo de dados no sistema e qual é a estrutura dos dados representados. Escreva em Português do Brasil de forma concisa."
                )
                results[path] = query_ollama(prompt)
                
    # Save the analysis summary
    analysis_file = "scratch/resumo_analise.json"
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print(f"\nAnálise concluída com sucesso! Resultados salvos em '{analysis_file}'.")

if __name__ == "__main__":
    main()

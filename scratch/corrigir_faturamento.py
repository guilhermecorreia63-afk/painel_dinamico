import urllib.request
import json
import os

def corrigir_codigo():
    arquivo_path = "oficial_turso.py"
    
    if not os.path.exists(arquivo_path):
        print(f"Erro: O arquivo {arquivo_path} nao foi encontrado!")
        return

    # 1. Ler o arquivo de codigo real do seu projeto
    with open(arquivo_path, "r", encoding="utf-8") as f:
        codigo_original = f.read()

    print("Enviando trecho para o Qwen 2.5 Coder local processar na GTX 1660 Ti...")

    # 2. Prompt estruturado para a API local do Ollama
    prompt = (
        "Você é um agente especialista em refatoração de código Python. Analise a lógica de tratamento de eventos logísticos abaixo.\n"
        "Localize o bloco 'elif etapa_atual == \"Faturado\":' (provavelmente localizado entre as linhas 490 e 535) e faça exatamente as duas seguintes correções:\n"
        "1. Remova qualquer linha de dentro do bloco 'Faturado' que atualize, altere ou atribua valores à coluna/campo 'DataEntradaFaturar' (isso está gerando métricas erradas de < 1m no banco).\n"
        "2. Garanta que o campo 'DataFaturamento' puxe o valor do horário real de faturamento bruto retornado pela API/Payload (ex: payload.get('data_faturamento')), sem fallbacks genéricos de data de alteração de etapa.\n"
        "Mantenha rigorosamente intactas todas as outras estruturas, ifs, elifs, nomes de variáveis e identações.\n"
        "Me retorne APENAS o código completo do arquivo final atualizado, sem nenhuma introdução, explicação ou blocos de marcação de texto do Markdown (sem as três crases).\n\n"
        f"Aqui está o código completo do arquivo:\n\n{codigo_original}"
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
            novo_codigo = res_body.get("response", "").strip()
            
            # Limpar marcadores markdown residuais se a IA insistir em colocar
            if novo_codigo.startswith("```python"):
                novo_codigo = novo_codigo[9:]
            if novo_codigo.startswith("```"):
                novo_codigo = novo_codigo[3:]
            if novo_codigo.endswith("```"):
                novo_codigo = novo_codigo[:-3]
            novo_codigo = novo_codigo.strip()

            if len(novo_codigo) < 100:
                print("Erro: Resposta da IA veio incompleta ou vazia. Nenhuma alteracao foi feita.")
                return

            # 3. Salvar o arquivo atualizado substituindo o antigo com seguranca
            with open(arquivo_path, "w", encoding="utf-8") as f:
                f.write(novo_codigo)
            
            print(f"Sucesso! O arquivo {arquivo_path} foi atualizado de forma cirurgica pelo agente local.")

    except Exception as e:
        print(f"Ocorreu um erro na comunicacao com o Ollama: {e}")

if __name__ == "__main__":
    corrigir_codigo()

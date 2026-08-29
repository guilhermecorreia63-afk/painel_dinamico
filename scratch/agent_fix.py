import re

# Lê o conteúdo do arquivo 'oficial_turso.py'
with open('oficial_turso.py', 'r', encoding='utf-8') as file:
    content = file.read()

# Define o padrão regex para encontrar a seção 'elif etapa_atual == \'Fatur[7D[K
\'Faturado\':'
pattern = r'elif etapa_atual == \'Faturado\':\s*([\s\S]*?)\s*else:'

# Substitui o bloco encontrado para remover a atribuição de 'DataEntradaFat[15D[K
'DataEntradaFaturar' e ajustar 'DataFaturamento'
new_content = re.sub(pattern, r'elif etapa_atual == \'Faturado\':\n    Data[4D[K
DataFaturamento = api_faturamento.get_faturamento_datetime()\nelse:', conte[5D[K
content, flags=re.DOTALL)

# Salva as alterações de volta no arquivo 'oficial_turso.py'
with open('oficial_turso.py', 'w', encoding='utf-8') as file:
    file.write(new_content)


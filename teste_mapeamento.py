# MAPEAMENTO DE DEPARTAMENTOS
MAPEAMENTO_DEPTO = {
    "1807684664": "Comercial",
    "1807684776": "Ecommerce"
}

def processar_teste(codigo_do_pedido):
    # Simula o código de departamento que recebemos da API
    cod_encontrado = str(codigo_do_pedido)
    
    # Busca o nome no mapeamento
    nome_depto = MAPEAMENTO_DEPTO.get(cod_encontrado, "Departamento Não Mapeado")
    
    print(f"Código recebido da API: {cod_encontrado}")
    print(f"Departamento identificado: {nome_depto}")
    print("-" * 30)

# Testando os dois casos
if __name__ == "__main__":
    processar_teste("1807684664")
    processar_teste("1807684776")
    processar_teste("0000000000") # Teste de um código que não existe
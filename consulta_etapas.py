import os
import requests
import json
from dotenv import load_dotenv

# Carrega as variáveis
load_dotenv()
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")

def buscar_detalhes_em_lote():
    url = "https://app.omie.com.br/api/v1/produtos/pedido/"
    payload = {
        "call": "ListarPedidos",
        "app_key": APP_KEY,
        "app_secret": APP_SECRET,
        "param": [{
            "pagina": 1,
            "registros_por_pagina": 20,
            "apenas_importado_api": "N"
        }]
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

if __name__ == "__main__":
    # Agora chamamos o nome correto da função que criamos acima
    resultado = buscar_detalhes_em_lote()
    
    print("Resultado da API:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
import json
import os
import requests
import pandas as pd
from pathlib import Path
import tomllib

def carregar_secrets():
    caminho = Path(".streamlit/secrets.toml")
    if caminho.exists():
        with open(caminho, "rb") as f:
            return tomllib.load(f)
    return {}

secrets = carregar_secrets()
APP_KEY = secrets.get("APP_KEY")
APP_SECRET = secrets.get("APP_SECRET")

url = "https://app.omie.com.br/api/v1/produtos/pedido/"
payload = {
    "call": "ConsultarPedido",
    "app_key": APP_KEY,
    "app_secret": APP_SECRET,
    "param": [{
        "numero_pedido": "16618"
    }]
}

response = requests.post(url, json=payload)
res = response.json()
print("ConsultarPedido 16618 keys:", res.keys())
print("etapas_alteracoes in res:", "etapas_alteracoes" in res)
print("etapas_alteracoes value:", res.get("etapas_alteracoes"))
print("cabecalho keys:", res.get("cabecalho", {}).keys())
print("infoCadastro keys:", res.get("infoCadastro", {}).keys())

# Print the whole response to a file so we can read it if needed
with open("scratch/consultar_16618.json", "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)

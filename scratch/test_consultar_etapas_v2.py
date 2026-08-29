import json
with open("scratch/consultar_16618.json", "r", encoding="utf-8") as f:
    data = json.load(f)

order = data.get("pedido_venda_produto", {})
print("Order type:", type(order))
if isinstance(order, dict):
    print("Order keys:", order.keys())
    print("etapas_alteracoes in order:", "etapas_alteracoes" in order)
    print("etapas_alteracoes value:", order.get("etapas_alteracoes"))
elif isinstance(order, list) and len(order) > 0:
    print("First item keys:", order[0].keys())
    print("etapas_alteracoes in first item:", "etapas_alteracoes" in order[0])
    print("etapas_alteracoes value:", order[0].get("etapas_alteracoes"))

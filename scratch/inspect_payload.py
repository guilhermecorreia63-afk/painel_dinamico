import json

with open("dados_pedidos.json", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

if lines[0].strip().startswith("Resultado da API:"):
    json_str = "".join(lines[1:])
else:
    json_str = "".join(lines)

data = json.loads(json_str)
orders = data.get("pedido_venda_produto", [])
print(f"Total orders: {len(orders)}")
if orders:
    first_order = orders[0]
    print("Keys of first order:", first_order.keys())
    print("Cabecalho keys:", first_order.get("cabecalho", {}).keys())
    print("infoCadastro keys:", first_order.get("infoCadastro", {}).keys())
    
    # print any order with etapas_alteracoes if we can find it
    for i, p in enumerate(orders):
        if "etapas_alteracoes" in p:
            print(f"Order index {i} has etapas_alteracoes: {p['etapas_alteracoes']}")
        # check if it's inside cabecalho or somewhere else
        for k, v in p.items():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "etapa" in str(v[0]).lower():
                print(f"Found something in key '{k}': {v}")

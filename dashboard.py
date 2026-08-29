import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import tomllib
from datetime import datetime, timedelta
import time

if 'ultima_atualizacao' not in st.session_state:
    st.session_state.ultima_atualizacao = datetime.now()
# --- CONTROLE DE ESTADO PARA NOTIFICAÇÕES ---
if 'pedidos_antigos' not in st.session_state:
    st.session_state.pedidos_antigos = pd.DataFrame()
# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Painel de Pedidos Omie")

# --- CARREGAMENTO DE SECRETS ---
def carregar_secrets():
    caminho = Path(".streamlit/secrets.toml")
    if caminho.exists():
        with open(caminho, "rb") as f:
            return tomllib.load(f)
    return st.secrets

# --- FUNÇÕES DE APOIO ---
@st.cache_data(ttl=600)
def buscar_pedidos():
    secrets = carregar_secrets()
    url = "https://app.omie.com.br/api/v1/produtos/pedido/"
    data_alvo = (datetime.now() - timedelta(days=5)).strftime("%d/%m/%Y")
    
    todos_pedidos = []
    for pagina in range(1, 4): 
        payload = {
            "call": "ListarPedidos",
            "app_key": secrets["APP_KEY"],
            "app_secret": secrets["APP_SECRET"],
            "param": [{"pagina": pagina, "registros_por_pagina": 300, "apenas_importado_api": "N", "filtrar_por_data_de": data_alvo}]
        }
        try:
            res = requests.post(url, json=payload, timeout=30).json()
            pedidos_pagina = res.get("pedido_venda_produto", [])
            if not pedidos_pagina: break
            todos_pedidos.extend(pedidos_pagina)
        except Exception: continue
    return todos_pedidos

def limpar_observacao(obs):
    if not obs: return "-"
    obs_limpa = str(obs).replace("&amp;", "&")
    obs_str = obs_limpa.lower()
    if obs_str.strip() == "" or "faturar" in obs_str or "faturamento" in obs_str or "prestação de contas" in obs_str:
        return "-"
    if "j&t" in obs_str: return "J&T"
    elif "magazine luiza" in obs_str: return "Magazine Luiza"
    elif "mini envios" in obs_str: return "Mini Envios"
    elif "sedex" in obs_str: return "Sedex"
    elif "retirada" in obs_str or "retirar" in obs_str or "expedição" in obs_str or "estoque" in obs_str: return "Retirada Estoque"
    elif "total express" in obs_str: return "Total"
    elif "pac" in obs_str: return "PAC"
    elif "souza" in obs_str or "sousa" in obs_str: return "Souza"
    elif "entrega econômica" in obs_str:
        if "25 dias" in obs_str: return "Impresso"
        elif "3 dias" in obs_str: return "Souza"
        return "Impresso"
    return obs_limpa.strip()

# --- MAPEAMENTO E PROCESSAMENTO ---
MAPEAMENTO_DEPTO = {"1807684664": "Comercial", "1807684776": "Ecommerce"}

def processar_pedidos(lista_bruta):
    etapas_map = {"80": "Separar Estoque", "60": "Faturado", "20": "Em Processo", "50": "Faturar"}
    dados_processados = []
    for p in lista_bruta:
        cab = p.get("cabecalho", {})
        obs_obj = p.get("observacoes", {})
        deps = p.get("departamentos", [])
        nome_depto = "Sem Departamento"
        if isinstance(deps, list):
            for dep in deps:
                codigo = str(dep.get("cCodDepto", ""))
                if codigo in MAPEAMENTO_DEPTO:
                    nome_depto = MAPEAMENTO_DEPTO[codigo]
                    break
        num_pedido = cab.get("numero_pedido")
        dados_processados.append({
            "Pedido": int(num_pedido) if num_pedido and str(num_pedido).isdigit() else 0,
            "Etapa": etapas_map.get(str(cab.get("etapa")), str(cab.get("etapa"))),
            "Cód. Cliente": cab.get("codigo_cliente"),
            "Departamento": nome_depto,
            "Observação": limpar_observacao(obs_obj.get("obs_venda"))
        })
    return pd.DataFrame(dados_processados).sort_values(by="Pedido", ascending=False)

# --- INTERFACE ---
st.title("📊 Painel Dinâmico de Pedidos")

# --- LÓGICA DE SINCRONIZAÇÃO (Na Sidebar) ---
# Definimos o intervalo (ex: 600 segundos = 10 minutos)
INTERVALO_SEGUNDOS = 600 

agora = datetime.now()
segundos_desde_ultima = (agora - st.session_state.ultima_atualizacao).total_seconds()
tempo_restante = max(0, int(INTERVALO_SEGUNDOS - segundos_desde_ultima))

# Se o tempo acabou, força a atualização
if tempo_restante <= 0:
    st.cache_data.clear()
    st.session_state.ultima_atualizacao = datetime.now()
    st.rerun()

st.sidebar.header("Controle de Sincronização")
if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.session_state.ultima_atualizacao = datetime.now()
    st.rerun()

# Exibição (O que você queria ver)
st.sidebar.metric("Próxima atualização em", f"{tempo_restante // 60:02d}:{tempo_restante % 60:02d}")
st.sidebar.caption(f"Última: {st.session_state.ultima_atualizacao.strftime('%H:%M:%S')}")

with st.spinner("Carregando pedidos do Omie..."):
    dados = buscar_pedidos()
    if dados:
        df = processar_pedidos(dados)
        st.sidebar.header("Filtros")
        opcoes_depto = ["Todos"] + sorted(df["Departamento"].unique().tolist())
        filtro_depto = st.sidebar.selectbox("Filtrar por Departamento", options=opcoes_depto)
        df_exibicao = df[df["Departamento"] == filtro_depto] if filtro_depto != "Todos" else df
        filtro_etapa = st.sidebar.multiselect("Filtrar por Etapa", options=df_exibicao["Etapa"].unique())
        if filtro_etapa: df_exibicao = df_exibicao[df_exibicao["Etapa"].isin(filtro_etapa)]

        # --- ESTRUTURA DE COLUNAS ---
        col_principal, col_lateral = st.columns([3, 1])

        # --- ESTRUTURA DE COLUNAS ---
        col_principal, col_lateral = st.columns([3, 1])

        with col_principal: 
            # --- ESTRUTURA TRAVADA E ALINHADA ---
            contagem_etapas = df_exibicao["Etapa"].value_counts()
            etapas_config = [
                {"nome": "EM PROCESSO", "cor": "#FFC107", "desc": "pedidos aguardando"},
                {"nome": "SEPARAR ESTOQUE", "cor": "#9C27B0", "desc": "pendentes para picking"},
                {"nome": "FATURAR", "cor": "#FF9800", "desc": "caixas no packing"},
                {"nome": "FATURADO", "cor": "#4CAF50", "desc": "concluídos no período"}
            ]
            
            cols = st.columns(4)

            for i, col in enumerate(cols):
                config = etapas_config[i]
                nome_chave = config["nome"].title() 
                qtd = contagem_etapas.get(nome_chave, 0)
                
                with col.container(border=True, height=200):
                    st.markdown(f"<div style='border-top: 5px solid {config['cor']}; margin: -15px -15px 10px -15px;'></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center; font-size: 0.75rem; font-weight: bold; color: #555;'>{config['nome']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center; font-size: 2.5rem; font-weight: bold;'>{qtd}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center; font-size: 0.7rem; color: #888;'>{config['desc']}</div>", unsafe_allow_html=True)

            st.divider()
        
            # Tabela
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True, column_config={
                "Pedido": st.column_config.NumberColumn("Pedido", format="%d"),
                "Etapa": st.column_config.TextColumn("Etapa Atual"),
                "Cód. Cliente": st.column_config.NumberColumn("Cód. Cliente", format="%d"),
                "Departamento": st.column_config.TextColumn("Departamento"),
                "Observação": st.column_config.TextColumn("Observações do Pedido")
            })
            st.caption(f"Total de pedidos: {len(df_exibicao)}")

        # --- LÓGICA DE NOTIFICAÇÃO (DISPARADA POR CLIQUE) ---
        with col_lateral:
            st.subheader("🔄 Alterações")
            
            # Se ainda não temos dados antigos, inicializamos
            if st.session_state.pedidos_antigos.empty:
                st.info("Monitoramento iniciado. Clique em 'Sincronizar Agora' para verificar mudanças.")
                st.session_state.pedidos_antigos = df.copy()
            else:
                # Comparamos o DF atual com o antigo
                mapa_antigo = st.session_state.pedidos_antigos.set_index('Pedido')['Etapa'].to_dict()
                mudou = False
                
                for _, row in df.iterrows():
                    pedido_id = row['Pedido']
                    etapa_atual = row['Etapa']
                    
                    if pedido_id in mapa_antigo:
                        if mapa_antigo[pedido_id] != etapa_atual:
                            st.info(f"Pedido {pedido_id}: {mapa_antigo[pedido_id]} → {etapa_atual}")
                            mudou = True
                
                # Novos
                novos = df[~df['Pedido'].isin(st.session_state.pedidos_antigos['Pedido'])]
                if not novos.empty:
                    st.error(f"🚨 {len(novos)} novo(s) pedido(s)!")
                    mudou = True
                
                if not mudou:
                    st.success("Nenhuma alteração recente.")

                # BOTÃO PARA ATUALIZAR O ESTADO
                if st.button("💾 Salvar estado atual"):
                    st.session_state.pedidos_antigos = df.copy()
                    st.rerun()

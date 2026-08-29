import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import tomllib
from datetime import datetime, timedelta
import plotly.express as px

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'ultima_atualizacao' not in st.session_state:
    st.session_state.ultima_atualizacao = datetime.now()
if 'pedidos_antigos' not in st.session_state:
    st.session_state.pedidos_antigos = pd.DataFrame()
if 'notificacoes_toast' not in st.session_state:
    st.session_state.notificacoes_toast = []

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Painel de Pedidos Omie")

# --- CSS PARA CORRIGIR CORTE DO TÍTULO E COMPACTAR ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 0rem !important;
    }
    div[data-baseweb="select"] {
        margin-bottom: -10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES E CONFIGURAÇÕES GLOBAIS ---
INTERVALO_SEGUNDOS = 600  # 10 minutos
LIMITE_PESO_KG = 25
LIMITE_VALOR_REAIS = 5000

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

MAPEAMENTO_DEPTO = {"1807684664": "Comercial", "1807684776": "Ecommerce"}

def processar_pedidos(lista_bruta):
    etapas_map = {"80": "Separar Estoque", "60": "Faturado", "20": "Em Processo", "50": "Faturar"}
    dados_processados = []
    for p in lista_bruta:
        cabecalho = p.get("cabecalho", {})
        observacoes = p.get("observacoes", {})
        deps = p.get("departamentos", []) or []
        total_pedido = p.get("total_pedido", {})
        frete = p.get("frete", {})
        nome_depto = "Não Identificado"
        if isinstance(deps, list):
            for dep in deps:
                codigo = str(dep.get("cCodDepto", ""))
                if codigo in MAPEAMENTO_DEPTO:
                    nome_depto = MAPEAMENTO_DEPTO[codigo]
                    break
        num_pedido = cabecalho.get("numero_pedido")
        
        dados_processados.append({
            "Pedido": int(num_pedido) if num_pedido and str(num_pedido).isdigit() else 0,
            "Etapa": etapas_map.get(str(cabecalho.get("etapa")), str(cabecalho.get("etapa"))),
            "Cód. Cliente": cabecalho.get("codigo_cliente"),
            "Departamento": nome_depto,
            "Observação": limpar_observacao(observacoes.get("obs_venda")),
            "Valor Total": total_pedido.get("valor_total_pedido", 0.0),
            "Peso Bruto (kg)": frete.get("peso_bruto", 0.0)
        })
    return pd.DataFrame(dados_processados).sort_values(by="Pedido", ascending=False)

# --- CONTROLE DE ATUALIZAÇÃO AUTOMÁTICA ---
agora = datetime.now()
segundos_desde_ultima = (agora - st.session_state.ultima_atualizacao).total_seconds()
tempo_restante = max(0, int(INTERVALO_SEGUNDOS - segundos_desde_ultima))

if tempo_restante <= 0:
    st.cache_data.clear()
    st.session_state.ultima_atualizacao = datetime.now()
    st.rerun()

# --- SIDEBAR: CONTROLES E FILTROS ---
st.sidebar.header("Controle de Sincronização")
if st.sidebar.button("🔄 Sincronizar Agora", use_container_width=True):
    st.cache_data.clear()
    st.session_state.ultima_atualizacao = datetime.now()
    st.rerun()

st.sidebar.metric("Próxima atualização em", f"{tempo_restante // 60:02d}:{tempo_restante % 60:02d}")
st.sidebar.caption(f"Última: {st.session_state.ultima_atualizacao.strftime('%H:%M:%S')}")

with st.spinner("Carregando pedidos do Omie..."):
    dados = buscar_pedidos()

if dados:
    df = processar_pedidos(dados)

    # --- VERIFICAÇÃO DE PEDIDOS CRÍTICOS EM SEPARAR ESTOQUE (PARA INCLUIR NAS NOTIFICAÇÕES) ---
    df_separando = df[df["Etapa"] == "Separar Estoque"]
    pedidos_grandes_valor = df_separando[df_separando["Valor Total"] > LIMITE_VALOR_REAIS]
    pedidos_pesados = df_separando[df_separando["Peso Bruto (kg)"] > LIMITE_PESO_KG]

    # --- PROCESSAMENTO DE NOTIFICAÇÕES E ALERTAS ---
    if st.session_state.pedidos_antigos.empty:
        st.session_state.pedidos_antigos = df.copy()
    else:
        mapa_antigo = st.session_state.pedidos_antigos.set_index('Pedido')[['Etapa', 'Departamento']].to_dict('index')
        
        for _, row in df.iterrows():
            pedido_id = row['Pedido']
            etapa_atual = row['Etapa']
            if pedido_id in mapa_antigo and mapa_antigo[pedido_id]['Etapa'] != etapa_atual:
                msg = f"Pedido **{pedido_id}** ({mapa_antigo[pedido_id]['Departamento']}): {mapa_antigo[pedido_id]['Etapa']} → **{etapa_atual}**"
                if msg not in st.session_state.notificacoes_toast:
                    st.session_state.notificacoes_toast.append(msg)
        
        novos = df[~df['Pedido'].isin(st.session_state.pedidos_antigos['Pedido'])]
        if not novos.empty:
            msg_novo = f"🚨 {len(novos)} novo(s) pedido(s) lançado(s)!"
            if msg_novo not in st.session_state.notificacoes_toast:
                st.session_state.notificacoes_toast.append(msg_novo)

    st.sidebar.divider()
    st.sidebar.header("Filtros")
    opcoes_depto = ["Todos"] + sorted(df["Departamento"].unique().tolist())
    filtro_depto = st.sidebar.selectbox("Filtrar por Departamento", options=opcoes_depto)
    df_exibicao = df[df["Departamento"] == filtro_depto] if filtro_depto != "Todos" else df
    filtro_etapa = st.sidebar.multiselect("Filtrar por Etapa", options=df_exibicao["Etapa"].unique())
    if filtro_etapa: 
        df_exibicao = df_exibicao[df_exibicao["Etapa"].isin(filtro_etapa)]

    # --- TOPO: TÍTULO COM ESPAÇAMENTO CORRETO ---
    st.markdown("## 📊 Painel Dinâmico")
    st.write("")

    # --- ESTRUTURA DE COLUNAS (PRINCIPAL + LATERAL) ---
    col_principal, col_lateral = st.columns([3, 1])

    with col_principal: 
        # --- CARDS DE STATUS SUPERIORES ---
        contagem_etapas = df_exibicao["Etapa"].value_counts()
        etapas_config = [
            {"nome": "EM PROCESSO", "cor": "#FFC107", "desc": "pedidos aguardando"},
            {"nome": "SEPARAR ESTOQUE", "cor": "#9C27B0", "desc": "pendentes para separação"},
            {"nome": "FATURAR", "cor": "#FF9800", "desc": "caixas na embalagem"},
            {"nome": "FATURADO", "cor": "#4CAF50", "desc": "concluídos no período"}
        ]
        
        cols = st.columns(4)
        for i, col in enumerate(cols):
            config = etapas_config[i]
            nome_chave = config["nome"].title() 
            qtd = contagem_etapas.get(nome_chave, 0)
            
            with col.container(border=True, height=150):
                st.markdown(f"<div style='border-top: 4px solid {config['cor']}; margin: -15px -15px 8px -15px;'></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 0.7rem; font-weight: bold; color: #555;'>{config['nome']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 2rem; font-weight: bold;'>{qtd}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 0.65rem; color: #888;'>{config['desc']}</div>", unsafe_allow_html=True)

    with col_lateral:
        # --- NOTIFICAÇÕES E ALERTAS CRÍTICOS UNIFICADOS ---
        st.subheader("🔄 Notificações & Alertas")
        with st.container(border=True):
            tem_conteudo = False

            # 1. Alertas Críticos em Vermelho (Pedidos > 25kg ou > R$ 5mil em Separar Estoque)
            if not pedidos_grandes_valor.empty or not pedidos_pesados.empty:
                tem_conteudo = True
                for _, row in pedidos_grandes_valor.iterrows():
                    st.error(f"💰 **VALOR ALTO:** Pedido **{row['Pedido']}** - R$ {row['Valor Total']:.2f} (Separando)")
                for _, row in pedidos_pesados.iterrows():
                    st.error(f"⚖️ **PESO ELEVADO:** Pedido **{row['Pedido']}** - {row['Peso Bruto (kg)']:.2f} kg (Separando)")

            # 2. Notificações normais com botão 'X'
            if st.session_state.notificacoes_toast:
                tem_conteudo = True
                for idx, notif in enumerate(st.session_state.notificacoes_toast):
                    c_notif, c_btn = st.columns([5, 1])
                    with c_notif:
                        st.info(notif)
                    with c_btn:
                        if st.button("❌", key=f"del_notif_{idx}", help="Dispensar notificação"):
                            st.session_state.notificacoes_toast.pop(idx)
                            st.rerun()

            if not tem_conteudo:
                st.success("Nenhuma alteração ou alerta pendente.")
            elif st.session_state.notificacoes_toast:
                if st.button("Limpar Notificações", use_container_width=True):
                    st.session_state.notificacoes_toast = []
                    st.session_state.pedidos_antigos = df.copy()
                    st.rerun()

    # ==========================================
    # SEÇÃO INFERIOR: COLETAS VIVAS & PICKING POR DEPTO LADO A LADO
    # ==========================================
    st.divider()
    col_inf_1, col_inf_2 = st.columns(2)

    with col_inf_1:
        st.subheader("🕒 Painel de Coletas (Tempo Real)")
        with st.container(border=True):
            hora_atual = datetime.now().time()
            
            t_800 = datetime.strptime("08:00", "%H:%M").time()
            t_1030 = datetime.strptime("10:30", "%H:%M").time()
            t_1400 = datetime.strptime("14:00", "%H:%M").time()
            t_1630 = datetime.strptime("16:30", "%H:%M").time()
            
            # Lógica exata baseada nos horários solicitados
            if t_800 <= hora_atual <= t_1030:
                st.success("🟢 **HORÁRIO DOS CORREIOS (08:00 - 10:30):** Preferência ativa para envios via Correios.")
            elif t_1030 < hora_atual < t_1400:
                st.info("⏳ **HORÁRIO J&T & TOTAL EXPRESS (10:30 - 14:00):** Preferência ativa para J&T e Total Express.")
            elif t_1400 <= hora_atual <= t_1630:
                st.error("🚨 **HORÁRIO SOUZA - FORTALEZA (14:00 - 16:30):** Prioridade máxima para pedidos Souza.")
            else:
                st.warning("🌙 **PÓS-16:30 (RETORNO LIVRE):** Retorno para J&T, Total ou Correios de acordo com a demanda.")

            st.caption("Faixas ativas: 08:00-10:30 (Correios) | 10:30-14:00 (J&T/Total) | 14:00-16:30 (Souza) | Após 16:30 (Demanda livre).")

    with col_inf_2:
        st.subheader("📊 Separação por Depto (Separar ou Faturar)")
        with st.container(border=True):
            import plotly.express as px
            try:
                # Atualizado para buscar pedidos que estão em Separar Estoque ou Faturar
                df_picking_filtro = df[df["Etapa"].isin(["Separar Estoque", "Faturar"])]
                if not df_picking_filtro.empty:
                    contagem_picking = df_picking_filtro["Departamento"].value_counts().reset_index()
                    contagem_picking.columns = ["Departamento", "Contagem"]
                    fig_picking = px.pie(contagem_picking, names="Departamento", values="Contagem", hole=0.4)
                    fig_picking.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig_picking, use_container_width=True)
                else:
                    st.info("Nenhum pedido em 'Separar Estoque' ou 'Faturar' no momento.")
            except ImportError:
                st.warning("Instale a biblioteca `plotly` para visualizar os gráficos.")

else:
    st.warning("Não foi possível carregar os dados dos pedidos.")
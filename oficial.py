import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import tomllib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from historico import renderizar_aba_historico
from streamlit_autorefresh import st_autorefresh
import numpy as np

BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")

def agora_brasilia():
    """Retorna o datetime atual no fuso de Brasília."""
    return datetime.now(BRASILIA_TZ).replace(tzinfo=None)

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'ultima_atualizacao' not in st.session_state:
    st.session_state.ultima_atualizacao = agora_brasilia()

if 'pedidos_antigos' not in st.session_state:
    st.session_state.pedidos_antigos = pd.DataFrame()
if 'last_daily_snapshot_date' not in st.session_state:
    st.session_state.last_daily_snapshot_date = datetime.min.date()
if 'df_pedidos_cache' not in st.session_state:
    st.session_state.df_pedidos_cache = pd.DataFrame()
if 'notificacoes_toast' not in st.session_state:
    st.session_state.notificacoes_toast = []
if 'tempo_medio_processo' not in st.session_state:
    st.session_state.tempo_medio_processo = "-"
if 'tempo_medio_faturamento' not in st.session_state:
    st.session_state.tempo_medio_faturamento = "-"

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
LIMITE_PESO_KG = 20
LIMITE_VALOR_REAIS = 2500

# --- CARREGAMENTO DE SECRETS ---
def carregar_secrets():
    caminho = Path(".streamlit/secrets.toml")
    if caminho.exists():
        with open(caminho, "rb") as f:
            return tomllib.load(f)
    return st.secrets

# --- FUNÇÕES DE APOIO ---
@st.cache_data(ttl=INTERVALO_SEGUNDOS)
def buscar_pedidos():
    secrets = carregar_secrets()
    url = "https://app.omie.com.br/api/v1/produtos/pedido/"
    data_alvo = (datetime.now() - timedelta(days=5)).strftime("%d/%m/%Y")
    
    pagina_atual = 1
    total_de_paginas = 1
    todos_pedidos = []

    while pagina_atual <= total_de_paginas:
        payload = {
            "call": "ListarPedidos",
            "app_key": secrets["APP_KEY"],
            "app_secret": secrets["APP_SECRET"],
            "param": [{"pagina": pagina_atual, "registros_por_pagina": 300, "apenas_importado_api": "N", "filtrar_por_data_de": data_alvo}]
        }
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            res = response.json()

            total_de_paginas = res.get("total_de_paginas", 1)
            pedidos_pagina = res.get("pedido_venda_produto", [])
            if not pedidos_pagina: break
            todos_pedidos.extend(pedidos_pagina)
            pagina_atual += 1
        except (requests.exceptions.RequestException, ValueError) as e:
            st.error(f"Erro ao buscar pedidos na página {pagina_atual}: {e}")
            break
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
        info_cadastro = p.get("infoCadastro", {})
        observacoes = p.get("observacoes", {})
        deps = p.get("departamentos", []) or []
        total_pedido = p.get("total_pedido", {})
        etapas_alteracoes = p.get("etapas_alteracoes", [])
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
            "Data Faturamento": info_cadastro.get("dFat", "-"),
            "Hora Faturamento": info_cadastro.get("hFat", "-"),
            "Data Alteração": info_cadastro.get("dAlt", "-"),
            "Hora Alteração": info_cadastro.get("hAlt", "-"),
            "Data Inclusao": info_cadastro.get("dInc", "-"),
            "Hora Inclusao": info_cadastro.get("hInc", "-"),
            "Departamento": nome_depto,
            "Transportadora": limpar_observacao(observacoes.get("obs_venda")),
            "Historico Etapas": etapas_alteracoes,
            "Valor Total": total_pedido.get("valor_total_pedido", 0.0),
            "Peso Bruto (kg)": frete.get("peso_bruto", 0.0)
        })
    return pd.DataFrame(dados_processados).sort_values(by="Pedido", ascending=False)

# --- FUNÇÕES DE AJUSTE PARA HORÁRIO COMERCIAL ---
def ajustar_para_horario_comercial(dt):
    while True:
        wd = dt.weekday()
        if wd <= 3:  # Segunda a Quinta (08:00 às 18:00)
            start_work = dt.replace(hour=8, minute=0, second=0, microsecond=0)
            end_work = dt.replace(hour=18, minute=0, second=0, microsecond=0)
            if dt < start_work:
                return start_work
            elif dt >= end_work:
                dt = (dt + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                continue
            else:
                return dt
        elif wd == 4:  # Sexta-feira (08:00 às 17:00)
            start_work = dt.replace(hour=8, minute=0, second=0, microsecond=0)
            end_work = dt.replace(hour=17, minute=0, second=0, microsecond=0)
            if dt < start_work:
                return start_work
            elif dt >= end_work:
                dt = (dt + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                continue
            else:
                return dt
        else:  # Sábado e Domingo
            dt = (dt + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
            continue

def parse_and_adjust_datetime(data_str, hora_str):
    if not data_str or data_str == '-' or not hora_str or hora_str == '-':
        dt = datetime.now()
    else:
        try:
            dt = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M:%S")
        except Exception:
            dt = datetime.now()
    dt_adjusted = ajustar_para_horario_comercial(dt)
    return dt_adjusted.strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime_real(data_str, hora_str):
    if not data_str or data_str == '-' or not hora_str or hora_str == '-':
        dt = datetime.now()
    else:
        try:
            dt = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M:%S")
        except Exception:
            dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# --- CONSTANTES DE HORÁRIO COMERCIAL ---
from datetime import time as dt_time
TIME_0800 = dt_time(8, 0, 0)
TIME_1700 = dt_time(17, 0, 0)
TIME_1800 = dt_time(18, 0, 0)

# --- FUNÇÃO AUXILIAR PARA CÁLCULO DE TEMPO EM HORÁRIO COMERCIAL ---
def calcular_tempo_trabalho(t_start, t_end):
    if pd.isna(t_start) or pd.isna(t_end):
        return pd.Timedelta(0)
    
    t_start = pd.to_datetime(t_start)
    t_end = pd.to_datetime(t_end)
    
    if t_start > t_end:
        return pd.Timedelta(0)
    
    total_working_time = pd.Timedelta(0)
    current_date = t_start.date()
    end_date = t_end.date()
    
    while current_date <= end_date:
        weekday = current_date.weekday() # Monday = 0, ..., Sunday = 6
        
        # Define os limites do expediente do dia
        if weekday <= 3:  # Segunda a Quinta (08:00 às 18:00)
            work_start_time = datetime.combine(current_date, TIME_0800)
            work_end_time = datetime.combine(current_date, TIME_1800)
            is_working_day = True
        elif weekday == 4:  # Sexta-feira (08:00 às 17:00)
            work_start_time = datetime.combine(current_date, TIME_0800)
            work_end_time = datetime.combine(current_date, TIME_1700)
            is_working_day = True
        else:  # Sábado e Domingo (sem expediente)
            is_working_day = False
            
        if is_working_day:
            # Interseção do período com o expediente do dia
            int_start = max(t_start, work_start_time)
            int_end = min(t_end, work_end_time)
            if int_start < int_end:
                total_working_time += (int_end - int_start)
                
        current_date += timedelta(days=1)
        
    return total_working_time

# --- FUNÇÃO AUXILIAR PARA CÁLCULO DE TEMPO MÉDIO ---
def calcular_tempo_medio(df_historico, col_inicio, col_fim):
    if df_historico.empty:
        return "-"
    if col_inicio not in df_historico.columns or col_fim not in df_historico.columns:
        return "-"
    # Filtra pedidos que possuem ambas as colunas preenchidas
    df_valid = df_historico[df_historico[col_inicio].notna() & df_historico[col_fim].notna()].copy()
    if df_valid.empty:
        return "-"
    
    # Calcula o tempo útil de trabalho para cada linha
    diff = df_valid.apply(lambda row: calcular_tempo_trabalho(row[col_inicio], row[col_fim]), axis=1)
    
    # Filtra diferenças válidas (incluindo 0 segundos para transições rápidas/estimadas)
    diff = diff[diff >= pd.Timedelta(0)]
    if diff.empty:
        return "-"
    
    # Calcula a média
    mean_diff = diff.mean()
    
    # Formata a duração amigavelmente
    total_seconds = int(mean_diff.total_seconds())
    dias = total_seconds // 86400
    horas = (total_seconds % 86400) // 3600
    minutos = (total_seconds % 3600) // 60
    
    parts = []
    if dias > 0:
        parts.append(f"{dias}d")
    if horas > 0 or dias > 0:
        parts.append(f"{horas}h")
    parts.append(f"{minutos}m")
    
    return " ".join(parts)

# --- PROCESSAMENTO DE HISTÓRICO PRECISO (USANDO DATA DE ALTERAÇÃO DA OMIE) ---
def verificar_e_notificar_mudancas():
    df_atual = st.session_state.get('df_pedidos_cache', pd.DataFrame())
    if df_atual.empty:
        return

    # Garante pasta e arquivo CSV
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    historico_pedidos_file = data_dir / "historico_pedidos.csv"

    try:
        df_historico = pd.read_csv(historico_pedidos_file)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_historico = pd.DataFrame(columns=["Pedido", "DataEntradaSeparacao", "DataEntradaFaturar", "DataFaturamento"])

    if "DataEntradaFaturar" not in df_historico.columns:
        df_historico["DataEntradaFaturar"] = np.nan

    if not df_historico.empty and 'Pedido' in df_historico.columns:
        df_historico['Pedido'] = pd.to_numeric(df_historico['Pedido'], errors='coerce').fillna(0).astype(int)
    
    df_historico = df_historico.astype({"DataEntradaSeparacao": object, "DataEntradaFaturar": object, "DataFaturamento": object})

    hoje_omie = datetime.now().strftime('%d/%m/%Y')  # Formato Omie: DD/MM/YYYY
    houve_alteracao = False

    for _, row in df_atual.iterrows():
        try:
            pedido_id = int(row['Pedido'])
            etapa_atual = str(row['Etapa']).strip()
            data_alt = str(row.get('Data Alteração', '-')).strip()
            hora_alt = str(row.get('Hora Alteração', '-')).strip()
            data_fat = str(row.get('Data Faturamento', '-')).strip()
            hora_fat = str(row.get('Hora Faturamento', '-')).strip()
            data_inc = str(row.get('Data Inclusao', '-')).strip()
            hora_inc = str(row.get('Hora Inclusao', '-')).strip()

            # Entrada de separação é baseada na inclusão (lançamento) do pedido
            ts_separacao = parse_and_adjust_datetime(data_inc, hora_inc)

            # REGRA 1: Pedidos em Separar Estoque
            if etapa_atual == 'Separar Estoque':
                if pedido_id not in df_historico['Pedido'].values:
                    nova_linha = pd.DataFrame([{
                        "Pedido": pedido_id,
                        "DataEntradaSeparacao": ts_separacao,
                        "DataEntradaFaturar": np.nan,
                        "DataFaturamento": np.nan
                    }])
                    df_historico = pd.concat([df_historico, nova_linha], ignore_index=True)
                    houve_alteracao = True
                else:
                    idx = df_historico.index[df_historico['Pedido'] == pedido_id].tolist()
                    if idx and pd.isna(df_historico.loc[idx[0], 'DataEntradaSeparacao']):
                        df_historico.loc[idx[0], 'DataEntradaSeparacao'] = ts_separacao
                        houve_alteracao = True

            # REGRA 2: Pedidos em Faturar
            elif etapa_atual == 'Faturar':
                ts_faturar = parse_and_adjust_datetime(data_alt, hora_alt)
                if pedido_id not in df_historico['Pedido'].values:
                    nova_linha = pd.DataFrame([{
                        "Pedido": pedido_id,
                        "DataEntradaSeparacao": ts_separacao,
                        "DataEntradaFaturar": ts_faturar,
                        "DataFaturamento": np.nan
                    }])
                    df_historico = pd.concat([df_historico, nova_linha], ignore_index=True)
                    houve_alteracao = True
                else:
                    idx = df_historico.index[df_historico['Pedido'] == pedido_id].tolist()
                    if idx:
                        if pd.isna(df_historico.loc[idx[0], 'DataEntradaSeparacao']):
                            df_historico.loc[idx[0], 'DataEntradaSeparacao'] = ts_separacao
                            houve_alteracao = True
                        if pd.isna(df_historico.loc[idx[0], 'DataEntradaFaturar']):
                            df_historico.loc[idx[0], 'DataEntradaFaturar'] = ts_faturar
                            houve_alteracao = True

            # REGRA 3: Pedidos Faturados
            elif etapa_atual == 'Faturado':
                # REGRA CORRIGIDA: Captura apenas o horário nativo de faturamento da API e não altera a entrada
                if data_fat and data_fat != '-':
                    ts_faturamento = parse_datetime_real(data_fat, hora_fat)
                    if pedido_id in df_historico['Pedido'].values:
                        idx = df_historico.index[df_historico['Pedido'] == pedido_id].tolist()
                        if idx:
                            if pd.isna(df_historico.loc[idx[0], 'DataEntradaSeparacao']):
                                df_historico.loc[idx[0], 'DataEntradaSeparacao'] = ts_separacao
                                houve_alteracao = True
                            if pd.isna(df_historico.loc[idx[0], 'DataFaturamento']):
                                df_historico.loc[idx[0], 'DataFaturamento'] = ts_faturamento
                                houve_alteracao = True
                            # O campo DataEntradaFaturar NÃO é alterado aqui! Ele permanece inalterado para evitar o bug de < 1m.
                    else:
                        nova_linha = pd.DataFrame([{
                            "Pedido": pedido_id,
                            "DataEntradaSeparacao": ts_separacao,
                            "DataEntradaFaturar": np.nan,
                            "DataFaturamento": ts_faturamento
                        }])
                        df_historico = pd.concat([df_historico, nova_linha], ignore_index=True)
                        houve_alteracao = True

        except Exception:
            continue

    # Salva no arquivo CSV se houver alterações
    if houve_alteracao:
        try:
            df_historico = df_historico.groupby('Pedido', as_index=False).first()
            df_historico['Pedido'] = df_historico['Pedido'].astype(int)
            df_historico.to_csv(historico_pedidos_file, index=False, encoding='utf-8-sig')
            st.sidebar.success("✅ Histórico atualizado!")
        except PermissionError:
            st.sidebar.error("⚠️ Feche o arquivo CSV se ele estiver aberto no Excel.")
        except Exception as e:
            st.sidebar.error(f"Erro ao salvar: {e}")

    # Filtra o histórico para o dia de hoje de forma a exibir médias operacionais correspondentes apenas a hoje
    hoje = datetime.now().date()
    df_historico_hoje = pd.DataFrame()
    if not df_historico.empty and 'DataFaturamento' in df_historico.columns:
        try:
            df_historico_parsed = df_historico.copy()
            df_historico_parsed['DataFaturamento_Date'] = pd.to_datetime(df_historico_parsed['DataFaturamento'].astype(str).str[:10], errors='coerce').dt.date
            df_historico_hoje = df_historico_parsed[df_historico_parsed['DataFaturamento_Date'] == hoje]
        except Exception:
            df_historico_hoje = pd.DataFrame()

    # Atualiza as métricas globais na sessão (calculando sobre hoje para bater com a aba de histórico de hoje)
    if not df_historico_hoje.empty:
        st.session_state.tempo_medio_processo = calcular_tempo_medio(df_historico_hoje, 'DataEntradaSeparacao', 'DataFaturamento')
        st.session_state.tempo_medio_faturamento = calcular_tempo_medio(df_historico_hoje, 'DataEntradaFaturar', 'DataFaturamento')
    else:
        st.session_state.tempo_medio_processo = "-"
        st.session_state.tempo_medio_faturamento = "-"
    st.session_state.pedidos_antigos = df_atual.copy()

# --- LÓGICA DE ATUALIZAÇÃO AUTOMÁTICA E CONTROLE DA SIDEBAR ---
agora = datetime.now()
segundos_desde_ultima = (agora - st.session_state.ultima_atualizacao).total_seconds()
tempo_restante = max(0, int(INTERVALO_SEGUNDOS - segundos_desde_ultima))

if tempo_restante <= 0:
    st.cache_data.clear()
    st.session_state.ultima_atualizacao = datetime.now()
    st.session_state.pedidos_antigos = st.session_state.get('df_pedidos_cache', pd.DataFrame()).copy()
    st.rerun()

st.sidebar.header("Controle de Sincronização")
if st.sidebar.button("🔄 Sincronizar Agora", use_container_width=True):
    st.cache_data.clear()
    st.session_state.notificacoes_toast = []
    st.session_state.ultima_atualizacao = datetime.now()
    st.session_state.pedidos_antigos = st.session_state.get('df_pedidos_cache', pd.DataFrame()).copy()
    st.rerun()

st.sidebar.metric("Próxima atualização em", f"{tempo_restante // 60:02d}:{tempo_restante % 60:02d}")
st.sidebar.caption(f"Última: {st.session_state.ultima_atualizacao.strftime('%H:%M:%S')}")

with st.spinner("Carregando e processando pedidos do Omie..."):
    try:
        dados_brutos = buscar_pedidos()
        if dados_brutos:
            df = processar_pedidos(dados_brutos)
            st.session_state['df_pedidos_cache'] = df
            verificar_e_notificar_mudancas()
            st.session_state['erro_conexao_omie'] = False
        else:
            st.session_state['erro_conexao_omie'] = True
    except Exception as e:
        st.session_state['erro_conexao_omie'] = True

    # Fallback de Resiliência: se a chamada falhou, exibe aviso e mantém os dados anteriores do session_state
    if st.session_state.get('erro_conexao_omie', False):
        if not st.session_state.get('df_pedidos_cache', pd.DataFrame()).empty:
            st.sidebar.warning("⚠️ Exibindo dados em cache (Falha temporária ao conectar com a API Omie).")
        else:
            st.warning("Não foi possível conectar à API do Omie no momento e não há dados em cache.")

    # --- LÓGICA DE SNAPSHOT DIÁRIO ---
    current_date = datetime.now().date()
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    historico_resumo_file = data_dir / "historico_diario_resumo.csv"

    if st.session_state.last_daily_snapshot_date < current_date:
        if not st.session_state.df_pedidos_cache.empty:
            total_pendentes_snapshot = len(df[df["Etapa"].isin(["Em Processo", "Separar Estoque", "Faturar"])])
            total_faturados_snapshot = len(df[df["Etapa"] == "Faturado"])
            
            new_entry_resumo = pd.DataFrame([{
                "Data": current_date.strftime("%Y-%m-%d"),
                "Total Pendentes": total_pendentes_snapshot,
                "Total Faturados": total_faturados_snapshot
            }])
            new_entry_resumo.to_csv(historico_resumo_file, mode='a', header=not historico_resumo_file.exists(), index=False)
            st.toast(f"Resumo diário salvo para {current_date.strftime('%d/%m/%Y')}!", icon="📸")

        historico_detalhado_file = data_dir / f"pedidos_detalhados_{current_date.strftime('%Y-%m-%d')}.csv"
        if not st.session_state.df_pedidos_cache.empty:
            st.session_state.df_pedidos_cache.to_csv(historico_detalhado_file, index=False, encoding='utf-8-sig')
            st.toast(f"Detalhes dos pedidos do dia salvos em {historico_detalhado_file.name}!", icon="💾")
        
        st.session_state.last_daily_snapshot_date = current_date
        st.rerun()

# --- FILTROS DA SIDEBAR ---
st.sidebar.divider()
st.sidebar.header("Filtros")

if not st.session_state.df_pedidos_cache.empty:
    opcoes_depto = ["Todos"] + sorted(st.session_state.df_pedidos_cache["Departamento"].unique().tolist())
else:
    opcoes_depto = ["Todos"]

filtro_depto = st.sidebar.selectbox("Filtrar por Departamento", options=opcoes_depto)

df_filtrado = st.session_state.df_pedidos_cache
if filtro_depto != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Departamento"] == filtro_depto]

if not df_filtrado.empty:
    opcoes_etapa = df_filtrado["Etapa"].unique()
    filtro_etapa = st.sidebar.multiselect("Filtrar por Etapa", options=opcoes_etapa)
    if filtro_etapa: 
        df_filtrado = df_filtrado[df_filtrado["Etapa"].isin(filtro_etapa)]

# --- RENDERIZAÇÃO DAS ABAS ---
aba_painel, aba_historico = st.tabs(["📊 Painel Operacional", "📁 Histórico & Consolidado"])

with aba_painel:
    if not df_filtrado.empty:
        st.markdown("## 📊 Painel Operacional")
        st.write("")

        # --- CARDS DE STATUS ---
        with st.container():
            if not df_filtrado.empty:
                contagem_etapas = df_filtrado["Etapa"].value_counts()
            else:
                contagem_etapas = pd.Series()

            etapas_config = [
                {"nome": "EM PROCESSO", "cor": "#FFC107", "desc": "pedidos aguardando"},
                {"nome": "SEPARAR ESTOQUE", "cor": "#9C27B0", "desc": "pendentes para separação"},
                {"nome": "FATURAR", "cor": "#FF9800", "desc": "caixas na embalagem"},
                {"nome": "FATURADO", "cor": "#4CAF50", "desc": "concluídos no período"}
            ]
            
            cols = st.columns(6)
            for i in range(4):
                col = cols[i]
                config = etapas_config[i]
                nome_chave = config["nome"].title() 
                qtd = contagem_etapas.get(nome_chave, 0)
                
                with col.container(border=True, height=150):
                    st.markdown(f"<div style='border-top: 4px solid {config['cor']}; margin: -15px -15px 8px -15px;'></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center; font-size: 0.7rem; font-weight: bold; color: #555;'>{config['nome']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center; font-size: 2rem; font-weight: bold;'>{qtd}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center; font-size: 0.65rem; color: #888;'>{config['desc']}</div>", unsafe_allow_html=True)
            
            with cols[4].container(border=True, height=150):
                st.markdown(f"<div style='border-top: 4px solid #00BCD4; margin: -15px -15px 8px -15px;'></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 0.7rem; font-weight: bold; color: #555;'>MÉDIA PROCESSO</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 2.0rem; font-weight: bold;'>{st.session_state.tempo_medio_processo}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 0.65rem; color: #888;'>lançamento (separação) até nf</div>", unsafe_allow_html=True)

            with cols[5].container(border=True, height=150):
                st.markdown(f"<div style='border-top: 4px solid #FF5722; margin: -15px -15px 8px -15px;'></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 0.7rem; font-weight: bold; color: #555;'>MÉDIA FATURAMENTO</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 2.0rem; font-weight: bold;'>{st.session_state.tempo_medio_faturamento}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 0.65rem; color: #888;'>etapa faturar até emissão nf</div>", unsafe_allow_html=True)

        # --- ALERTAS CRÍTICOS ---
        df_alerta_critico = st.session_state.df_pedidos_cache[st.session_state.df_pedidos_cache["Etapa"].isin(["Separar Estoque", "Faturar"])]
        pedidos_grandes_valor = df_alerta_critico[df_alerta_critico["Valor Total"] > LIMITE_VALOR_REAIS]
        pedidos_pesados = df_alerta_critico[df_alerta_critico["Peso Bruto (kg)"] > LIMITE_PESO_KG]

        if not pedidos_grandes_valor.empty or not pedidos_pesados.empty:
            with st.container(border=True):
                st.markdown("##### 🚨 Alertas de Pedidos Críticos em Separação")
                for _, row in pedidos_grandes_valor.iterrows():
                    st.error(f"💰 **VALOR ALTO:** Pedido **{int(row['Pedido'])}** - R$ {row['Valor Total']:.2f}", icon="💰")
                for _, row in pedidos_pesados.iterrows():
                    st.error(f"⚖️ **PESO ELEVADO:** Pedido **{int(row['Pedido'])}** - {row['Peso Bruto (kg)']:.2f} kg", icon="⚖️")

        st.divider()
        
        st.subheader("🕒 Painel de Coletas (Tempo Real)")
        with st.container(border=True):
            hora_atual = agora_brasilia().time()
            
            t_800 = datetime.strptime("08:00", "%H:%M").time()
            t_1030 = datetime.strptime("10:30", "%H:%M").time()
            t_1400 = datetime.strptime("14:00", "%H:%M").time()
            t_1630 = datetime.strptime("16:30", "%H:%M").time()
            
            if t_800 <= hora_atual <= t_1030:
                st.success("🟢 **HORÁRIO DOS CORREIOS (08:00 - 10:30):** Preferência ativa para envios via Correios.")
            elif t_1030 < hora_atual < t_1400:
                st.info("⏳ **HORÁRIO J&T & TOTAL EXPRESS (10:30 - 14:00):** Preferência ativa para J&T e Total Express.")
            elif t_1400 <= hora_atual <= t_1630:
                st.error("🚨 **HORÁRIO SOUZA - FORTALEZA (14:00 - 16:30):** Prioridade máxima para pedidos Souza.")
            else:
                st.warning("🌙 **PÓS-16:30 (RETORNO LIVRE):** Retorno para J&T, Total ou Correios de acordo com a demanda.")

            st.caption("Faixas ativas: 08:00-10:30 (Correios) | 10:30-14:00 (J&T/Total) | 14:00-16:30 (Souza) | Após 16:30 (Demanda livre).")
    else:
        st.info("Aguardando dados para exibir o painel...")

with aba_historico:
    renderizar_aba_historico(st.session_state['df_pedidos_cache'])

# --- LÓGICA DE ATUALIZAÇÃO VISUAL DO CONTADOR ---
st_autorefresh(interval=30000, key="visual_refresher")
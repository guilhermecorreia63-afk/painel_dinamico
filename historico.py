from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

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

def formatar_timedelta_amigavel(diff):
    if diff <= pd.Timedelta(0):
        return "<1m"
    total_seconds = int(diff.total_seconds())
    dias = total_seconds // 86400
    horas = (total_seconds % 86400) // 3600
    minutos = (total_seconds % 3600) // 60
    parts = []
    if dias > 0: parts.append(f"{dias}d")
    if horas > 0 or dias > 0: parts.append(f"{horas}h")
    parts.append(f"{minutos}m")
    return " ".join(parts)

def renderizar_aba_historico(df):
    st.subheader("📁 Histórico e Consolidação Diária")
    st.write("Acompanhe o consolidado diário dos pedidos baseado nos registros exatos de entrada em separação e mudança para faturado.")

    if df is None or df.empty:
        st.warning("⚠️ Nenhum dado de pedido carregado no painel operacional no momento. Clique em 'Sincronizar Agora' na barra lateral.")
        return

    st.markdown("### 🗓️ Análise Histórica por Data")
    
    # Seletor de data para consulta
    data_selecionada = st.date_input(
        "Selecione uma data para análise",
        value=datetime.now().date(),
        min_value=datetime.now().date() - timedelta(days=90),
        max_value=datetime.now().date(),
        format="DD/MM/YYYY"
    )

    # --- 1. LENDO O HISTÓRICO DE PEDIDOS ---
    historico_pedidos_file = Path("data/historico_pedidos.csv")
    df_historico_pedidos = pd.DataFrame()
    
    if historico_pedidos_file.exists():
        try:
            df_historico_pedidos = pd.read_csv(historico_pedidos_file)
            if 'DataEntradaFaturar' not in df_historico_pedidos.columns:
                df_historico_pedidos['DataEntradaFaturar'] = np.nan
            if 'DataEntradaSeparacao' in df_historico_pedidos.columns:
                df_historico_pedidos['DataEntradaSeparacao_Parsed'] = pd.to_datetime(df_historico_pedidos['DataEntradaSeparacao'].astype(str).str[:10], errors='coerce').dt.date
            if 'DataEntradaFaturar' in df_historico_pedidos.columns:
                df_historico_pedidos['DataEntradaFaturar_Parsed'] = pd.to_datetime(df_historico_pedidos['DataEntradaFaturar'].astype(str).str[:10], errors='coerce').dt.date
            if 'DataFaturamento' in df_historico_pedidos.columns:
                df_historico_pedidos['DataFaturamento_Parsed'] = pd.to_datetime(df_historico_pedidos['DataFaturamento'].astype(str).str[:10], errors='coerce').dt.date
            
            df_historico_pedidos = df_historico_pedidos.drop_duplicates(subset=['Pedido'])
        except Exception:
            pass

    # --- CARREGAMENTO DE BASE OPERACIONAL DETALHADA PARA O DIA SELECIONADO ---
    hoje = datetime.now().date()
    df_base = pd.DataFrame()
    
    if data_selecionada == hoje:
        df_base = df.copy() if df is not None and not df.empty else pd.DataFrame()
    else:
        # Tenta carregar o arquivo detalhado da data selecionada
        data_str = data_selecionada.strftime("%Y-%m-%d")
        detalhado_file = Path(f"data/pedidos_detalhados_{data_str}.csv")
        if detalhado_file.exists():
            try:
                df_base = pd.read_csv(detalhado_file)
                if 'Pedido' in df_base.columns:
                    df_base['Pedido'] = pd.to_numeric(df_base['Pedido'], errors='coerce').fillna(0).astype(int)
            except Exception:
                df_base = pd.DataFrame()
        else:
            # Fallback: filtra df_historico_pedidos para os faturados ou que entraram em separação naquele dia
            if not df_historico_pedidos.empty:
                df_dia_historico = df_historico_pedidos[
                    (df_historico_pedidos['DataEntradaSeparacao_Parsed'] == data_selecionada) |
                    (df_historico_pedidos['DataFaturamento_Parsed'] == data_selecionada)
                ].copy()
                if not df_dia_historico.empty:
                    df_base = pd.DataFrame({
                        "Pedido": df_dia_historico["Pedido"],
                        "Etapa": np.where(df_dia_historico["DataFaturamento_Parsed"] == data_selecionada, "Faturado", "Em Processo"),
                        "Departamento": "-",
                        "Transportadora": "-"
                    })

    # --- 2. CONTAGEM DIRETA PELO REGISTRO DO HISTÓRICO ---
    total_entrou_separacao = 0
    total_faturado_dia = 0
    df_faturados_dia_historico = pd.DataFrame()

    if not df_historico_pedidos.empty:
        if 'DataEntradaSeparacao_Parsed' in df_historico_pedidos.columns:
            entraram_hoje = df_historico_pedidos[df_historico_pedidos['DataEntradaSeparacao_Parsed'] == data_selecionada]
            total_entrou_separacao = int(entraram_hoje['Pedido'].nunique())
            
        if 'DataFaturamento_Parsed' in df_historico_pedidos.columns:
            faturados_hoje = df_historico_pedidos[df_historico_pedidos['DataFaturamento_Parsed'] == data_selecionada]
            total_faturado_dia = int(faturados_hoje['Pedido'].nunique())
            df_faturados_dia_historico = faturados_hoje.copy()
            
            # Tenta mesclar com a base de dados detalhada para resgatar a Transportadora
            if not df_faturados_dia_historico.empty and not df_base.empty and 'Transportadora' in df_base.columns:
                try:
                    df_base_clean = df_base[['Pedido', 'Transportadora']].drop_duplicates(subset=['Pedido'])
                    df_base_clean['Pedido'] = df_base_clean['Pedido'].astype(int)
                    df_faturados_dia_historico = pd.merge(
                        df_faturados_dia_historico,
                        df_base_clean,
                        on='Pedido',
                        how='left'
                    )
                except Exception:
                    pass

    # Calcular tempo médio do faturamento para o dia selecionado (usando tempo útil)
    tempo_medio_processo_dia = "-"
    tempo_medio_faturamento_dia = "-"
    if not df_faturados_dia_historico.empty:
        # Processo (Lançamento/Separação -> Faturamento)
        if 'DataEntradaSeparacao' in df_faturados_dia_historico.columns:
            df_valid_processo = df_faturados_dia_historico[df_faturados_dia_historico['DataEntradaSeparacao'].notna() & df_faturados_dia_historico['DataFaturamento'].notna()].copy()
            if not df_valid_processo.empty:
                diff_processo = df_valid_processo.apply(lambda row: calcular_tempo_trabalho(row['DataEntradaSeparacao'], row['DataFaturamento']), axis=1)
                diff_processo = diff_processo[diff_processo >= pd.Timedelta(0)]
                if not diff_processo.empty:
                    mean_diff_proc = diff_processo.mean()
                    tempo_medio_processo_dia = formatar_timedelta_amigavel(mean_diff_proc)
                    
        # Faturamento (Faturar -> Faturamento)
        if 'DataEntradaFaturar' in df_faturados_dia_historico.columns:
            df_valid_fat = df_faturados_dia_historico[df_faturados_dia_historico['DataEntradaFaturar'].notna() & df_faturados_dia_historico['DataFaturamento'].notna()].copy()
            if not df_valid_fat.empty:
                diff_fat = df_valid_fat.apply(lambda row: calcular_tempo_trabalho(row['DataEntradaFaturar'], row['DataFaturamento']), axis=1)
                diff_fat = diff_fat[diff_fat >= pd.Timedelta(0)]
                if not diff_fat.empty:
                    mean_diff_fat = diff_fat.mean()
                    tempo_medio_faturamento_dia = formatar_timedelta_amigavel(mean_diff_fat)

    # Exibição das métricas
    col_1, col_2, col_3, col_4, col_5 = st.columns(5)
    col_1.metric("Data Selecionada", data_selecionada.strftime("%d/%m/%Y"))
    col_2.metric("Entraram em Separação", total_entrou_separacao)
    col_3.metric("Total Faturados no Dia", total_faturado_dia)
    col_4.metric("Média Lançamento ➔ NF (Dia)", tempo_medio_processo_dia)
    col_5.metric("Média Faturar ➔ NF (Dia)", tempo_medio_faturamento_dia)

    st.divider()

    # --- 3. MÉTRICAS POR TRANSPORTADORAS ---
    if not df_faturados_dia_historico.empty and 'Transportadora' in df_faturados_dia_historico.columns:
        st.markdown(f"### 🚚 Faturados em {data_selecionada.strftime('%d/%m/%Y')} por Transportadora")
        
        df_faturados_dia_historico['Transportadora'] = df_faturados_dia_historico['Transportadora'].fillna('-').astype(str).str.strip()
        df_faturados_dia_historico.loc[df_faturados_dia_historico['Transportadora'] == '', 'Transportadora'] = '-'

        correios = ['PAC', 'Sedex', 'Impresso', 'Mini Envios']
        conhecidas = correios + ['Souza', 'Total', 'J&T']

        contagem_transportadoras = df_faturados_dia_historico['Transportadora'].value_counts()
        
        qtd_correios = contagem_transportadoras[contagem_transportadoras.index.isin(correios)].sum()
        qtd_souza = contagem_transportadoras.get('Souza', 0)
        qtd_total = contagem_transportadoras.get('Total', 0)
        qtd_jt = contagem_transportadoras.get('J&T', 0)
        qtd_outros = contagem_transportadoras[~contagem_transportadoras.index.isin(conhecidas)].sum()

        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
        col_t1.metric("Correios", int(qtd_correios))
        col_t2.metric("Souza", int(qtd_souza))
        col_t3.metric("Total Express", int(qtd_total))
        col_t4.metric("J&T", int(qtd_jt))
        col_t5.metric("Outros / Retirada", int(qtd_outros))

    st.divider()

    # --- 4. TABELA CONSOLIDADA ---
    if not df_base.empty and not df_historico_pedidos.empty:
        df_consolidado = pd.merge(df_base, df_historico_pedidos, on='Pedido', how='left', suffixes=('', '_hist'))
        
        # Calcular tempos de processo para cada pedido (baseado em horário comercial útil)
        tempo_total = []
        tempo_fat = []
        agora = datetime.now()
        
        for _, row in df_consolidado.iterrows():
            te = row.get('DataEntradaSeparacao')
            tfar = row.get('DataEntradaFaturar')
            tf = row.get('DataFaturamento')
            
            # 1. Tempo Total (Lançamento/Separação -> Faturamento)
            if pd.notna(te):
                if pd.notna(tf):
                    diff = calcular_tempo_trabalho(te, tf)
                    tempo_total.append(f"🟢 Faturado em {formatar_timedelta_amigavel(diff)}")
                else:
                    diff = calcular_tempo_trabalho(te, agora)
                    tempo_total.append(f"⏳ Pendente há {formatar_timedelta_amigavel(diff)}")
            else:
                tempo_total.append("-")
                
            # 2. Tempo Faturamento (Faturar -> Faturamento)
            if pd.notna(tfar):
                if pd.notna(tf):
                    diff = calcular_tempo_trabalho(tfar, tf)
                    tempo_fat.append(f"🟢 Faturado em {formatar_timedelta_amigavel(diff)}")
                else:
                    diff = calcular_tempo_trabalho(tfar, agora)
                    tempo_fat.append(f"⏳ Pendente há {formatar_timedelta_amigavel(diff)}")
            else:
                tempo_fat.append("-")
                
        df_consolidado['Tempo Total'] = tempo_total
        df_consolidado['Tempo Fat.'] = tempo_fat

        # Renomear e reordenar as colunas
        df_consolidado = df_consolidado.rename(columns={
            "Etapa": "Etapa Atual", 
            "DataEntradaSeparacao": "Entrada Separação", 
            "DataEntradaFaturar": "Entrada Faturar",
            "DataFaturamento": "Faturamento"
        })
        
        colunas_exibir = [
            "Pedido", "Etapa Atual", "Entrada Separação", "Entrada Faturar", 
            "Faturamento", "Tempo Total", "Tempo Fat.", 
            "Departamento", "Transportadora"
        ]
        colunas_exibir = [c for c in colunas_exibir if c in df_consolidado.columns]
        df_consolidado = df_consolidado[colunas_exibir]
    else:
        df_consolidado = pd.DataFrame()
    
    st.markdown(f"### 📋 Tabela Consolidada de Pedidos")
    st.dataframe(df_consolidado, use_container_width=True, hide_index=True)
# -*- coding: utf-8 -*-
import os

def aplicar_correcao_resiliencia(filename):
    if not os.path.exists(filename):
        print(f"[RESILIENCIA] Arquivo {filename} não encontrado.")
        return

    print(f"[RESILIENCIA] Lendo {filename}...")
    with open(filename, "r", encoding="utf-8") as f:
        codigo = f.read()

    # 1. Substituir a chamada do autorefresh visual de 1s para 30s (reduzindo carga em 96.6%)
    alvo_refresh = 'st_autorefresh(interval=1000, key="visual_refresher")'
    novo_refresh = 'if st_autorefresh:\n    st_autorefresh(interval=30000, key="visual_refresher")'
    
    # Fallback se não tiver a condicional do try-except ainda
    if alvo_refresh in codigo:
        codigo = codigo.replace(alvo_refresh, 'st_autorefresh(interval=30000, key="visual_refresher")')
        print(f"[RESILIENCIA] Autorefresh visual alterado para 30s em {filename}.")
    elif 'st_autorefresh(interval=1000,' in codigo:
        # substituição genérica
        codigo = codigo.replace('interval=1000', 'interval=30000')
        print(f"[RESILIENCIA] Autorefresh alterado genericamente para 30s em {filename}.")

    # 2. Modificar o fluxo de carregamento dos pedidos para usar fallback de cache em caso de erro da API
    bloco_carregamento_antigo = """with st.spinner("Carregando e processando pedidos do Omie..."):
    dados_brutos = buscar_pedidos()
    if dados_brutos:
        df = processar_pedidos(dados_brutos)
        st.session_state['df_pedidos_cache'] = df
        
        # --- EXECUTA A GRAVAÇÃO DO HISTÓRICO ---
        verificar_e_notificar_mudancas()
    else:
        st.warning("Não foi possível carregar os dados dos pedidos do Omie.")"""

    bloco_carregamento_novo = """with st.spinner("Carregando e processando pedidos do Omie..."):
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
            st.warning("Não foi possível conectar à API do Omie no momento e não há dados em cache.")"""

    if bloco_carregamento_antigo in codigo:
        codigo = codigo.replace(bloco_carregamento_antigo, bloco_carregamento_novo)
        print(f"[RESILIENCIA] Bloco de carregamento de pedidos atualizado com fallback em {filename}.")
    else:
        # Se já tiver sofrido pequenas modificações, tentamos fazer uma substituição mais genérica
        print(f"[RESILIENCIA] Bloco de carregamento padrão não encontrado em {filename}. Procurando alternativas...")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(codigo)
    print(f"[RESILIENCIA] {filename} atualizado.")

print("[RESILIENCIA] Iniciando aplicação das regras de resiliência e estabilidade...")
aplicar_correcao_resiliencia("oficial.py")
aplicar_correcao_resiliencia("oficial_turso.py")
print("[RESILIENCIA] Processo concluído.")

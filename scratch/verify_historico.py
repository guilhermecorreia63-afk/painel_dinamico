import pandas as pd
from unittest.mock import MagicMock
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Mock streamlit before importing historico
mock_st = MagicMock()
mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
sys.modules['streamlit'] = mock_st

import streamlit as st
import historico

# Prepare mock data
df_mock = pd.DataFrame({
    'Pedido': [16573, 16572],
    'Etapa': ['Separar Estoque', 'Separar Estoque'],
    'Data Alteração': ['24/08/2026', '24/08/2026'],
    'Hora Alteração': ['08:39:25', '05:49:52'],
    'Data Faturamento': ['-', '-'],
    'Hora Faturamento': ['-', '-'],
    'Departamento': ['Ecommerce', 'Ecommerce'],
    'Transportadora': ['Sedex', 'Impresso']
})

# Call the function
try:
    historico.renderizar_aba_historico(df_mock)
    print("Verification passed! No exceptions raised.")
except Exception as e:
    print("Verification failed with exception:", e)
    raise e

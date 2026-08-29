@echo off
title Painel Omie Turso - Rede Local
echo Iniciando o painel de pedidos (Versao Banco de Dados)...
cd /d %~dp0
call .venv\Scripts\activate
    streamlit run oficial_turso.py --server.address 172.16.110.12
pause

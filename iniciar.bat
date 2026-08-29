@echo off
title Painel Omie - Rede Local
echo Iniciando o painel de pedidos...
cd /d %~dp0
call .venv\Scripts\activate
    streamlit run oficial.py --server.address 172.16.110.12
pause

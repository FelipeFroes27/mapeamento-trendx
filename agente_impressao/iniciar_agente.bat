@echo off
rem Inicia o agente de impressão sem janela. Coloque um atalho deste arquivo em shell:startup.
cd /d "%~dp0"
start "" pythonw agente.py

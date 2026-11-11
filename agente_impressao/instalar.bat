@echo off
rem Instala as dependencias do agente de impressao. Precisa do Python 3.11 ou mais novo.
cd /d "%~dp0"
python --version || (echo Python nao encontrado. Instale pelo python.org marcando "Add python.exe to PATH". & pause & exit /b 1)
python -m pip install -r requirements.txt
echo.
echo Impressoras encontradas:
python agente.py --impressoras
pause

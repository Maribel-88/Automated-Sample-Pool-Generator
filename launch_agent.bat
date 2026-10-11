@echo off
title Launching TeamLead AI Agent...
cd /d "%~dp0"

echo [1/3] Activating Local Virtual Environment Container...
call venv\Scripts\activate.bat

echo [2/3] Checking Core Component Dependencies...
pip install -r requirements.txt --quiet

echo [3/3] Booting Warehouse Logistics Web Dashboard Viewport...
streamlit run agent_app.py

pause

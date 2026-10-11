@echo off
REM Arranca el semaforo de senales (deja MetaTrader 5 abierto)
cd /d "%~dp0"
python -m semaforo bot
pause

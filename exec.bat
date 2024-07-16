@echo off
call .prueba\Scripts\activate.bat
start /B "" pythonw run.py > nul 2>&1
start http://127.0.0.1:5000
@echo off
echo 🌐 Iniciando WEX Intelligence Interface Frontend...
echo 🖥️  Interface em: http://localhost:3000
echo 📡 APIs em: http://localhost:8000
echo.

cd /d "C:\ProjetosGIT\Hackathon\Projeto-Hackathon-1\backend"
call "venv\Scripts\activate.bat"
python start_frontend_server.py
pause
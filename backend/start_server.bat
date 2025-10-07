@echo off
echo 🚀 Iniciando WEX Intelligence Backend API...
echo 📡 APIs em: http://localhost:8000
echo 🌐 Interface: http://localhost:3000
echo 📚 Docs: http://localhost:8000/docs
echo.

cd /d "C:\ProjetosGIT\Hackathon\Projeto-Hackathon-1\backend"
call "venv\Scripts\activate.bat"
python start_backend_api.py
pause
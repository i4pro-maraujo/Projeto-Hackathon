# Script PowerShell para iniciar Interface Frontend
Write-Host "🌐 Iniciando WEX Intelligence Interface Frontend..." -ForegroundColor Green
Write-Host "🖥️  Interface em: http://localhost:3000" -ForegroundColor Cyan
Write-Host "📡 APIs em: http://localhost:8000" -ForegroundColor Cyan

Set-Location "C:\ProjetosGIT\Hackathon\Projeto-Hackathon-1\backend"
& ".\venv\Scripts\Activate.ps1"
python start_frontend_server.py
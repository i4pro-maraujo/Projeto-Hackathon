# Script PowerShell para iniciar Backend API
Write-Host "🚀 Iniciando WEX Intelligence Backend API..." -ForegroundColor Green
Write-Host "📡 APIs em: http://localhost:8000" -ForegroundColor Cyan
Write-Host "🌐 Interface: http://localhost:3000" -ForegroundColor Cyan
Write-Host "📚 Docs: http://localhost:8000/docs" -ForegroundColor Cyan

Set-Location "C:\ProjetosGIT\Hackathon\Projeto-Hackathon-1\backend"
& ".\venv\Scripts\Activate.ps1"
python start_backend_api.py
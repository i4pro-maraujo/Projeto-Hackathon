#!/usr/bin/env python3
"""
Script para iniciar o Backend API do WEX Intelligence
Roda na porta 8000 servindo apenas as APIs
"""

import uvicorn
import sys
from pathlib import Path

def start_backend_api():
    """Iniciar servidor FastAPI para as APIs"""
    
    print("🚀 WEX Intelligence - Backend API")
    print("=" * 50)
    print("📡 APIs serão executadas em: http://localhost:8000")
    print("📚 Documentação: http://localhost:8000/docs")
    print("🌐 Interface Frontend: http://localhost:3000")
    print("=" * 50)
    print("📝 Pressione Ctrl+C para parar o servidor")
    print()
    
    try:
        # Iniciar servidor FastAPI
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️  Servidor API parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_backend_api()
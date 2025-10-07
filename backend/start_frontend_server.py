#!/usr/bin/env python3
"""
Servidor HTTP simples para servir a Interface HTML do WEX Intelligence
Roda na porta 3000 para separar da API (porta 8000)
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

def start_frontend_server():
    """Iniciar servidor HTTP para a Interface HTML"""
    
    # Definir configurações
    PORT = 3000
    HOST = "localhost"
    
    # Diretório onde estão os arquivos estáticos
    static_dir = Path(__file__).parent / "static"
    
    # Verificar se o diretório existe
    if not static_dir.exists():
        print(f"❌ Erro: Diretório {static_dir} não encontrado!")
        sys.exit(1)
    
    # Verificar se index.html existe
    index_file = static_dir / "index.html"
    if not index_file.exists():
        print(f"❌ Erro: Arquivo {index_file} não encontrado!")
        sys.exit(1)
    
    # Mudar para o diretório static
    os.chdir(static_dir)
    
    # Configurar handler HTTP
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
            print("🌐 WEX Intelligence - Interface Frontend")
            print("=" * 50)
            print(f"🚀 Servidor HTTP iniciado em: http://{HOST}:{PORT}")
            print(f"📁 Servindo arquivos de: {static_dir}")
            print(f"📡 APIs disponíveis em: http://localhost:8000")
            print("=" * 50)
            print("📝 Pressione Ctrl+C para parar o servidor")
            print()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n⏹️  Servidor parado pelo usuário")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Erro: Porta {PORT} já está em uso!")
            print(f"   Verifique se outro serviço está rodando na porta {PORT}")
        else:
            print(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_frontend_server()
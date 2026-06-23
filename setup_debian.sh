#!/bin/bash
# Script de instalación y arranque de SQUAD en Debian
echo "⚙️ Instalando dependencias del sistema..."
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nodejs npm git

echo "📦 Configurando entorno virtual de Python..."
python3 -m venv venv
source venv/bin/activate

echo "🐍 Instalando dependencias de Python..."
pip install fastapi uvicorn psutil

echo "🚀 Iniciando SQUAD..."
python squad_local/squad_server.py

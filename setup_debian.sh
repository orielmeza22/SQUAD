#!/bin/bash
# Script de instalación y arranque de SQUAD en Debian
echo "⚙️ Instalando dependencias del sistema..."
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nodejs npm git

echo "📦 Configurando entorno virtual de Python..."
python3 -m venv venv
source venv/bin/activate

echo "🐍 Instalando dependencias de Python..."
pip install -r squad_local_refactored/requirements.txt

if command -v docker &> /dev/null; then
    echo "🐳 Docker detectado en el sistema."
    read -p "¿Deseas activar sandbox_mode=docker para aislar la ejecución de las aplicaciones generadas? (s/N): " use_docker
    if [[ "$use_docker" =~ ^[sS]$ ]]; then
        if [ ! -f squad_settings.json ]; then
            echo '{"sandbox_mode": "docker"}' > squad_settings.json
        else
            python3 -c "import json; d=json.load(open('squad_settings.json')); d['sandbox_mode']='docker'; json.dump(d, open('squad_settings.json','w'), indent=2)"
        fi
        echo "✅ sandbox_mode configurado en 'docker'."
    fi
fi

echo "🚀 Iniciando SQUAD..."
python squad_local_refactored/main.py

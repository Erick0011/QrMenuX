#!/bin/bash

echo "🔁 Atualizando QRmenuX no PythonAnywhere..."

# Caminho do projeto
cd /home/SEU_USUARIO/SEU_PROJETO

# Ativa o ambiente virtual
source /home/SEU_USUARIO/.virtualenvs/SEU_VENV/bin/activate

# Puxa últimas alterações do Git
git pull origin main

# Instala novas dependências (se houver)
pip install -r requirements.txt

# Aplica migrações do banco de dados
flask db upgrade

# Reinicia o app
touch /var/www/SEU_USUARIO_pythonanywhere_com_wsgi.py

echo "✅ Código atualizado com sucesso!"

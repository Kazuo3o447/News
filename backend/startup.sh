#!/bin/bash
# Azure App Service Linux Startup Script
# Wird in App Service → Konfiguration → Allgemeine Einstellungen → Startbefehl eingetragen:
# bash startup.sh

cd /home/site/wwwroot
pip install -r requirements.txt --quiet
gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile '-' \
  --error-logfile '-'

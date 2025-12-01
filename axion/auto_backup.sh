#!/bin/bash

# Script que hace backups automáticos cada 2 horas
BACKUP_INTERVAL=7200  # 2 horas en segundos (2 * 60 * 60)

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[Auto-Backup] Servicio iniciado - Backup cada 2 horas${NC}" >> auto_backup.log

while true; do
    # Esperar 2 horas
    sleep $BACKUP_INTERVAL
    
    # Registrar en log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Ejecutando backup automático..." >> auto_backup.log
    
    # Ejecutar backup
    if [ -f backup.sh ]; then
        ./backup.sh >> auto_backup.log 2>&1
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Backup completado" >> auto_backup.log
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ backup.sh no encontrado" >> auto_backup.log
    fi
    
    echo "---" >> auto_backup.log
done

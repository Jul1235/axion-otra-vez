#!/bin/bash

# ============================================================
# AXION STORE - ESTADO DEL SISTEMA
# ============================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}   📊 AXION STORE - ESTADO DEL SISTEMA${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# ============================================================
# SERVICIOS
# ============================================================
echo -e "${BLUE}🔧 Servicios:${NC}"
echo ""

# MariaDB
if sudo systemctl is-active --quiet mariadb; then
    echo -e "  MariaDB:        ${GREEN}● Corriendo${NC}"
else
    echo -e "  MariaDB:        ${RED}○ Detenido${NC}"
fi

# Flask
if [ -f .flask.pid ] && kill -0 $(cat .flask.pid) 2>/dev/null; then
    FLASK_PID=$(cat .flask.pid)
    echo -e "  Flask:          ${GREEN}● Corriendo${NC} (PID: $FLASK_PID)"
    
    # Verificar si responde
    if curl -s http://localhost:5000 > /dev/null; then
        echo -e "                  ${GREEN}✓ Respondiendo en http://localhost:5000${NC}"
    else
        echo -e "                  ${YELLOW}⚠ No responde${NC}"
    fi
else
    echo -e "  Flask:          ${RED}○ Detenido${NC}"
fi

# Ngrok
if [ -f .ngrok.pid ] && kill -0 $(cat .ngrok.pid) 2>/dev/null; then
    NGROK_PID=$(cat .ngrok.pid)
    echo -e "  Ngrok:          ${GREEN}● Corriendo${NC} (PID: $NGROK_PID)"
    
    # Intentar obtener URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[^"]*\.ngrok-free\.app' | head -n1)
    if [ ! -z "$NGROK_URL" ]; then
        echo -e "                  ${GREEN}URL: $NGROK_URL${NC}"
    fi
else
    echo -e "  Ngrok:          ${RED}○ Detenido${NC}"
fi

# Auto Backup
if [ -f .auto_backup.pid ] && kill -0 $(cat .auto_backup.pid) 2>/dev/null; then
    AUTO_BACKUP_PID=$(cat .auto_backup.pid)
    echo -e "  Auto Backup:    ${GREEN}● Corriendo${NC} (PID: $AUTO_BACKUP_PID)"
else
    echo -e "  Auto Backup:    ${RED}○ Detenido${NC}"
fi

echo ""

# ============================================================
# BASE DE DATOS
# ============================================================
echo -e "${BLUE}💾 Base de Datos:${NC}"
echo ""

if sudo systemctl is-active --quiet mariadb; then
    # Estadísticas de la BD
    DB_SIZE=$(mysql -u root -p321 -e "
        SELECT 
            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
        FROM information_schema.tables 
        WHERE table_schema = 'axion_store';
    " -sN 2>/dev/null)
    
    TOTAL_PRODUCTOS=$(mysql -u root -p321 axion_store -e "SELECT COUNT(*) FROM producto;" -sN 2>/dev/null)
    TOTAL_USUARIOS=$(mysql -u root -p321 axion_store -e "SELECT COUNT(*) FROM users;" -sN 2>/dev/null)
    TOTAL_PEDIDOS=$(mysql -u root -p321 axion_store -e "SELECT COUNT(*) FROM pedido;" -sN 2>/dev/null)
    
    echo -e "  Tamaño BD:      ${CYAN}${DB_SIZE} MB${NC}"
    echo -e "  Productos:      ${CYAN}${TOTAL_PRODUCTOS}${NC}"
    echo -e "  Usuarios:       ${CYAN}${TOTAL_USUARIOS}${NC}"
    echo -e "  Pedidos:        ${CYAN}${TOTAL_PEDIDOS}${NC}"
else
    echo -e "  ${RED}MariaDB no está corriendo${NC}"
fi

echo ""

# ============================================================
# RECURSOS DEL SISTEMA
# ============================================================
echo -e "${BLUE}💻 Recursos:${NC}"
echo ""

# Uso de CPU por proceso Flask
if [ -f .flask.pid ] && kill -0 $(cat .flask.pid) 2>/dev/null; then
    FLASK_CPU=$(ps -p $(cat .flask.pid) -o %cpu --no-headers 2>/dev/null | xargs)
    FLASK_MEM=$(ps -p $(cat .flask.pid) -o %mem --no-headers 2>/dev/null | xargs)
    echo -e "  Flask CPU:      ${CYAN}${FLASK_CPU}%${NC}"
    echo -e "  Flask RAM:      ${CYAN}${FLASK_MEM}%${NC}"
fi

# Espacio en disco
DISK_USAGE=$(df -h /home | tail -1 | awk '{print $5}')
echo -e "  Disco usado:    ${CYAN}${DISK_USAGE}${NC}"

echo ""

# ============================================================
# LOGS
# ============================================================
echo -e "${BLUE}📋 Logs:${NC}"
echo ""

if [ -f flask.log ]; then
    FLASK_LOG_SIZE=$(du -h flask.log | cut -f1)
    FLASK_LOG_LINES=$(wc -l < flask.log)
    echo -e "  flask.log:      ${CYAN}${FLASK_LOG_SIZE}${NC} (${FLASK_LOG_LINES} líneas)"
else
    echo -e "  flask.log:      ${YELLOW}No existe${NC}"
fi

if [ -f ngrok.log ]; then
    NGROK_LOG_SIZE=$(du -h ngrok.log | cut -f1)
    echo -e "  ngrok.log:      ${CYAN}${NGROK_LOG_SIZE}${NC}"
else
    echo -e "  ngrok.log:      ${YELLOW}No existe${NC}"
fi

if [ -f auto_backup.log ]; then
    AUTO_LOG_SIZE=$(du -h auto_backup.log | cut -f1)
    AUTO_LOG_LINES=$(wc -l < auto_backup.log)
    echo -e "  auto_backup.log:${CYAN}${AUTO_LOG_SIZE}${NC} (${AUTO_LOG_LINES} líneas)"
else
    echo -e "  auto_backup.log:${YELLOW}No existe${NC}"
fi

echo ""

# ============================================================
# BACKUPS
# ============================================================
echo -e "${BLUE}📦 Backups:${NC}"
echo ""

BACKUP_DIR="$HOME/axion_backups"
if [ -d "$BACKUP_DIR" ]; then
    TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/axion_store_*.sql 2>/dev/null | wc -l)
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    
    echo -e "  Total backups:  ${CYAN}${TOTAL_BACKUPS}${NC}"
    echo -e "  Espacio:        ${CYAN}${BACKUP_SIZE}${NC}"
    
    if [ $TOTAL_BACKUPS -gt 0 ]; then
        ULTIMO_BACKUP=$(ls -t "$BACKUP_DIR"/axion_store_*.sql | head -1)
        FECHA_BACKUP=$(stat -c %y "$ULTIMO_BACKUP" 2>/dev/null | cut -d'.' -f1)
        echo -e "  Último backup:  ${CYAN}$(basename "$ULTIMO_BACKUP")${NC}"
        echo -e "  Fecha:          ${CYAN}${FECHA_BACKUP}${NC}"
    fi
else
    echo -e "  ${YELLOW}No hay directorio de backups${NC}"
fi

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${BLUE}💡 Comandos útiles:${NC}"
echo -e "   Iniciar:     ${CYAN}./start.sh${NC}"
echo -e "   Detener:     ${CYAN}./stop.sh${NC}"
echo -e "   Ver backups: ${CYAN}./ver_backups.sh${NC}"
echo -e "   Ver logs:    ${CYAN}tail -f flask.log${NC}"
echo ""
echo -e "${CYAN}============================================================${NC}"

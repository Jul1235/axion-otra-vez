#!/bin/bash

# ============================================================
# AXION STORE - SCRIPT DE DETENCIÓN COMPLETO
# ============================================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Banner
clear
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}   🛑 AXION STORE - DETENIENDO SERVICIOS${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Ir al directorio del proyecto
PROYECTO_DIR="/home/user/Descargas/axion"
cd "$PROYECTO_DIR" || exit 1

# Contador de servicios detenidos
SERVICIOS_DETENIDOS=0
TOTAL_SERVICIOS=3

# ============================================================
# [1/3] DETENER FLASK
# ============================================================
echo -e "${BLUE}[1/3] Deteniendo Flask...${NC}"

if [ -f .flask.pid ]; then
    FLASK_PID=$(cat .flask.pid)
    
    # Verificar si el proceso está corriendo
    if kill -0 $FLASK_PID 2>/dev/null; then
        echo "  PID encontrado: $FLASK_PID"
        
        # Intentar detener gracefully
        kill $FLASK_PID 2>/dev/null
        sleep 1
        
        # Verificar si se detuvo
        if kill -0 $FLASK_PID 2>/dev/null; then
            echo "  Forzando detención..."
            kill -9 $FLASK_PID 2>/dev/null
            sleep 1
        fi
        
        # Verificar resultado final
        if ! kill -0 $FLASK_PID 2>/dev/null; then
            echo -e "${GREEN}✓ Flask detenido correctamente${NC}"
            SERVICIOS_DETENIDOS=$((SERVICIOS_DETENIDOS + 1))
        else
            echo -e "${RED}✗ Error al detener Flask${NC}"
        fi
    else
        echo -e "${YELLOW}ℹ  Flask no estaba corriendo${NC}"
    fi
    
    rm .flask.pid 2>/dev/null
else
    echo -e "${YELLOW}ℹ  No se encontró archivo PID de Flask${NC}"
    
    # Buscar proceso por nombre
    FLASK_PROC=$(pgrep -f "python.*app.py")
    if [ ! -z "$FLASK_PROC" ]; then
        echo "  Encontrado proceso Flask sin PID file: $FLASK_PROC"
        kill $FLASK_PROC 2>/dev/null
        sleep 1
        echo -e "${GREEN}✓ Flask detenido${NC}"
        SERVICIOS_DETENIDOS=$((SERVICIOS_DETENIDOS + 1))
    fi
fi
echo ""

# ============================================================
# [2/3] DETENER NGROK
# ============================================================
echo -e "${BLUE}[2/3] Deteniendo Ngrok...${NC}"

if [ -f .ngrok.pid ]; then
    NGROK_PID=$(cat .ngrok.pid)
    
    if kill -0 $NGROK_PID 2>/dev/null; then
        echo "  PID encontrado: $NGROK_PID"
        kill $NGROK_PID 2>/dev/null
        sleep 1
        
        if ! kill -0 $NGROK_PID 2>/dev/null; then
            echo -e "${GREEN}✓ Ngrok detenido correctamente${NC}"
            SERVICIOS_DETENIDOS=$((SERVICIOS_DETENIDOS + 1))
        else
            echo -e "${RED}✗ Error al detener Ngrok${NC}"
        fi
    else
        echo -e "${YELLOW}ℹ  Ngrok no estaba corriendo${NC}"
    fi
    
    rm .ngrok.pid 2>/dev/null
else
    echo -e "${YELLOW}ℹ  No se encontró archivo PID de Ngrok${NC}"
    
    # Buscar proceso por nombre
    NGROK_PROC=$(pgrep -f "ngrok")
    if [ ! -z "$NGROK_PROC" ]; then
        echo "  Encontrado proceso Ngrok sin PID file: $NGROK_PROC"
        kill $NGROK_PROC 2>/dev/null
        sleep 1
        echo -e "${GREEN}✓ Ngrok detenido${NC}"
        SERVICIOS_DETENIDOS=$((SERVICIOS_DETENIDOS + 1))
    fi
fi
echo ""

# ============================================================
# [3/3] DETENER AUTO BACKUP
# ============================================================
echo -e "${BLUE}[3/3] Deteniendo servicio de Auto Backup...${NC}"

if [ -f .auto_backup.pid ]; then
    AUTO_BACKUP_PID=$(cat .auto_backup.pid)
    
    if kill -0 $AUTO_BACKUP_PID 2>/dev/null; then
        echo "  PID encontrado: $AUTO_BACKUP_PID"
        kill $AUTO_BACKUP_PID 2>/dev/null
        sleep 1
        
        if ! kill -0 $AUTO_BACKUP_PID 2>/dev/null; then
            echo -e "${GREEN}✓ Auto Backup detenido correctamente${NC}"
            SERVICIOS_DETENIDOS=$((SERVICIOS_DETENIDOS + 1))
        else
            echo -e "${RED}✗ Error al detener Auto Backup${NC}"
        fi
    else
        echo -e "${YELLOW}ℹ  Auto Backup no estaba corriendo${NC}"
    fi
    
    rm .auto_backup.pid 2>/dev/null
else
    echo -e "${YELLOW}ℹ  No se encontró archivo PID de Auto Backup${NC}"
    
    # Buscar proceso por nombre
    AUTO_BACKUP_PROC=$(pgrep -f "auto_backup.sh")
    if [ ! -z "$AUTO_BACKUP_PROC" ]; then
        echo "  Encontrado proceso Auto Backup sin PID file: $AUTO_BACKUP_PROC"
        kill $AUTO_BACKUP_PROC 2>/dev/null
        sleep 1
        echo -e "${GREEN}✓ Auto Backup detenido${NC}"
    fi
fi
echo ""

# ============================================================
# LIMPIEZA ADICIONAL
# ============================================================
echo -e "${BLUE}Limpieza adicional...${NC}"

# Matar cualquier proceso residual
pkill -f "python3 app.py" 2>/dev/null && echo "  Procesos Python residuales eliminados"
pkill -f "ngrok http" 2>/dev/null && echo "  Procesos Ngrok residuales eliminados"

echo ""

# ============================================================
# RESUMEN FINAL
# ============================================================
echo -e "${CYAN}============================================================${NC}"

if [ $SERVICIOS_DETENIDOS -gt 0 ]; then
    echo -e "${GREEN}   ✅ SERVICIOS DETENIDOS CORRECTAMENTE${NC}"
else
    echo -e "${YELLOW}   ℹ️  NO HABÍA SERVICIOS CORRIENDO${NC}"
fi

echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "${BLUE}📊 Resumen:${NC}"
echo -e "   Servicios detenidos: ${GREEN}$SERVICIOS_DETENIDOS${NC}/${TOTAL_SERVICIOS}"
echo ""

# Verificar que no queden procesos
PROCS_RESTANTES=$(pgrep -f "python.*app.py|ngrok|auto_backup" | wc -l)
if [ $PROCS_RESTANTES -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Advertencia: Aún hay $PROCS_RESTANTES proceso(s) relacionado(s) corriendo${NC}"
    echo -e "   Usa: ${CYAN}ps aux | grep -E 'python.*app.py|ngrok|auto_backup'${NC}"
    echo -e "   Para ver detalles y matar manualmente si es necesario"
else
    echo -e "${GREEN}✓ No hay procesos residuales${NC}"
fi

echo ""
echo -e "${BLUE}📁 Archivos de log:${NC}"
if [ -f flask.log ]; then
    echo -e "   flask.log        ($(du -h flask.log | cut -f1))"
fi
if [ -f ngrok.log ]; then
    echo -e "   ngrok.log        ($(du -h ngrok.log | cut -f1))"
fi
if [ -f auto_backup.log ]; then
    echo -e "   auto_backup.log  ($(du -h auto_backup.log | cut -f1))"
fi

echo ""
echo -e "${BLUE}💡 Comandos útiles:${NC}"
echo -e "   Reiniciar:       ${CYAN}./start.sh${NC}"
echo -e "   Ver backups:     ${CYAN}./ver_backups.sh${NC}"
echo -e "   Backup manual:   ${CYAN}./backup.sh${NC}"
echo -e "   Limpiar logs:    ${CYAN}rm -f *.log${NC}"

echo ""
echo -e "${CYAN}============================================================${NC}"

#!/bin/bash

# ============================================================
# AXION STORE - VISOR DE BACKUPS
# ============================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}   📦 AXION STORE - HISTORIAL DE BACKUPS${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

BACKUP_DIR="$HOME/axion_backups"

# ============================================================
# BACKUPS DISPONIBLES
# ============================================================
echo -e "${BLUE}📊 Backups disponibles:${NC}"
echo ""

if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR/*.sql 2>/dev/null)" ]; then
    # Mostrar últimos 10 backups
    echo -e "${GREEN}Últimos 10 backups:${NC}"
    echo ""
    ls -lht "$BACKUP_DIR"/axion_store_*.sql 2>/dev/null | head -10 | awk '{
        size = $5
        date = $6 " " $7 " " $8
        file = $9
        gsub(".*/", "", file)
        printf "  %s  %-10s  %s\n", date, size, file
    }'
    
    echo ""
    
    # Estadísticas
    TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/axion_store_*.sql 2>/dev/null | wc -l)
    ESPACIO_TOTAL=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    BACKUP_MAS_RECIENTE=$(ls -t "$BACKUP_DIR"/axion_store_*.sql 2>/dev/null | head -n1)
    
    echo -e "${BLUE}📈 Estadísticas:${NC}"
    echo -e "   Total de backups:    ${GREEN}$TOTAL_BACKUPS${NC}"
    echo -e "   Espacio utilizado:   ${GREEN}$ESPACIO_TOTAL${NC}"
    echo -e "   Directorio:          ${CYAN}$BACKUP_DIR${NC}"
    
    if [ ! -z "$BACKUP_MAS_RECIENTE" ]; then
        FECHA_RECIENTE=$(stat -c %y "$BACKUP_MAS_RECIENTE" 2>/dev/null | cut -d'.' -f1)
        TAMANO_RECIENTE=$(du -h "$BACKUP_MAS_RECIENTE" 2>/dev/null | cut -f1)
        echo -e "   Backup más reciente: ${GREEN}$(basename "$BACKUP_MAS_RECIENTE")${NC}"
        echo -e "   Fecha:               ${CYAN}$FECHA_RECIENTE${NC}"
        echo -e "   Tamaño:              ${CYAN}$TAMANO_RECIENTE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No hay backups disponibles en: $BACKUP_DIR${NC}"
    echo ""
    echo -e "${BLUE}💡 Para crear un backup:${NC}"
    echo -e "   ${CYAN}./backup.sh${NC}"
fi

echo ""

# ============================================================
# LOG DE BACKUPS AUTOMÁTICOS
# ============================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${BLUE}📝 Log de Backups Automáticos:${NC}"
echo ""

if [ -f auto_backup.log ]; then
    LINEAS_LOG=$(wc -l < auto_backup.log)
    
    if [ $LINEAS_LOG -gt 0 ]; then
        echo -e "${GREEN}Últimas 20 líneas del log:${NC}"
        echo ""
        tail -20 auto_backup.log | sed 's/^/  /'
        echo ""
        echo -e "${BLUE}Total de líneas en log: ${GREEN}$LINEAS_LOG${NC}"
    else
        echo -e "${YELLOW}El log está vacío${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No hay log de backups automáticos${NC}"
    echo ""
    echo -e "${BLUE}💡 El log se crea cuando:${NC}"
    echo -e "   1. Ejecutas ${CYAN}./start.sh${NC}"
    echo -e "   2. El servicio de auto-backup está activo"
fi

echo ""

# ============================================================
# OPCIONES RÁPIDAS
# ============================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${BLUE}💡 Comandos útiles:${NC}"
echo -e "   Crear backup:        ${CYAN}./backup.sh${NC}"
echo -e "   Ver último backup:   ${CYAN}ls -lh $BACKUP_DIR/axion_store_*.sql | tail -1${NC}"
echo -e "   Limpiar backups:     ${CYAN}rm $BACKUP_DIR/axion_store_*.sql${NC}"
echo -e "   Restaurar backup:    ${CYAN}mysql -u root -p321 axion_store < [archivo.sql]${NC}"
echo ""
echo -e "${CYAN}============================================================${NC}"

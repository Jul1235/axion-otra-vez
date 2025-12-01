#!/bin/bash

BACKUP_DIR="$HOME/axion_backups"
DATE=$(date +%Y%m%d_%H%M%S)
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Verificar si MariaDB está corriendo
if ! sudo systemctl is-active --quiet mariadb; then
    echo -e "${RED}✗ MariaDB no está corriendo${NC}"
    echo "Iniciando MariaDB..."
    sudo systemctl start mariadb
    sleep 2
    
    if ! sudo systemctl is-active --quiet mariadb; then
        echo -e "${RED}✗ No se pudo iniciar MariaDB${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ MariaDB iniciado${NC}"
fi

# Hacer backup
echo "Creando backup..."
mysqldump -u root -p'321' axion_store > "$BACKUP_DIR/axion_store_$DATE.sql" 2>/dev/null

# Verificar que el backup se creó correctamente
if [ -s "$BACKUP_DIR/axion_store_$DATE.sql" ]; then
    SIZE=$(du -h "$BACKUP_DIR/axion_store_$DATE.sql" | cut -f1)
    echo -e "${GREEN}✓ Backup creado: axion_store_$DATE.sql ($SIZE)${NC}"
else
    echo -e "${RED}✗ Error al crear el backup${NC}"
    rm "$BACKUP_DIR/axion_store_$DATE.sql" 2>/dev/null
    exit 1
fi

# Mantener solo los últimos 7 backups
cd $BACKUP_DIR
BACKUP_COUNT=$(ls -1 axion_store_*.sql 2>/dev/null | wc -l)
if [ $BACKUP_COUNT -gt 7 ]; then
    ls -t axion_store_*.sql | tail -n +8 | xargs -r rm
    echo -e "${GREEN}✓ Backups antiguos limpiados (manteniendo últimos 7)${NC}"
fi

echo ""
echo "Backups disponibles:"
ls -lh axion_store_*.sql 2>/dev/null | tail -7

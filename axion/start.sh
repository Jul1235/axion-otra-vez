#!/bin/bash

# ============================================================
# AXION STORE - SCRIPT DE INICIO COMPLETO
# ============================================================

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuración
PROYECTO_DIR="/home/user/Descargas/axion"
DB_USER="root"
DB_PASS="321"
DB_NAME="axion_store"

# Banner
clear
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}   ⚡ AXION STORE - SISTEMA DE INICIO AUTOMÁTICO ⚡${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

cd "$PROYECTO_DIR" || exit 1

# ============================================================
# [1/7] VERIFICAR MARIADB
# ============================================================
echo -e "${GREEN}[1/7] Verificando MariaDB...${NC}"
if sudo systemctl is-active --quiet mariadb; then
    echo "✓ MariaDB está corriendo"
else
    echo "  Iniciando MariaDB..."
    sudo systemctl start mariadb
    if [ $? -eq 0 ]; then
        echo "✓ MariaDB iniciado correctamente"
    else
        echo -e "${RED}✗ Error al iniciar MariaDB${NC}"
        exit 1
    fi
fi
echo ""

# ============================================================
# [2/7] BACKUP AUTOMÁTICO
# ============================================================
echo -e "${GREEN}[2/7] Creando backup automático...${NC}"
if [ -f backup.sh ]; then
    ./backup.sh
    if [ $? -eq 0 ]; then
        echo "✓ Backup creado exitosamente"
    else
        echo -e "${YELLOW}⚠ Advertencia: Error en backup (continuando...)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ backup.sh no encontrado (saltando)${NC}"
fi
echo ""

# ============================================================
# [3/7] ACTIVAR ENTORNO VIRTUAL
# ============================================================
echo -e "${GREEN}[3/7] Activando entorno virtual...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ No existe el entorno virtual${NC}"
    echo "  Créalo con: python3 -m venv venv"
    echo "  Luego instala dependencias: pip install -r requirements.txt"
    exit 1
fi
source venv/bin/activate
echo "✓ Entorno virtual activado"
echo ""

# ============================================================
# [4/7] DETECTAR E IMPORTAR CSV
# ============================================================
echo -e "${GREEN}[4/7] Detectando archivos CSV...${NC}"

# Lista de tablas válidas
TABLAS=("users" "producto" "productos" "wallet" "carrito" "pedido" "detalle_pedido" "historial_carrito" "transacciones_wallet")

CSV_ENCONTRADOS=()

# Buscar archivos CSV
for tabla in "${TABLAS[@]}"; do
    for archivo in "$PROYECTO_DIR"/*.csv; do
        if [ -f "$archivo" ]; then
            nombre_archivo=$(basename "$archivo" .csv)
            nombre_archivo_lower=$(echo "$nombre_archivo" | tr '[:upper:]' '[:lower:]')
            
            if [[ "$nombre_archivo_lower" == "$tabla" ]] || [[ "$nombre_archivo_lower" == "${tabla}s" ]]; then
                CSV_ENCONTRADOS+=("$archivo:$tabla")
                echo -e "  ${CYAN}→${NC} Encontrado: ${YELLOW}$(basename "$archivo")${NC} (tabla: ${tabla})"
            fi
        fi
    done
done

if [ ${#CSV_ENCONTRADOS[@]} -eq 0 ]; then
    echo -e "  ${BLUE}ℹ  No se encontraron archivos CSV para importar${NC}"
    echo ""
else
    echo ""
    echo -e "${YELLOW}📊 Archivos CSV encontrados: ${#CSV_ENCONTRADOS[@]}${NC}"
    echo -e "${YELLOW}¿Deseas importar estos archivos a la base de datos?${NC}"
    echo -n -e "${CYAN}Opciones: ${NC}[${GREEN}S${NC}]í / [${RED}N${NC}]o / [${YELLOW}I${NC}]ndividual: "
    read -r respuesta
    echo ""
    
    importar_csv() {
        local archivo=$1
        local tabla=$2
        
        echo -e "${CYAN}  📥 Importando $(basename "$archivo") → $tabla${NC}"
        
        case $tabla in
            "producto"|"productos")
                if [ -f "importar_productos.py" ]; then
                    python3 importar_productos.py "$archivo" 2>&1 | sed 's/^/     /'
                else
                    python3 -c "
import csv, pymysql
conexion = pymysql.connect(host='localhost', user='$DB_USER', password='$DB_PASS', database='$DB_NAME', charset='utf8mb4')
cursor = conexion.cursor()
with open('$archivo', 'r', encoding='utf-8') as f:
    lector = csv.DictReader(f)
    count = 0
    for fila in lector:
        sql = '''INSERT INTO producto (ID_Producto, nombre, precio, imagen, disponible, stock)
                 VALUES (%s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), precio=VALUES(precio), 
                 imagen=VALUES(imagen), disponible=VALUES(disponible), stock=VALUES(stock)'''
        cursor.execute(sql, (fila['id'], fila['nombre'], float(fila['precio']), 
                           fila['imagen'], 1 if fila['disponible'].lower() in ['true','1'] else 0, 
                           int(fila['stock'])))
        count += 1
conexion.commit()
cursor.execute('SELECT COUNT(*) FROM producto')
total = cursor.fetchone()[0]
print(f'     ✓ {count} productos procesados. Total en BD: {total}')
cursor.close()
conexion.close()
" 2>&1
                fi
                ;;
                
            "users")
                python3 -c "
import csv, pymysql
from werkzeug.security import generate_password_hash
conexion = pymysql.connect(host='localhost', user='$DB_USER', password='$DB_PASS', database='$DB_NAME', charset='utf8mb4')
cursor = conexion.cursor()
count = 0
with open('$archivo', 'r', encoding='utf-8') as f:
    lector = csv.DictReader(f)
    for fila in lector:
        password_hash = generate_password_hash(fila.get('password', '123456'))
        sql = '''INSERT INTO users (ID_Users, nombre, email, password, es_admin)
                 VALUES (%s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), email=VALUES(email)'''
        cursor.execute(sql, (fila.get('id'), fila['nombre'], fila['email'], 
                           password_hash, 1 if fila.get('es_admin','0')=='1' else 0))
        count += 1
        # Crear wallet si no existe
        cursor.execute('INSERT IGNORE INTO wallet (ID_Users, saldo) VALUES (%s, 50.0)', (fila.get('id'),))
conexion.commit()
print(f'     ✓ {count} usuarios procesados')
cursor.close()
conexion.close()
" 2>&1
                ;;
                
            *)
                echo -e "     ${YELLOW}⚠ No hay script para: $tabla (saltando)${NC}"
                ;;
        esac
        echo ""
    }
    
    case $respuesta in
        [Ss]*)
            echo -e "${GREEN}✓ Importando TODOS los archivos...${NC}"
            echo ""
            for item in "${CSV_ENCONTRADOS[@]}"; do
                IFS=':' read -r archivo tabla <<< "$item"
                importar_csv "$archivo" "$tabla"
            done
            ;;
        [Ii]*)
            echo -e "${CYAN}Modo individual activado${NC}"
            echo ""
            for item in "${CSV_ENCONTRADOS[@]}"; do
                IFS=':' read -r archivo tabla <<< "$item"
                echo -n -e "${YELLOW}¿Importar $(basename "$archivo") → $tabla?${NC} (s/N): "
                read -r respuesta_individual
                if [[ $respuesta_individual =~ ^[Ss]$ ]]; then
                    importar_csv "$archivo" "$tabla"
                else
                    echo -e "  ${BLUE}Saltando $(basename "$archivo")${NC}"
                    echo ""
                fi
            done
            ;;
        *)
            echo -e "${BLUE}✓ Importación omitida${NC}"
            echo ""
            ;;
    esac
fi

# ============================================================
# [5/7] INICIAR FLASK
# ============================================================
echo -e "${GREEN}[5/7] Iniciando Flask en puerto 5000...${NC}"

# Limpiar logs antiguos
> flask.log

# Iniciar Flask en background
python3 app.py > flask.log 2>&1 &
FLASK_PID=$!
echo $FLASK_PID > .flask.pid
echo "✓ Flask corriendo (PID: $FLASK_PID)"

# Esperar a que Flask inicie
echo "  Esperando que Flask inicie..."
sleep 3

# Verificar que Flask está corriendo
if curl -s http://localhost:5000 > /dev/null; then
    echo "✓ Flask responde correctamente"
else
    echo -e "${RED}✗ Flask no responde, revisa flask.log${NC}"
    echo "  Ver logs: tail -f flask.log"
fi
echo ""

# ============================================================
# [6/7] INICIAR NGROK
# ============================================================
echo -e "${GREEN}[6/7] Iniciando ngrok...${NC}"
if command -v ngrok &> /dev/null; then
    # Limpiar logs antiguos
    > ngrok.log
    
    # Iniciar ngrok en background
    ngrok http 5000 > ngrok.log 2>&1 &
    NGROK_PID=$!
    echo $NGROK_PID > .ngrok.pid
    echo "✓ Ngrok corriendo (PID: $NGROK_PID)"
    
    # Esperar a que ngrok inicie
    sleep 2
    
    # Intentar obtener URL pública
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[^"]*\.ngrok-free\.app' | head -n1)
    
    if [ ! -z "$NGROK_URL" ]; then
        echo "✓ URL pública: $NGROK_URL"
    fi
else
    echo -e "${YELLOW}⚠ ngrok no encontrado (continuando sin túnel público)${NC}"
    echo "  Instálalo desde: https://ngrok.com/download"
    NGROK_PID=""
fi
echo ""

# ============================================================
# [7/7] SERVICIO DE BACKUP AUTOMÁTICO
# ============================================================
echo -e "${GREEN}[7/7] Iniciando servicio de backup automático...${NC}"
if [ -f auto_backup.sh ]; then
    ./auto_backup.sh &
    AUTO_BACKUP_PID=$!
    echo $AUTO_BACKUP_PID > .auto_backup.pid
    echo "✓ Backup automático activo (PID: $AUTO_BACKUP_PID)"
    echo "  Frecuencia: Cada 2 horas"
else
    echo -e "${YELLOW}⚠ auto_backup.sh no encontrado (saltando)${NC}"
    AUTO_BACKUP_PID=""
fi
echo ""

# ============================================================
# RESUMEN FINAL
# ============================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}   ✅ SERVIDOR AXION STORE ACTIVO${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "${BLUE}🌐 URLs de acceso:${NC}"
echo -e "   Local:        ${GREEN}http://localhost:5000${NC}"
if [ ! -z "$NGROK_URL" ]; then
    echo -e "   Público:      ${GREEN}$NGROK_URL${NC}"
fi
echo -e "   Ngrok Panel:  ${GREEN}http://localhost:4040${NC}"
echo ""
echo -e "${BLUE}🔐 Credenciales de administrador:${NC}"
echo -e "   Email:    ${CYAN}admin@axionstore.com${NC}"
echo -e "   Password: ${CYAN}admin123${NC}"
echo ""
echo -e "${BLUE}📊 Procesos activos:${NC}"
echo -e "   Flask:          PID ${FLASK_PID}"
if [ ! -z "$NGROK_PID" ]; then
    echo -e "   Ngrok:          PID ${NGROK_PID}"
fi
if [ ! -z "$AUTO_BACKUP_PID" ]; then
    echo -e "   Auto Backup:    PID ${AUTO_BACKUP_PID}"
fi
echo ""
echo -e "${BLUE}📋 Comandos útiles:${NC}"
echo -e "   Ver logs Flask:  ${YELLOW}tail -f flask.log${NC}"
echo -e "   Detener todo:    ${YELLOW}./stop.sh${NC}"
echo -e "   Backup manual:   ${YELLOW}./backup.sh${NC}"
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}Presiona Ctrl+C para detener (o usa ./stop.sh)${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Mantener el script corriendo
wait $FLASK_PID

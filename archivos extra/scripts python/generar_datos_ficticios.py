#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════
GENERADOR DE DATOS FICTICIOS REALISTAS PARA AXION STORE
════════════════════════════════════════════════════════════════════════════
Base de Datos: axion_est (estadísticas - separada de producción)
Generador: 100 usuarios con patrones de compra asimétricos
Distribución: Pareto, Beta, Normal (estadísticamente realista)
Autor: Sistema de Generación Automática
Versión: 2.0
════════════════════════════════════════════════════════════════════════════
"""

import pymysql
import random
import string
from datetime import datetime, timedelta
from faker import Faker
import numpy as np
from tqdm import tqdm
from werkzeug.security import generate_password_hash
from io import StringIO

# ==========================================
# CONFIGURACIÓN GLOBAL
# ==========================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '321',
    'charset': 'utf8mb4'
}

DB_NAME = 'axion_est'
NUMERO_USUARIOS = 100
FECHA_INICIO = datetime(2024, 1, 1)
FECHA_FIN = datetime.now()

fake = Faker(['es_ES', 'es_MX'])
np.random.seed(42)  # Reproducibilidad

# ==========================================
# DATOS DE PRODUCTOS POR CATEGORÍA
# ==========================================

CATEGORIAS_SUBCATEGORIAS = {
    "Procesadores (CPUs)": [
        {"nombre": "Procesador Intel Core i9-14900K", "precio": 589.99, "stock": 15},
        {"nombre": "Procesador Intel Core i7-13700K", "precio": 419.99, "stock": 25},
        {"nombre": "Procesador Intel Core i5-13400F", "precio": 219.99, "stock": 40},
        {"nombre": "Procesador Intel Core i3-12100F", "precio": 109.99, "stock": 50},
        {"nombre": "Procesador Intel Core i5-12600K", "precio": 249.99, "stock": 30},
        {"nombre": "Procesador AMD Ryzen 9 7950X", "precio": 699.99, "stock": 12},
        {"nombre": "Procesador AMD Ryzen 7 7800X3D", "precio": 449.99, "stock": 20},
        {"nombre": "Procesador AMD Ryzen 5 7600X", "precio": 229.99, "stock": 35},
        {"nombre": "Procesador AMD Ryzen 7 5800X", "precio": 289.99, "stock": 28},
        {"nombre": "Procesador AMD Ryzen 5 5600G", "precio": 159.99, "stock": 45}
    ],
    "Tarjetas Madre (Motherboards)": [
        {"nombre": "ASUS ROG Strix Z790-E Gaming WiFi", "precio": 499.99, "stock": 18},
        {"nombre": "ASUS TUF Gaming B760-PLUS WiFi", "precio": 219.99, "stock": 30},
        {"nombre": "Gigabyte Z690 AORUS Elite AX", "precio": 329.99, "stock": 22},
        {"nombre": "Gigabyte B660M DS3H AX DDR4", "precio": 139.99, "stock": 40},
        {"nombre": "MSI MPG Z790 Carbon WiFi", "precio": 459.99, "stock": 15},
        {"nombre": "MSI MAG B550 Tomahawk Max WiFi", "precio": 189.99, "stock": 35},
        {"nombre": "ASUS Prime H610M-E D4", "precio": 99.99, "stock": 50},
        {"nombre": "ASRock B550M Steel Legend", "precio": 149.99, "stock": 38},
        {"nombre": "Gigabyte X670E AORUS Master", "precio": 549.99, "stock": 10},
        {"nombre": "MSI PRO B650M-A WiFi", "precio": 179.99, "stock": 32}
    ],
    "Memoria RAM": [
        {"nombre": "Corsair Vengeance RGB Pro 32GB (2x16GB) DDR4 3200MHz", "precio": 129.99, "stock": 45},
        {"nombre": "Corsair Vengeance LPX 16GB (2x8GB) DDR4 3200MHz", "precio": 59.99, "stock": 60},
        {"nombre": "Kingston Fury Beast RGB 16GB (2x8GB) DDR4 3200MHz", "precio": 64.99, "stock": 55},
        {"nombre": "Kingston Fury Renegade 32GB (2x16GB) DDR5 6000MHz", "precio": 189.99, "stock": 30},
        {"nombre": "G.Skill Trident Z5 RGB 32GB (2x16GB) DDR5 6400MHz", "precio": 209.99, "stock": 25},
        {"nombre": "G.Skill Ripjaws V 16GB (2x8GB) DDR4 3600MHz", "precio": 69.99, "stock": 50},
        {"nombre": "TeamGroup T-Force Delta RGB 16GB (2x8GB) DDR4 3200MHz", "precio": 62.99, "stock": 48},
        {"nombre": "Adata XPG Spectrix D50 16GB (2x8GB) DDR4 3200MHz", "precio": 67.99, "stock": 42},
        {"nombre": "Crucial RAM 8GB DDR4 2666MHz", "precio": 29.99, "stock": 70},
        {"nombre": "Corsair Dominator Platinum RGB 32GB (2x16GB) DDR5 5600MHz", "precio": 229.99, "stock": 20}
    ],
    "Tarjetas Gráficas (GPUs)": [
        {"nombre": "ASUS ROG Strix GeForce RTX 4090 24GB OC", "precio": 1899.99, "stock": 5},
        {"nombre": "MSI Gaming X Trio GeForce RTX 4080 16GB", "precio": 1299.99, "stock": 8},
        {"nombre": "Gigabyte GeForce RTX 4070 Ti Eagle OC 12GB", "precio": 849.99, "stock": 12},
        {"nombre": "ASUS Dual GeForce RTX 4060 8GB", "precio": 329.99, "stock": 25},
        {"nombre": "Zotac Gaming GeForce RTX 3060 Twin Edge 12GB", "precio": 299.99, "stock": 30},
        {"nombre": "AMD Radeon RX 7900 XTX 24GB", "precio": 1099.99, "stock": 10},
        {"nombre": "Sapphire Pulse AMD Radeon RX 7800 XT 16GB", "precio": 599.99, "stock": 18},
        {"nombre": "XFX Speedster SWFT 210 Radeon RX 6600 8GB", "precio": 239.99, "stock": 28},
        {"nombre": "MSI Ventus 2X GeForce RTX 3050 8GB", "precio": 259.99, "stock": 35},
        {"nombre": "Gigabyte GeForce GTX 1650 D6 OC 4GB", "precio": 179.99, "stock": 40}
    ],
    "Almacenamiento (SSD/HDD)": [
        {"nombre": "Samsung 990 PRO 2TB PCIe 4.0 NVMe M.2", "precio": 199.99, "stock": 35},
        {"nombre": "Samsung 980 PRO 1TB PCIe 4.0 NVMe M.2", "precio": 119.99, "stock": 45},
        {"nombre": "Kingston NV2 1TB PCIe 4.0 NVMe M.2", "precio": 79.99, "stock": 60},
        {"nombre": "WD Black SN850X 2TB PCIe 4.0 NVMe M.2", "precio": 189.99, "stock": 30},
        {"nombre": "Crucial P3 Plus 1TB PCIe 4.0 NVMe M.2", "precio": 84.99, "stock": 55},
        {"nombre": "WD Blue SA510 500GB SATA SSD 2.5\"", "precio": 49.99, "stock": 65},
        {"nombre": "Kingston A400 480GB SATA SSD 2.5\"", "precio": 44.99, "stock": 70},
        {"nombre": "Seagate Barracuda 2TB HDD 7200RPM", "precio": 59.99, "stock": 50},
        {"nombre": "WD Blue 4TB HDD 5400RPM", "precio": 89.99, "stock": 45},
        {"nombre": "Adata XPG Gammix S70 Blade 1TB NVMe", "precio": 109.99, "stock": 38}
    ],
    "Fuentes de Poder (PSU)": [
        {"nombre": "Corsair RM850x 850W 80 Plus Gold Modular", "precio": 149.99, "stock": 28},
        {"nombre": "Corsair RM750e 750W 80 Plus Gold Modular", "precio": 119.99, "stock": 35},
        {"nombre": "EVGA SuperNOVA 850 GT 850W 80 Plus Gold", "precio": 139.99, "stock": 30},
        {"nombre": "EVGA 600 W1, 600W 80 Plus White", "precio": 49.99, "stock": 60},
        {"nombre": "Thermaltake Toughpower GF1 750W 80 Plus Gold", "precio": 129.99, "stock": 32},
        {"nombre": "ASUS ROG Thor 1000W Platinum II", "precio": 299.99, "stock": 12},
        {"nombre": "MSI MPG A850G PCIE5 850W Gold", "precio": 159.99, "stock": 25},
        {"nombre": "Cooler Master MWE Gold 850 V2 Full Modular", "precio": 134.99, "stock": 28},
        {"nombre": "Gigabyte UD750GM 750W 80 Plus Gold", "precio": 109.99, "stock": 38},
        {"nombre": "Seasonic Focus GX-750 750W 80 Plus Gold", "precio": 124.99, "stock": 30}
    ],
    "Gabinetes (Cases)": [
        {"nombre": "NZXT H9 Flow Dual-Chamber Mid-Tower", "precio": 159.99, "stock": 20},
        {"nombre": "NZXT H5 Flow Compact Mid-Tower", "precio": 89.99, "stock": 35},
        {"nombre": "Corsair 4000D Airflow Tempered Glass Mid-Tower", "precio": 104.99, "stock": 40},
        {"nombre": "Corsair 5000D Airflow Mid-Tower", "precio": 159.99, "stock": 25},
        {"nombre": "Lian Li O11 Dynamic EVO Mid-Tower", "precio": 179.99, "stock": 18},
        {"nombre": "Lian Li Lancool 216 RGB Mid-Tower", "precio": 124.99, "stock": 30},
        {"nombre": "Hyte Y60 Dual Chamber Mid-Tower", "precio": 189.99, "stock": 15},
        {"nombre": "Cooler Master MasterBox Q300L Mini-Tower", "precio": 49.99, "stock": 50},
        {"nombre": "Phanteks Eclipse G360A Mid-Tower", "precio": 109.99, "stock": 32},
        {"nombre": "DeepCool CH560 Digital Mid-Tower", "precio": 94.99, "stock": 38}
    ],
    "Refrigeración (Cooling)": [
        {"nombre": "Cooler Master Hyper 212 Halo Black", "precio": 44.99, "stock": 55},
        {"nombre": "DeepCool AK620 Zero Dark", "precio": 64.99, "stock": 45},
        {"nombre": "DeepCool AK400 Digital", "precio": 39.99, "stock": 60},
        {"nombre": "NZXT Kraken Elite 360 RGB AIO Liquid Cooler", "precio": 289.99, "stock": 15},
        {"nombre": "Corsair iCUE H150i Elite LCD XT Liquid Cooler", "precio": 279.99, "stock": 18},
        {"nombre": "Arctic Liquid Freezer III 360 AIO", "precio": 149.99, "stock": 25},
        {"nombre": "Noctua NH-D15 Chromax.Black", "precio": 109.99, "stock": 30},
        {"nombre": "Thermalright Peerless Assassin 120 SE", "precio": 39.99, "stock": 50},
        {"nombre": "Kit 3 Ventiladores Corsair iCUE SP120 RGB Elite", "precio": 59.99, "stock": 45},
        {"nombre": "Kit 3 Ventiladores Lian Li Uni Fan SL120 V2", "precio": 79.99, "stock": 35}
    ],
    "Monitores": [
        {"nombre": "Monitor LG UltraGear 27\" QHD 144Hz IPS (27GN800-B)", "precio": 349.99, "stock": 22},
        {"nombre": "Monitor Samsung Odyssey G5 32\" Curvo WQHD 165Hz", "precio": 399.99, "stock": 18},
        {"nombre": "Monitor ASUS TUF Gaming 24\" FHD 165Hz (VG249Q1A)", "precio": 179.99, "stock": 35},
        {"nombre": "Monitor Dell Alienware 34\" QD-OLED Curvo (AW3423DWF)", "precio": 1099.99, "stock": 8},
        {"nombre": "Monitor AOC 24\" FHD 144Hz (G2490VX)", "precio": 149.99, "stock": 40}
    ],
    "Periféricos": [
        {"nombre": "Mouse Logitech G502 HERO High Performance", "precio": 49.99, "stock": 65},
        {"nombre": "Mouse Razer DeathAdder V3 Pro Wireless", "precio": 149.99, "stock": 30},
        {"nombre": "Teclado Mecánico Logitech G915 TKL Wireless", "precio": 229.99, "stock": 20},
        {"nombre": "Teclado Mecánico Razer BlackWidow V4 Pro", "precio": 229.99, "stock": 22},
        {"nombre": "Audífonos HyperX Cloud II Wireless", "precio": 149.99, "stock": 35}
    ]
}

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def generar_fecha_aleatoria(inicio, fin):
    """Genera fecha aleatoria entre dos fechas"""
    delta = fin - inicio
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    return inicio + timedelta(days=random_days, seconds=random_seconds)

def generar_email_unico(nombre, emails_existentes):
    """Genera email único basado en el nombre"""
    base = fake.user_name()
    email = f"{base}@{fake.free_email_domain()}"

    contador = 1
    while email in emails_existentes:
        email = f"{base}{contador}@{fake.free_email_domain()}"
        contador += 1

    return email

# ==========================================
# CONEXIÓN Y CREACIÓN DE BASE DE DATOS
# ==========================================

def crear_base_datos():
    """Crea la base de datos axion_est si no existe"""
    print(f"\n🗄️  Creando base de datos '{DB_NAME}'...")

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

    conn.close()
    print(f"✅ Base de datos '{DB_NAME}' creada")

def crear_estructura_tablas():
    """Crea todas las tablas necesarias"""
    print("\n📋 Creando estructura de tablas...")

    config = DB_CONFIG.copy()
    config['database'] = DB_NAME

    conn = pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()

    # Tabla users
    cursor.execute("""
        CREATE TABLE users (
            ID_Users INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            es_admin BOOLEAN DEFAULT FALSE,

            total_compras INT DEFAULT 0,
            total_gastado FLOAT DEFAULT 0.0,
            ticket_promedio FLOAT DEFAULT 0.0,
            ultimo_pedido_fecha DATETIME,
            dias_desde_ultima_compra INT,

            total_recargas INT DEFAULT 0,
            dinero_recargado_total FLOAT DEFAULT 0.0,
            recarga_promedio FLOAT DEFAULT 0.0,
            ultima_recarga_fecha DATETIME,

            productos_carrito_actual INT DEFAULT 0,
            valor_carrito_actual FLOAT DEFAULT 0.0,
            productos_agregados_carrito_total INT DEFAULT 0,
            carritos_abandonados INT DEFAULT 0,

            tasa_conversion FLOAT DEFAULT 0.0,
            segmento_cliente VARCHAR(50) DEFAULT 'nuevo',
            ultima_actividad DATETIME DEFAULT CURRENT_TIMESTAMP,

            INDEX idx_email (email),
            INDEX idx_segmento (segmento_cliente)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla categoria
    cursor.execute("""
        CREATE TABLE categoria (
            ID_Categoria INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) UNIQUE NOT NULL,
            descripcion TEXT,
            icono VARCHAR(50),
            activa BOOLEAN DEFAULT TRUE,
            orden INT DEFAULT 0,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

            INDEX idx_nombre (nombre),
            INDEX idx_activa_orden (activa, orden)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla subcategoria
    cursor.execute("""
        CREATE TABLE subcategoria (
            ID_Subcategoria INT AUTO_INCREMENT PRIMARY KEY,
            ID_Categoria INT NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            activa BOOLEAN DEFAULT TRUE,
            orden INT DEFAULT 0,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (ID_Categoria) REFERENCES categoria(ID_Categoria) ON DELETE CASCADE,
            INDEX idx_categoria (ID_Categoria),
            INDEX idx_activa (activa)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla producto
    cursor.execute("""
        CREATE TABLE producto (
            ID_Producto INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(200) NOT NULL,
            precio FLOAT NOT NULL,
            imagen VARCHAR(300),
            disponible BOOLEAN DEFAULT TRUE,
            stock INT DEFAULT 0,
            ID_Categoria INT,
            ID_Subcategoria INT,

            FOREIGN KEY (ID_Categoria) REFERENCES categoria(ID_Categoria) ON DELETE SET NULL,
            FOREIGN KEY (ID_Subcategoria) REFERENCES subcategoria(ID_Subcategoria) ON DELETE SET NULL,
            INDEX idx_nombre (nombre),
            INDEX idx_categoria (ID_Categoria),
            INDEX idx_subcategoria (ID_Subcategoria)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla wallet
    cursor.execute("""
        CREATE TABLE wallet (
            ID_Wallet INT AUTO_INCREMENT PRIMARY KEY,
            ID_Users INT NOT NULL,
            saldo FLOAT DEFAULT 50.0,

            FOREIGN KEY (ID_Users) REFERENCES users(ID_Users) ON DELETE CASCADE,
            INDEX idx_user (ID_Users)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla carrito
    cursor.execute("""
        CREATE TABLE carrito (
            ID_Carrito INT AUTO_INCREMENT PRIMARY KEY,
            ID_Users INT NOT NULL,
            ID_Producto INT NOT NULL,
            cantidad INT DEFAULT 1,

            FOREIGN KEY (ID_Users) REFERENCES users(ID_Users) ON DELETE CASCADE,
            FOREIGN KEY (ID_Producto) REFERENCES producto(ID_Producto) ON DELETE CASCADE,
            INDEX idx_user (ID_Users),
            INDEX idx_producto (ID_Producto)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla pedido
    cursor.execute("""
        CREATE TABLE pedido (
            ID_Pedido INT AUTO_INCREMENT PRIMARY KEY,
            ID_Users INT NOT NULL,
            total FLOAT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            estado VARCHAR(20) DEFAULT 'pagado',

            FOREIGN KEY (ID_Users) REFERENCES users(ID_Users) ON DELETE CASCADE,
            INDEX idx_user (ID_Users),
            INDEX idx_fecha (fecha)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla detalle_pedido
    cursor.execute("""
        CREATE TABLE detalle_pedido (
            ID_Detalle_Pedido INT AUTO_INCREMENT PRIMARY KEY,
            ID_Pedido INT NOT NULL,
            ID_Producto INT NOT NULL,
            cantidad INT NOT NULL,
            precio_unitario FLOAT NOT NULL,

            FOREIGN KEY (ID_Pedido) REFERENCES pedido(ID_Pedido) ON DELETE CASCADE,
            FOREIGN KEY (ID_Producto) REFERENCES producto(ID_Producto) ON DELETE CASCADE,
            INDEX idx_pedido (ID_Pedido),
            INDEX idx_producto (ID_Producto)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla historial_carrito
    cursor.execute("""
        CREATE TABLE historial_carrito (
            ID_Historial INT AUTO_INCREMENT PRIMARY KEY,
            ID_Users INT NOT NULL,
            ID_Producto INT NOT NULL,
            accion VARCHAR(20) NOT NULL,
            cantidad INT NOT NULL,
            precio_momento FLOAT NOT NULL,
            valor_total FLOAT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            ID_Pedido INT,

            FOREIGN KEY (ID_Users) REFERENCES users(ID_Users) ON DELETE CASCADE,
            FOREIGN KEY (ID_Producto) REFERENCES producto(ID_Producto) ON DELETE CASCADE,
            FOREIGN KEY (ID_Pedido) REFERENCES pedido(ID_Pedido) ON DELETE SET NULL,
            INDEX idx_user_accion (ID_Users, accion),
            INDEX idx_fecha (fecha)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla transacciones_wallet
    cursor.execute("""
        CREATE TABLE transacciones_wallet (
            ID_Transaccion INT AUTO_INCREMENT PRIMARY KEY,
            ID_Wallet INT NOT NULL,
            ID_Users INT NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            monto FLOAT NOT NULL,
            saldo_anterior FLOAT NOT NULL,
            saldo_nuevo FLOAT NOT NULL,
            descripcion VARCHAR(200),
            ID_Pedido INT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (ID_Wallet) REFERENCES wallet(ID_Wallet) ON DELETE CASCADE,
            FOREIGN KEY (ID_Users) REFERENCES users(ID_Users) ON DELETE CASCADE,
            FOREIGN KEY (ID_Pedido) REFERENCES pedido(ID_Pedido) ON DELETE SET NULL,
            INDEX idx_user_tipo (ID_Users, tipo),
            INDEX idx_fecha (fecha)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla metricas_categoria
    cursor.execute("""
        CREATE TABLE metricas_categoria (
            ID_Metrica INT AUTO_INCREMENT PRIMARY KEY,
            ID_Categoria INT NOT NULL UNIQUE,

            total_productos_vendidos INT DEFAULT 0,
            total_pedidos INT DEFAULT 0,
            ingresos_totales FLOAT DEFAULT 0.0,
            ticket_promedio FLOAT DEFAULT 0.0,

            total_agregados_carrito INT DEFAULT 0,
            total_abandonos INT DEFAULT 0,
            valor_abandonos FLOAT DEFAULT 0.0,

            tasa_conversion FLOAT DEFAULT 0.0,

            productos_activos INT DEFAULT 0,
            productos_sin_stock INT DEFAULT 0,

            ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            FOREIGN KEY (ID_Categoria) REFERENCES categoria(ID_Categoria) ON DELETE CASCADE,
            INDEX idx_categoria (ID_Categoria)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Tabla metricas_subcategoria
    cursor.execute("""
        CREATE TABLE metricas_subcategoria (
            ID_Metrica INT AUTO_INCREMENT PRIMARY KEY,
            ID_Subcategoria INT NOT NULL UNIQUE,
            ID_Categoria INT NOT NULL,

            total_productos_vendidos INT DEFAULT 0,
            total_pedidos INT DEFAULT 0,
            ingresos_totales FLOAT DEFAULT 0.0,
            ticket_promedio FLOAT DEFAULT 0.0,

            total_agregados_carrito INT DEFAULT 0,
            total_abandonos INT DEFAULT 0,
            valor_abandonos FLOAT DEFAULT 0.0,

            tasa_conversion FLOAT DEFAULT 0.0,

            productos_activos INT DEFAULT 0,
            productos_sin_stock INT DEFAULT 0,

            ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            FOREIGN KEY (ID_Subcategoria) REFERENCES subcategoria(ID_Subcategoria) ON DELETE CASCADE,
            FOREIGN KEY (ID_Categoria) REFERENCES categoria(ID_Categoria) ON DELETE CASCADE,
            INDEX idx_subcategoria (ID_Subcategoria),
            INDEX idx_categoria (ID_Categoria)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    conn.commit()
    conn.close()

    print("✅ Estructura de tablas creada")

def obtener_conexion():
    """Crea conexión a la BD axion_est"""
    config = DB_CONFIG.copy()
    config['database'] = DB_NAME
    return pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)

# ==========================================
# INSERCIÓN DE DATOS
# ==========================================

def insertar_categorias_y_productos(conn):
    """Inserta categorías, subcategorías y productos"""
    print("\n📦 Insertando categorías, subcategorías y productos...")

    cursor = conn.cursor()

    categorias_ids = {}
    subcategorias_ids = {}
    productos_ids = []

    orden_categoria = 0

    for categoria_nombre, productos in CATEGORIAS_SUBCATEGORIAS.items():
        cursor.execute("""
            INSERT INTO categoria (nombre, descripcion, icono, activa, orden, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            categoria_nombre,
            f"Productos de {categoria_nombre}",
            "fa-microchip" if "Procesadores" in categoria_nombre else
            "fa-memory" if "RAM" in categoria_nombre else
            "fa-hdd" if "Almacenamiento" in categoria_nombre else
            "fa-bolt" if "Fuentes" in categoria_nombre else
            "fa-desktop" if "Monitores" in categoria_nombre else
            "fa-cube",
            True,
            orden_categoria,
            FECHA_INICIO
        ))

        categoria_id = cursor.lastrowid
        categorias_ids[categoria_nombre] = categoria_id

        cursor.execute("""
            INSERT INTO subcategoria (ID_Categoria, nombre, descripcion, activa, orden, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            categoria_id,
            f"{categoria_nombre} - General",
            f"Subcategoría general de {categoria_nombre}",
            True,
            0,
            FECHA_INICIO
        ))

        subcategoria_id = cursor.lastrowid
        subcategorias_ids[categoria_nombre] = subcategoria_id

        for producto_data in productos:
            cursor.execute("""
                INSERT INTO producto (nombre, precio, imagen, disponible, stock, ID_Categoria, ID_Subcategoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                producto_data['nombre'],
                producto_data['precio'],
                'img/default-product.png',
                True,
                producto_data['stock'],
                categoria_id,
                subcategoria_id
            ))

            productos_ids.append(cursor.lastrowid)

        # Crear métricas de categoría
        cursor.execute("""
            INSERT INTO metricas_categoria (ID_Categoria) VALUES (%s)
        """, (categoria_id,))

        # Crear métricas de subcategoría
        cursor.execute("""
            INSERT INTO metricas_subcategoria (ID_Subcategoria, ID_Categoria) VALUES (%s, %s)
        """, (subcategoria_id, categoria_id))

        orden_categoria += 1

    conn.commit()
    print(f"✅ {len(categorias_ids)} categorías | {len(subcategorias_ids)} subcategorías | {len(productos_ids)} productos")

    return categorias_ids, subcategorias_ids, productos_ids

def insertar_usuarios(conn):
    """Inserta 100 usuarios con datos realistas"""
    print("\n👥 Generando 100 usuarios...")

    cursor = conn.cursor()
    usuarios_ids = []
    emails_existentes = set()

    # Distribución de segmentos (asimétrica)
    segmentos = (
        ['nuevo'] * 40 +      # 40% nuevos (poca actividad)
        ['activo'] * 35 +     # 35% activos (actividad media)
        ['vip'] * 15 +        # 15% VIP (alta actividad)
        ['inactivo'] * 10     # 10% inactivos
    )
    random.shuffle(segmentos)

    for i in tqdm(range(NUMERO_USUARIOS), desc="Creando usuarios"):
        nombre = fake.name()
        email = generar_email_unico(nombre, emails_existentes)
        emails_existentes.add(email)

        password_hash = generate_password_hash("password123", method='pbkdf2:sha256')

        fecha_registro = generar_fecha_aleatoria(FECHA_INICIO, FECHA_FIN - timedelta(days=30))

        segmento = segmentos[i]

        cursor.execute("""
            INSERT INTO users (
                nombre, email, password, fecha_registro, es_admin,
                total_compras, total_gastado, ticket_promedio,
                total_recargas, dinero_recargado_total, recarga_promedio,
                productos_carrito_actual, valor_carrito_actual,
                productos_agregados_carrito_total, carritos_abandonados,
                tasa_conversion, segmento_cliente, ultima_actividad
            ) VALUES (
                %s, %s, %s, %s, %s,
                0, 0.0, 0.0,
                0, 0.0, 0.0,
                0, 0.0,
                0, 0,
                0.0, %s, %s
            )
        """, (
            nombre, email, password_hash, fecha_registro, False,
            segmento, fecha_registro
        ))

        usuarios_ids.append(cursor.lastrowid)

    conn.commit()
    print(f"✅ {len(usuarios_ids)} usuarios creados")

    return usuarios_ids

def insertar_wallets(conn, usuarios_ids):
    """Crea wallets para todos los usuarios con saldos variados"""
    print("\n💰 Creando wallets...")

    cursor = conn.cursor()

    for usuario_id in tqdm(usuarios_ids, desc="Creando wallets"):
        saldo_base = 50.0
        variacion = np.random.normal(200, 150)
        saldo = max(saldo_base, saldo_base + variacion)

        cursor.execute("""
            INSERT INTO wallet (ID_Users, saldo)
            VALUES (%s, %s)
        """, (usuario_id, round(saldo, 2)))

    conn.commit()
    print(f"✅ {len(usuarios_ids)} wallets creadas")

def generar_compras_realistas(conn, usuarios_ids, productos_ids):
    """Genera pedidos con distribución Pareto"""
    print("\n🛒 Generando compras (distribución Pareto)...")

    cursor = conn.cursor()

    cursor.execute("SELECT ID_Users, segmento_cliente FROM users WHERE es_admin = 0")
    usuarios = cursor.fetchall()

    total_pedidos = 0

    for usuario in tqdm(usuarios, desc="Generando pedidos"):
        usuario_id = usuario['ID_Users']
        segmento = usuario['segmento_cliente']

        if segmento == 'vip':
            num_compras = random.randint(5, 20)
        elif segmento == 'activo':
            num_compras = random.randint(2, 8)
        elif segmento == 'nuevo':
            num_compras = random.randint(0, 2)
        else:
            num_compras = random.randint(0, 1)

        for _ in range(num_compras):
            cursor.execute("SELECT fecha_registro FROM users WHERE ID_Users = %s", (usuario_id,))
            fecha_registro = cursor.fetchone()['fecha_registro']

            fecha_pedido = generar_fecha_aleatoria(fecha_registro, FECHA_FIN)

            num_productos = int(np.random.exponential(1.5)) + 1
            num_productos = min(num_productos, 5)

            productos_pedido = random.sample(productos_ids, num_productos)

            total_pedido = 0.0
            items_pedido = []

            for producto_id in productos_pedido:
                cursor.execute("SELECT precio FROM producto WHERE ID_Producto = %s", (producto_id,))
                precio = cursor.fetchone()['precio']

                cantidad = random.choices([1, 2, 3], weights=[70, 25, 5])[0]

                subtotal = precio * cantidad
                total_pedido += subtotal

                items_pedido.append({
                    'producto_id': producto_id,
                    'cantidad': cantidad,
                    'precio_unitario': precio
                })

            cursor.execute("""
                INSERT INTO pedido (ID_Users, total, fecha, estado)
                VALUES (%s, %s, %s, %s)
            """, (usuario_id, round(total_pedido, 2), fecha_pedido, 'pagado'))

            pedido_id = cursor.lastrowid

            for item in items_pedido:
                cursor.execute("""
                    INSERT INTO detalle_pedido (ID_Pedido, ID_Producto, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s)
                """, (
                    pedido_id,
                    item['producto_id'],
                    item['cantidad'],
                    item['precio_unitario']
                ))

            total_pedidos += 1

    conn.commit()
    print(f"✅ {total_pedidos} pedidos creados")

def generar_historial_carrito(conn, usuarios_ids, productos_ids):
    """Genera historial de acciones del carrito"""
    print("\n📊 Generando historial de carrito...")

    cursor = conn.cursor()

    total_acciones = 0

    for usuario_id in tqdm(usuarios_ids, desc="Historial carrito"):
        cursor.execute("""
            SELECT ID_Pedido, fecha FROM pedido WHERE ID_Users = %s ORDER BY fecha
        """, (usuario_id,))
        pedidos = cursor.fetchall()

        for pedido in pedidos:
            cursor.execute("""
                SELECT ID_Producto, cantidad, precio_unitario
                FROM detalle_pedido
                WHERE ID_Pedido = %s
            """, (pedido['ID_Pedido'],))

            detalles = cursor.fetchall()

            for detalle in detalles:
                # Agregar
                cursor.execute("""
                    INSERT INTO historial_carrito (
                        ID_Users, ID_Producto, accion, cantidad,
                        precio_momento, valor_total, fecha, ID_Pedido
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NULL)
                """, (
                    usuario_id,
                    detalle['ID_Producto'],
                    'agregar',
                    detalle['cantidad'],
                    detalle['precio_unitario'],
                    detalle['cantidad'] * detalle['precio_unitario'],
                    pedido['fecha'] - timedelta(minutes=random.randint(5, 120))
                ))

                total_acciones += 1

                # Comprar
                cursor.execute("""
                    INSERT INTO historial_carrito (
                        ID_Users, ID_Producto, accion, cantidad,
                        precio_momento, valor_total, fecha, ID_Pedido
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    usuario_id,
                    detalle['ID_Producto'],
                    'comprar',
                    detalle['cantidad'],
                    detalle['precio_unitario'],
                    detalle['cantidad'] * detalle['precio_unitario'],
                    pedido['fecha'],
                    pedido['ID_Pedido']
                ))

                total_acciones += 1

        # Abandonos (30% de usuarios)
        if random.random() < 0.3:
            num_abandonos = random.randint(1, 3)

            for _ in range(num_abandonos):
                productos_abandonados = random.sample(productos_ids, random.randint(1, 4))

                cursor.execute("SELECT fecha_registro FROM users WHERE ID_Users = %s", (usuario_id,))
                fecha_reg = cursor.fetchone()['fecha_registro']
                fecha_abandono = generar_fecha_aleatoria(fecha_reg, FECHA_FIN)

                for producto_id in productos_abandonados:
                    cursor.execute("SELECT precio FROM producto WHERE ID_Producto = %s", (producto_id,))
                    precio = cursor.fetchone()['precio']
                    cantidad = random.randint(1, 2)

                    cursor.execute("""
                        INSERT INTO historial_carrito (
                            ID_Users, ID_Producto, accion, cantidad,
                            precio_momento, valor_total, fecha, ID_Pedido
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NULL)
                    """, (
                        usuario_id, producto_id, 'agregar', cantidad,
                        precio, precio * cantidad,
                        fecha_abandono - timedelta(hours=random.randint(1, 48))
                    ))

                    cursor.execute("""
                        INSERT INTO historial_carrito (
                            ID_Users, ID_Producto, accion, cantidad,
                            precio_momento, valor_total, fecha, ID_Pedido
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NULL)
                    """, (
                        usuario_id, producto_id, 'abandonar', cantidad,
                        precio, precio * cantidad, fecha_abandono
                    ))

                    total_acciones += 2

    conn.commit()
    print(f"✅ {total_acciones} acciones de carrito registradas")

def generar_transacciones_wallet(conn, usuarios_ids):
    """Genera transacciones de wallet (recargas y compras)"""
    print("\n💳 Generando transacciones de wallet...")

    cursor = conn.cursor()

    total_transacciones = 0

    for usuario_id in tqdm(usuarios_ids, desc="Transacciones wallet"):
        cursor.execute("SELECT ID_Wallet, saldo FROM wallet WHERE ID_Users = %s", (usuario_id,))
        wallet_data = cursor.fetchone()
        wallet_id = wallet_data['ID_Wallet']
        saldo_actual = 50.0

        cursor.execute("""
            SELECT ID_Pedido, total, fecha FROM pedido
            WHERE ID_Users = %s ORDER BY fecha
        """, (usuario_id,))
        pedidos = cursor.fetchall()

        for pedido in pedidos:
            if saldo_actual < pedido['total']:
                monto_recarga = pedido['total'] * random.uniform(1.5, 3.0)
                monto_recarga = round(monto_recarga, 2)

                saldo_anterior = saldo_actual
                saldo_actual += monto_recarga

                cursor.execute("""
                    INSERT INTO transacciones_wallet (
                        ID_Wallet, ID_Users, tipo, monto,
                        saldo_anterior, saldo_nuevo, descripcion,
                        ID_Pedido, fecha
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, %s)
                """, (
                    wallet_id, usuario_id, 'recarga', monto_recarga,
                    saldo_anterior, saldo_actual, 'Recarga de saldo',
                    pedido['fecha'] - timedelta(minutes=random.randint(1, 30))
                ))

                total_transacciones += 1

            saldo_anterior = saldo_actual
            saldo_actual -= pedido['total']

            cursor.execute("""
                INSERT INTO transacciones_wallet (
                    ID_Wallet, ID_Users, tipo, monto,
                    saldo_anterior, saldo_nuevo, descripcion,
                    ID_Pedido, fecha
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                wallet_id, usuario_id, 'compra', -pedido['total'],
                saldo_anterior, saldo_actual,
                f"Compra - Pedido #{pedido['ID_Pedido']}",
                pedido['ID_Pedido'], pedido['fecha']
            ))

            total_transacciones += 1

        cursor.execute("""
            UPDATE wallet SET saldo = %s WHERE ID_Wallet = %s
        """, (round(saldo_actual, 2), wallet_id))

    conn.commit()
    print(f"✅ {total_transacciones} transacciones de wallet creadas")

def actualizar_metricas_usuarios(conn):
    """Actualiza todas las métricas calculadas de usuarios"""
    print("\n📈 Calculando métricas de usuarios...")

    cursor = conn.cursor()

    cursor.execute("SELECT ID_Users FROM users WHERE es_admin = 0")
    usuarios = cursor.fetchall()

    for usuario in tqdm(usuarios, desc="Actualizando métricas"):
        usuario_id = usuario['ID_Users']

        # Total compras y gastado
        cursor.execute("""
            SELECT COUNT(*) as total_compras, COALESCE(SUM(total), 0) as total_gastado
            FROM pedido WHERE ID_Users = %s
        """, (usuario_id,))
        compras_data = cursor.fetchone()

        total_compras = compras_data['total_compras']
        total_gastado = compras_data['total_gastado']
        ticket_promedio = total_gastado / total_compras if total_compras > 0 else 0

        cursor.execute("""
            SELECT MAX(fecha) as ultima_fecha FROM pedido WHERE ID_Users = %s
        """, (usuario_id,))
        ultima_fecha = cursor.fetchone()['ultima_fecha']

        dias_desde_ultima = (FECHA_FIN - ultima_fecha).days if ultima_fecha else None

        # Recargas
        cursor.execute("""
            SELECT COUNT(*) as total_recargas, COALESCE(SUM(monto), 0) as total_recargado
            FROM transacciones_wallet
            WHERE ID_Users = %s AND tipo = 'recarga'
        """, (usuario_id,))
        recargas_data = cursor.fetchone()

        total_recargas = recargas_data['total_recargas']
        dinero_recargado = recargas_data['total_recargado']
        recarga_promedio = dinero_recargado / total_recargas if total_recargas > 0 else 0

        # Carrito
        cursor.execute("""
            SELECT
                SUM(CASE WHEN accion = 'agregar' THEN cantidad ELSE 0 END) as agregados,
                COUNT(DISTINCT CASE WHEN accion = 'abandonar' THEN DATE(fecha) END) as abandonos
            FROM historial_carrito
            WHERE ID_Users = %s
        """, (usuario_id,))
        carrito_data = cursor.fetchone()

        productos_agregados = carrito_data['agregados'] or 0
        carritos_abandonados = carrito_data['abandonos'] or 0

        # Productos comprados
        cursor.execute("""
            SELECT COALESCE(SUM(dp.cantidad), 0) as comprados
            FROM detalle_pedido dp
            JOIN pedido p ON dp.ID_Pedido = p.ID_Pedido
            WHERE p.ID_Users = %s
        """, (usuario_id,))
        productos_comprados = cursor.fetchone()['comprados']

        tasa_conversion = (productos_comprados / productos_agregados * 100) if productos_agregados > 0 else 0

        cursor.execute("""
            UPDATE users SET
                total_compras = %s,
                total_gastado = %s,
                ticket_promedio = %s,
                ultimo_pedido_fecha = %s,
                dias_desde_ultima_compra = %s,
                total_recargas = %s,
                dinero_recargado_total = %s,
                recarga_promedio = %s,
                productos_agregados_carrito_total = %s,
                carritos_abandonados = %s,
                tasa_conversion = %s
            WHERE ID_Users = %s
        """, (
            total_compras, round(total_gastado, 2), round(ticket_promedio, 2),
            ultima_fecha, dias_desde_ultima,
            total_recargas, round(dinero_recargado, 2), round(recarga_promedio, 2),
            productos_agregados, carritos_abandonados, round(tasa_conversion, 2),
            usuario_id
        ))

    conn.commit()
    print("✅ Métricas de usuarios actualizadas")

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def main():
    print("=" * 70)
    print("🎲 GENERADOR DE DATOS FICTICIOS REALISTAS - AXION STORE")
    print("=" * 70)
    print(f"🗄️  Base de Datos: {DB_NAME}")
    print(f"📊 Generando: {NUMERO_USUARIOS} usuarios")
    print(f"📅 Período: {FECHA_INICIO.date()} → {FECHA_FIN.date()}")
    print("=" * 70)

    try:
        # 1. Crear base de datos
        crear_base_datos()

        # 2. Crear estructura de tablas
        crear_estructura_tablas()

        # 3. Conexión para insertar datos
        conn = obtener_conexion()
        print("✅ Conectado a", DB_NAME)

        # 4. Insertar categorías, subcategorías y productos
        categorias_ids, subcategorias_ids, productos_ids = insertar_categorias_y_productos(conn)

        # 5. Insertar usuarios
        usuarios_ids = insertar_usuarios(conn)

        # 6. Crear wallets
        insertar_wallets(conn, usuarios_ids)

        # 7. Generar compras realistas
        generar_compras_realistas(conn, usuarios_ids, productos_ids)

        # 8. Generar historial de carrito
        generar_historial_carrito(conn, usuarios_ids, productos_ids)

        # 9. Generar transacciones de wallet
        generar_transacciones_wallet(conn, usuarios_ids)

        # 10. Actualizar métricas
        actualizar_metricas_usuarios(conn)

        conn.close()

        print("\n" + "=" * 70)
        print("🎉 ¡DATOS GENERADOS EXITOSAMENTE!")
        print("=" * 70)
        print(f"✅ Base de datos: {DB_NAME}")
        print(f"✅ {NUMERO_USUARIOS} usuarios creados")
        print(f"✅ {len(productos_ids)} productos creados")
        print(f"✅ {len(categorias_ids)} categorías creadas")
        print(f"✅ Wallets, pedidos, historial y métricas generados")
        print("\n💡 Para usar estos datos:")
        print(f"   🔧 Cambiar en app.py (temporal):")
        print(f"      database='axion_store' → database='{DB_NAME}'")
        print("   📧 Contraseña de todos los usuarios: password123")
        print("   🔐 Usuario admin: usar script copiar_admin.py (opcional)")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

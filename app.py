from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, stream_with_context, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import pymysql
import os
import time
import json
import csv
from io import StringIO
from queue import Queue, Empty
from threading import Lock
from werkzeug.utils import secure_filename

pymysql.install_as_MySQLdb()

app = Flask(__name__)
from flask import url_for
@app.template_filter('static_or_placeholder')
def static_or_placeholder(filename, size=300):
    try:
        if filename:
            return url_for('static', filename=filename)
    except Exception:
        app.logger.debug(f'static_or_placeholder: failed to build static url for {filename}')
    # fallback placeholder
    return f'https://via.placeholder.com/{size}x{int(size*0.66)}?text=Sin+Imagen'

app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui-cambiala'

# Configuración de MySQL/MariaDB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:*9YsEP+SK2np*@localhost:3306/axion_store?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Opciones optimizadas para laptop
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'pool_size': 5,
    'max_overflow': 10,
    'connect_args': {
        'connect_timeout': 60,
        'charset': 'utf8mb4'
    }
}

db = SQLAlchemy(app)

# NOTE: Real-time server-sent notifications have been disabled.
# keep a noop `notify_user` so other code can call it safely.
def notify_user(user_id, message):
    """No-op notifier. Real-time notifications disabled to simplify UX.
    Calls to this function are logged for debugging only.
    """
    try:
        app.logger.debug(f'notify_user (disabled) for user {user_id}: {message}')
    except Exception:
        pass

# Configuración de uploads
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'img')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== CONSTANTES DE VALIDACIÓN ====================

class ValidationLimits:
    MIN_NOMBRE_LENGTH = 3
    MIN_PASSWORD_LENGTH = 6
    MAX_RECARGA = 10000
    MIN_RECARGA = 1

# ==================== MODELOS DE BASE DE DATOS ====================

class Usuario(db.Model):
    __tablename__ = 'users'
    ID_Users = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    es_admin = db.Column(db.Boolean, default=False)

    # === MÉTRICAS DE COMPRAS ===
    total_compras = db.Column(db.Integer, default=0)
    total_gastado = db.Column(db.Float, default=0.0)
    ticket_promedio = db.Column(db.Float, default=0.0)
    ultimo_pedido_fecha = db.Column(db.DateTime)
    dias_desde_ultima_compra = db.Column(db.Integer)

    # === MÉTRICAS DE WALLET ===
    total_recargas = db.Column(db.Integer, default=0)
    dinero_recargado_total = db.Column(db.Float, default=0.0)
    recarga_promedio = db.Column(db.Float, default=0.0)
    ultima_recarga_fecha = db.Column(db.DateTime)

    # === MÉTRICAS DE CARRITO ===
    productos_carrito_actual = db.Column(db.Integer, default=0)
    valor_carrito_actual = db.Column(db.Float, default=0.0)
    productos_agregados_carrito_total = db.Column(db.Integer, default=0)
    carritos_abandonados = db.Column(db.Integer, default=0)

    # === MÉTRICAS DE CONVERSIÓN ===
    tasa_conversion = db.Column(db.Float, default=0.0)

    # === SEGMENTACIÓN (SIN VIP) ===
    segmento_cliente = db.Column(db.String(50), default='nuevo')  # valores: nuevo, activo, inactivo
    ultima_actividad = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    wallet = db.relationship('Wallet', backref='usuario', uselist=False)
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)
    carritos = db.relationship('Carrito', backref='usuario', lazy=True)


class Producto(db.Model):
    __tablename__ = 'producto'
    ID_Producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, index=True)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(300))
    descripcion = db.Column(db.Text)
    disponible = db.Column(db.Boolean, default=True)
    stock = db.Column(db.Integer, default=0)
    ID_Subcategoria = db.Column(db.Integer, db.ForeignKey('subcategoria.ID_Subcategoria'), index=True)
    ID_Categoria = db.Column(db.Integer, db.ForeignKey('categoria.ID_Categoria'), index=True)


class Categoria(db.Model):
    __tablename__ = 'categoria'
    ID_Categoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.Text)
    icono = db.Column(db.String(50))
    activa = db.Column(db.Boolean, default=True, index=True)
    orden = db.Column(db.Integer, default=0, index=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    subcategorias = db.relationship('Subcategoria', backref='categoria', lazy=True, cascade='all, delete-orphan')
    productos = db.relationship('Producto', backref='categoria', lazy=True)


class Subcategoria(db.Model):
    __tablename__ = 'subcategoria'
    ID_Subcategoria = db.Column(db.Integer, primary_key=True)
    ID_Categoria = db.Column(db.Integer, db.ForeignKey('categoria.ID_Categoria'), nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    activa = db.Column(db.Boolean, default=True, index=True)
    orden = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    productos = db.relationship('Producto', backref='subcategoria', lazy=True)

    def to_dict(self):
        """Convierte el objeto a diccionario serializable para JSON"""
        return {
            'ID_Subcategoria': self.ID_Subcategoria,
            'nombre': self.nombre,
            'descripcion': self.descripcion or '',
            'activa': self.activa,
            'orden': self.orden
        }


class MetricaCategoria(db.Model):
    __tablename__ = 'metricas_categoria'
    ID_Metrica = db.Column(db.Integer, primary_key=True)
    ID_Categoria = db.Column(db.Integer, db.ForeignKey('categoria.ID_Categoria'), nullable=False, unique=True, index=True)

    total_productos_vendidos = db.Column(db.Integer, default=0)
    total_pedidos = db.Column(db.Integer, default=0)
    ingresos_totales = db.Column(db.Float, default=0.0)
    ticket_promedio = db.Column(db.Float, default=0.0)

    total_agregados_carrito = db.Column(db.Integer, default=0)
    total_abandonos = db.Column(db.Integer, default=0)
    valor_abandonos = db.Column(db.Float, default=0.0)

    tasa_conversion = db.Column(db.Float, default=0.0)

    productos_activos = db.Column(db.Integer, default=0)
    productos_sin_stock = db.Column(db.Integer, default=0)

    ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    categoria = db.relationship('Categoria', backref=db.backref('metricas', uselist=False))


class MetricaSubcategoria(db.Model):
    __tablename__ = 'metricas_subcategoria'
    ID_Metrica = db.Column(db.Integer, primary_key=True)
    ID_Subcategoria = db.Column(db.Integer, db.ForeignKey('subcategoria.ID_Subcategoria'), nullable=False, unique=True, index=True)
    ID_Categoria = db.Column(db.Integer, db.ForeignKey('categoria.ID_Categoria'), nullable=False, index=True)

    total_productos_vendidos = db.Column(db.Integer, default=0)
    total_pedidos = db.Column(db.Integer, default=0)
    ingresos_totales = db.Column(db.Float, default=0.0)
    ticket_promedio = db.Column(db.Float, default=0.0)

    total_agregados_carrito = db.Column(db.Integer, default=0)
    total_abandonos = db.Column(db.Integer, default=0)
    valor_abandonos = db.Column(db.Float, default=0.0)

    tasa_conversion = db.Column(db.Float, default=0.0)

    productos_activos = db.Column(db.Integer, default=0)
    productos_sin_stock = db.Column(db.Integer, default=0)

    ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subcategoria = db.relationship('Subcategoria', backref=db.backref('metricas', uselist=False))
    categoria = db.relationship('Categoria')


class Wallet(db.Model):
    __tablename__ = 'wallet'
    ID_Wallet = db.Column(db.Integer, primary_key=True)
    ID_Users = db.Column(db.Integer, db.ForeignKey('users.ID_Users'), nullable=False, index=True)
    saldo = db.Column(db.Float, default=50.0)


class Carrito(db.Model):
    __tablename__ = 'carrito'
    ID_Carrito = db.Column(db.Integer, primary_key=True)
    ID_Users = db.Column(db.Integer, db.ForeignKey('users.ID_Users'), nullable=False, index=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=False, index=True)
    cantidad = db.Column(db.Integer, default=1)
    producto = db.relationship('Producto', backref='carritos')


class Pedido(db.Model):
    __tablename__ = 'pedido'
    ID_Pedido = db.Column(db.Integer, primary_key=True)
    ID_Users = db.Column(db.Integer, db.ForeignKey('users.ID_Users'), nullable=False, index=True)
    total = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='pagado')
    detalles = db.relationship('DetallePedido', backref='pedido', lazy=True)


class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'
    ID_Detalle_Pedido = db.Column(db.Integer, primary_key=True)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('pedido.ID_Pedido'), nullable=False, index=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=False, index=True)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto', backref='detalles_pedido')


class HistorialCarrito(db.Model):
    __tablename__ = 'historial_carrito'
    ID_Historial = db.Column(db.Integer, primary_key=True)
    ID_Users = db.Column(db.Integer, db.ForeignKey('users.ID_Users'), nullable=False, index=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=False, index=True)
    accion = db.Column(db.String(20), nullable=False, index=True)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_momento = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('pedido.ID_Pedido'))

    usuario = db.relationship('Usuario')
    producto = db.relationship('Producto', backref='historial_carrito')
    pedido = db.relationship('Pedido', backref='items_originales')


class TransaccionWallet(db.Model):
    __tablename__ = 'transacciones_wallet'
    ID_Transaccion = db.Column(db.Integer, primary_key=True)
    ID_Wallet = db.Column(db.Integer, db.ForeignKey('wallet.ID_Wallet'), nullable=False, index=True)
    ID_Users = db.Column(db.Integer, db.ForeignKey('users.ID_Users'), nullable=False, index=True)
    tipo = db.Column(db.String(20), nullable=False, index=True)
    monto = db.Column(db.Float, nullable=False)
    saldo_anterior = db.Column(db.Float, nullable=False)
    saldo_nuevo = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200))
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('pedido.ID_Pedido'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    wallet = db.relationship('Wallet', backref='transacciones')
    usuario = db.relationship('Usuario')
    pedido = db.relationship('Pedido')


class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    ID_Wishlist = db.Column(db.Integer, primary_key=True)
    ID_Users = db.Column(db.Integer, db.ForeignKey('users.ID_Users'), nullable=False, index=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=False, index=True)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref=db.backref('wishlists', lazy=True))
    producto = db.relationship('Producto', backref=db.backref('en_wishlists', lazy=True))

    __table_args__ = (db.UniqueConstraint('ID_Users', 'ID_Producto', name='unique_user_product_wishlist'),)


class ActionHistory(db.Model):
    __tablename__ = 'action_history'
    ID_Action = db.Column(db.Integer, primary_key=True)
    ID_Users = db.Column(db.Integer, db.ForeignKey('users.ID_Users'), nullable=True, index=True)
    accion = db.Column(db.String(100), nullable=False, index=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=True, index=True)
    nombre = db.Column(db.String(200))
    meta = db.Column(db.Text)  # JSON string for extra metadata
    fecha = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    usuario = db.relationship('Usuario', backref='action_history', foreign_keys=[ID_Users])
    producto = db.relationship('Producto', foreign_keys=[producto_id])


# ==================== FUNCIÓN PARA CREAR TABLAS ====================

def crear_tablas_db():
    """
    Crea todas las tablas en la base de datos si no existen.
    Compatible con MariaDB/MySQL.
    """
    with app.app_context():
        try:
            # Crear todas las tablas definidas en los modelos
            db.create_all()

            # Verificar y corregir columnas faltantes que pueden causar errores en tiempo de ejecución.
            # Ej: algunos dumps/instalaciones antiguas pueden no contener la columna 'ID_Subcategoria' en 'producto'.
            try:
                # Comprobar existencia de la columna en information_schema
                res = db.session.execute(db.text("""
                    SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'producto' AND COLUMN_NAME = 'ID_Subcategoria'
                """)).fetchone()

                if not res or int(res[0]) == 0:
                    # Agregar la columna como NULLABLE para compatibilidad retroactiva
                    db.session.execute(db.text("ALTER TABLE producto ADD COLUMN ID_Subcategoria INT NULL"))
                    # Agregar índice para mejorar consultas que lo utilicen
                    try:
                        db.session.execute(db.text("ALTER TABLE producto ADD INDEX idx_producto_id_subcategoria (ID_Subcategoria)"))
                    except Exception:
                        # índice puede ya existir en algunos motores
                        pass

                    # Intentar añadir FK si la tabla subcategoria existe
                    tbl = db.session.execute(db.text("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'subcategoria'"))
                    if tbl and int(tbl.fetchone()[0] or 0) > 0:
                        try:
                            db.session.execute(db.text(
                                "ALTER TABLE producto ADD CONSTRAINT fk_producto_subcategoria FOREIGN KEY (ID_Subcategoria) REFERENCES subcategoria(ID_Subcategoria) ON DELETE SET NULL ON UPDATE CASCADE"
                            ))
                        except Exception:
                            # Si no se puede añadir la FK (por permisos o ya existe), continuar sin fallar
                            pass

                    db.session.commit()
                    app.logger.info('Columna faltante ID_Subcategoria añadida a producto')
            except Exception as e:
                db.session.rollback()
                app.logger.warning(f'No se pudo verificar/crear columna ID_Subcategoria automáticamente: {e}')

            # Asegurar columna 'descripcion' en la tabla producto (compatible retroactivo)
            try:
                res2 = db.session.execute(db.text("""
                    SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'producto' AND COLUMN_NAME = 'descripcion'
                """)).fetchone()
                if not res2 or int(res2[0]) == 0:
                    db.session.execute(db.text("ALTER TABLE producto ADD COLUMN descripcion TEXT NULL"))
                    db.session.commit()
                    app.logger.info('Columna faltante descripcion añadida a producto')
            except Exception as e:
                db.session.rollback()
                app.logger.warning(f'No se pudo crear columna descripcion automaticamente: {e}')
            except Exception as e:
                # No queremos que una corrección automática impida la creación de tablas; logueamos y continuamos
                db.session.rollback()
                app.logger.warning(f'No se pudo verificar/crear columna ID_Subcategoria automáticamente: {e}')

            print("✓ Tablas verificadas/creadas exitosamente en la base de datos")
            return True
        except Exception as e:
            print(f"✗ Error al crear tablas: {str(e)}")
            app.logger.error(f'Error al crear tablas: {str(e)}')
            return False


def verificar_conexion_db():
    """
    Verifica la conexión a la base de datos y crea las tablas si es necesario.
    """
    with app.app_context():
        try:
            # Intentar ejecutar una consulta simple
            db.session.execute(db.text('SELECT 1'))
            print("✓ Conexión a la base de datos establecida")

            # Crear tablas si no existen
            crear_tablas_db()
            return True
        except Exception as e:
            print(f"✗ Error de conexión a la base de datos: {str(e)}")
            app.logger.error(f'Error de conexión DB: {str(e)}')
            return False


# ==================== FUNCIÓN DE ACTUALIZACIÓN DE MÉTRICAS ====================

def actualizar_metricas_usuario(usuario_id):
    """
    Actualiza TODAS las métricas del usuario de forma eficiente.
    """
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return

        # === MÉTRICAS DE COMPRAS ===
        stats_pedidos = db.session.query(
            db.func.count(Pedido.ID_Pedido).label('total'),
            db.func.sum(Pedido.total).label('gastado'),
            db.func.max(Pedido.fecha).label('ultimo')
        ).filter(Pedido.ID_Users == usuario_id).first()

        usuario.total_compras = stats_pedidos.total or 0
        usuario.total_gastado = float(stats_pedidos.gastado or 0.0)
        usuario.ticket_promedio = (usuario.total_gastado / usuario.total_compras) if usuario.total_compras > 0 else 0.0
        usuario.ultimo_pedido_fecha = stats_pedidos.ultimo

        if usuario.ultimo_pedido_fecha:
            usuario.dias_desde_ultima_compra = (datetime.utcnow() - usuario.ultimo_pedido_fecha).days

        # === MÉTRICAS DE WALLET ===
        stats_recargas = db.session.query(
            db.func.count(TransaccionWallet.ID_Transaccion).label('total'),
            db.func.sum(TransaccionWallet.monto).label('dinero'),
            db.func.max(TransaccionWallet.fecha).label('ultima')
        ).filter(
            TransaccionWallet.ID_Users == usuario_id,
            TransaccionWallet.tipo == 'recarga'
        ).first()

        usuario.total_recargas = stats_recargas.total or 0
        usuario.dinero_recargado_total = float(stats_recargas.dinero or 0.0)
        usuario.recarga_promedio = (usuario.dinero_recargado_total / usuario.total_recargas) if usuario.total_recargas > 0 else 0.0
        usuario.ultima_recarga_fecha = stats_recargas.ultima

        # === MÉTRICAS DE CARRITO ACTUAL ===
        stats_carrito = db.session.query(
            db.func.sum(Carrito.cantidad).label('items'),
            db.func.sum(Carrito.cantidad * Producto.precio).label('valor')
        ).join(Producto).filter(Carrito.ID_Users == usuario_id).first()

        usuario.productos_carrito_actual = int(stats_carrito.items or 0)
        usuario.valor_carrito_actual = float(stats_carrito.valor or 0.0)

        # === MÉTRICAS HISTÓRICAS DE CARRITO ===
        total_agregados = db.session.query(
            db.func.sum(HistorialCarrito.cantidad)
        ).filter(
            HistorialCarrito.ID_Users == usuario_id,
            HistorialCarrito.accion == 'agregar'
        ).scalar() or 0
        usuario.productos_agregados_carrito_total = int(total_agregados)

        total_abandonos = db.session.query(
            db.func.count(db.distinct(db.func.date(HistorialCarrito.fecha)))
        ).filter(
            HistorialCarrito.ID_Users == usuario_id,
            HistorialCarrito.accion == 'abandonar'
        ).scalar() or 0
        usuario.carritos_abandonados = int(total_abandonos)

        # === TASA DE CONVERSIÓN ===
        if usuario.productos_agregados_carrito_total > 0:
            total_comprados = db.session.query(
                db.func.sum(DetallePedido.cantidad)
            ).join(Pedido).filter(Pedido.ID_Users == usuario_id).scalar() or 0
            usuario.tasa_conversion = (total_comprados / usuario.productos_agregados_carrito_total) * 100
        else:
            usuario.tasa_conversion = 0.0

        # === SEGMENTACIÓN AUTOMÁTICA (SIN VIP) ===
        if usuario.total_compras == 0:
            usuario.segmento_cliente = 'nuevo'
        elif usuario.dias_desde_ultima_compra and usuario.dias_desde_ultima_compra > 60:
            usuario.segmento_cliente = 'inactivo'
        else:
            usuario.segmento_cliente = 'activo'

        usuario.ultima_actividad = datetime.utcnow()
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error actualizando métricas usuario {usuario_id}: {str(e)}')


# ==================== FUNCIONES DE MÉTRICAS DE CATEGORÍAS ====================

def actualizar_metricas_categoria(categoria_id):
    """Actualiza TODAS las métricas de una categoría específica"""
    try:
        categoria = Categoria.query.get(categoria_id)
        if not categoria:
            return

        metricas = MetricaCategoria.query.filter_by(ID_Categoria=categoria_id).first()
        if not metricas:
            metricas = MetricaCategoria(ID_Categoria=categoria_id)
            db.session.add(metricas)

        # === MÉTRICAS DE VENTAS ===
        ventas_stats = db.session.query(
            db.func.coalesce(db.func.sum(DetallePedido.cantidad), 0).label('total_vendido'),
            db.func.count(db.distinct(Pedido.ID_Pedido)).label('total_pedidos'),
            db.func.coalesce(db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario), 0).label('ingresos')
        ).join(Producto).join(Pedido).filter(
            Producto.ID_Categoria == categoria_id
        ).first()

        metricas.total_productos_vendidos = int(ventas_stats.total_vendido or 0)
        metricas.total_pedidos = int(ventas_stats.total_pedidos or 0)
        metricas.ingresos_totales = float(ventas_stats.ingresos or 0.0)
        metricas.ticket_promedio = (metricas.ingresos_totales / metricas.total_pedidos) if metricas.total_pedidos > 0 else 0.0

        # === MÉTRICAS DE CARRITO ===
        agregados = db.session.query(
            db.func.coalesce(db.func.sum(HistorialCarrito.cantidad), 0)
        ).join(Producto).filter(
            Producto.ID_Categoria == categoria_id,
            HistorialCarrito.accion == 'agregar'
        ).scalar() or 0
        metricas.total_agregados_carrito = int(agregados)

        abandonos_stats = db.session.query(
            db.func.coalesce(db.func.sum(HistorialCarrito.cantidad), 0).label('total'),
            db.func.coalesce(db.func.sum(HistorialCarrito.valor_total), 0).label('valor')
        ).join(Producto).filter(
            Producto.ID_Categoria == categoria_id,
            HistorialCarrito.accion == 'abandonar'
        ).first()

        metricas.total_abandonos = int(abandonos_stats.total or 0)
        metricas.valor_abandonos = float(abandonos_stats.valor or 0.0)

        # === TASA DE CONVERSIÓN ===
        if metricas.total_agregados_carrito > 0:
            metricas.tasa_conversion = (metricas.total_productos_vendidos / metricas.total_agregados_carrito) * 100
        else:
            metricas.tasa_conversion = 0.0

        # === MÉTRICAS DE PRODUCTOS ===
        metricas.productos_activos = Producto.query.filter_by(ID_Categoria=categoria_id, disponible=True).count()
        metricas.productos_sin_stock = Producto.query.filter_by(ID_Categoria=categoria_id, stock=0).count()

        metricas.ultima_actualizacion = datetime.utcnow()
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error actualizando métricas categoría {categoria_id}: {str(e)}')


def actualizar_metricas_subcategoria(subcategoria_id):
    """Actualiza métricas de una subcategoría específica"""
    try:
        subcategoria = Subcategoria.query.get(subcategoria_id)
        if not subcategoria:
            return

        metricas = MetricaSubcategoria.query.filter_by(ID_Subcategoria=subcategoria_id).first()
        if not metricas:
            metricas = MetricaSubcategoria(
                ID_Subcategoria=subcategoria_id,
                ID_Categoria=subcategoria.ID_Categoria
            )
            db.session.add(metricas)

        # === MÉTRICAS DE VENTAS ===
        ventas_stats = db.session.query(
            db.func.coalesce(db.func.sum(DetallePedido.cantidad), 0).label('total_vendido'),
            db.func.count(db.distinct(Pedido.ID_Pedido)).label('total_pedidos'),
            db.func.coalesce(db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario), 0).label('ingresos')
        ).join(Producto).join(Pedido).filter(
            Producto.ID_Subcategoria == subcategoria_id
        ).first()

        metricas.total_productos_vendidos = int(ventas_stats.total_vendido or 0)
        metricas.total_pedidos = int(ventas_stats.total_pedidos or 0)
        metricas.ingresos_totales = float(ventas_stats.ingresos or 0.0)
        metricas.ticket_promedio = (metricas.ingresos_totales / metricas.total_pedidos) if metricas.total_pedidos > 0 else 0.0

        # === MÉTRICAS DE CARRITO ===
        agregados = db.session.query(
            db.func.coalesce(db.func.sum(HistorialCarrito.cantidad), 0)
        ).join(Producto).filter(
            Producto.ID_Subcategoria == subcategoria_id,
            HistorialCarrito.accion == 'agregar'
        ).scalar() or 0
        metricas.total_agregados_carrito = int(agregados)

        abandonos_stats = db.session.query(
            db.func.coalesce(db.func.sum(HistorialCarrito.cantidad), 0).label('total'),
            db.func.coalesce(db.func.sum(HistorialCarrito.valor_total), 0).label('valor')
        ).join(Producto).filter(
            Producto.ID_Subcategoria == subcategoria_id,
            HistorialCarrito.accion == 'abandonar'
        ).first()

        metricas.total_abandonos = int(abandonos_stats.total or 0)
        metricas.valor_abandonos = float(abandonos_stats.valor or 0.0)

        # === TASA DE CONVERSIÓN ===
        if metricas.total_agregados_carrito > 0:
            metricas.tasa_conversion = (metricas.total_productos_vendidos / metricas.total_agregados_carrito) * 100
        else:
            metricas.tasa_conversion = 0.0

        # === MÉTRICAS DE PRODUCTOS ===
        metricas.productos_activos = Producto.query.filter_by(ID_Subcategoria=subcategoria_id, disponible=True).count()
        metricas.productos_sin_stock = Producto.query.filter_by(ID_Subcategoria=subcategoria_id, stock=0).count()

        metricas.ultima_actualizacion = datetime.utcnow()
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error actualizando métricas subcategoría {subcategoria_id}: {str(e)}')


def actualizar_todas_metricas_categorias():
    """Actualiza métricas de TODAS las categorías y subcategorías"""
    try:
        categorias = Categoria.query.all()
        for cat in categorias:
            actualizar_metricas_categoria(cat.ID_Categoria)

        subcategorias = Subcategoria.query.all()
        for sub in subcategorias:
            actualizar_metricas_subcategoria(sub.ID_Subcategoria)

        app.logger.info('✓ Métricas de categorías actualizadas exitosamente')

    except Exception as e:
        app.logger.error(f'Error actualizando todas las métricas: {str(e)}')


# ==================== DECORADORES ====================

@app.context_processor
def inject_cart_count():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return dict(cart_count=0, wishlist_count=0)

        cart_total = db.session.query(db.func.sum(Carrito.cantidad)).filter(
            Carrito.ID_Users == user_id
        ).scalar() or 0

        wishlist_total = Wishlist.query.filter_by(ID_Users=user_id).count()

        return dict(cart_count=cart_total, wishlist_count=wishlist_total)
    except Exception:
        return dict(cart_count=0, wishlist_count=0)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión', 'warning')
            return redirect(url_for('login'))
        usuario = Usuario.query.get(session['user_id'])
        if not usuario or not usuario.es_admin:
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not all([nombre, email, password, confirm_password]):
                flash('Todos los campos son obligatorios', 'danger')
                return redirect(url_for('register'))

            if len(nombre) < ValidationLimits.MIN_NOMBRE_LENGTH:
                flash(f'El nombre debe tener al menos {ValidationLimits.MIN_NOMBRE_LENGTH} caracteres', 'danger')
                return redirect(url_for('register'))

            if len(password) < ValidationLimits.MIN_PASSWORD_LENGTH:
                flash(f'La contraseña debe tener al menos {ValidationLimits.MIN_PASSWORD_LENGTH} caracteres', 'danger')
                return redirect(url_for('register'))

            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'danger')
                return redirect(url_for('register'))

            usuario_existente = Usuario.query.filter_by(email=email).first()
            if usuario_existente:
                flash('El correo electrónico ya está registrado', 'danger')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            nuevo_usuario = Usuario(nombre=nombre, email=email, password=hashed_password)

            db.session.add(nuevo_usuario)
            db.session.commit()

            wallet = Wallet(ID_Users=nuevo_usuario.ID_Users, saldo=50.0)
            db.session.add(wallet)
            db.session.commit()

            session['user_id'] = nuevo_usuario.ID_Users
            session['user_name'] = nuevo_usuario.nombre
            session['user_email'] = nuevo_usuario.email
            session['is_admin'] = nuevo_usuario.es_admin

            flash('¡Registro exitoso! Has iniciado sesión automáticamente', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            db.session.rollback()
            flash('Error al registrar usuario. Por favor intenta de nuevo.', 'danger')
            app.logger.error(f'Error en registro: {str(e)}')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            if not email or not password:
                flash('Por favor completa todos los campos', 'warning')
                return redirect(url_for('login'))

            usuario = Usuario.query.filter_by(email=email).first()

            if usuario and check_password_hash(usuario.password, password):
                session['user_id'] = usuario.ID_Users
                session['user_name'] = usuario.nombre
                session['user_email'] = usuario.email
                session['is_admin'] = usuario.es_admin
                flash(f'¡Bienvenido de nuevo, {usuario.nombre}!', 'success')

                if usuario.es_admin:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('home'))
            else:
                flash('Correo electrónico o contraseña incorrectos', 'danger')
                return redirect(url_for('login'))

        except Exception as e:
            flash('Error al iniciar sesión. Por favor intenta de nuevo.', 'danger')
            app.logger.error(f'Error en login: {str(e)}')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('index'))


@app.route('/reset_password', methods=['POST'])
def reset_password():
    """Permite al usuario restablecer su contraseña suministrando su correo y la nueva contraseña.
    Si la petición es AJAX devuelve JSON, si no redirige con flash messages.
    """
    try:
        email = request.form.get('email') or ''
        new_pw = request.form.get('new_password') or ''
        confirm_pw = request.form.get('confirm_password') or ''

        if not email or not new_pw or not confirm_pw:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'error', 'message': 'Completa todos los campos'}), 400
            flash('Por favor completa todos los campos', 'warning')
            return redirect(url_for('login'))

        if new_pw != confirm_pw:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'error', 'message': 'Las contraseñas no coinciden'}), 400
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('login'))

        if len(new_pw) < ValidationLimits.MIN_PASSWORD_LENGTH:
            msg = f'La contraseña debe tener al menos {ValidationLimits.MIN_PASSWORD_LENGTH} caracteres'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'error', 'message': msg}), 400
            flash(msg, 'warning')
            return redirect(url_for('login'))

        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'error', 'message': 'No existe una cuenta con ese correo'}), 404
            flash('No existe una cuenta con ese correo', 'danger')
            return redirect(url_for('login'))

        usuario.password = generate_password_hash(new_pw)
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'ok', 'message': 'Contraseña actualizada. Ahora puedes iniciar sesión.'})

        flash('Contraseña restablecida correctamente. Inicia sesión con tu nueva contraseña.', 'success')
        return redirect(url_for('login'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error en reset_password: {e}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Error del servidor'}), 500
        flash('Ocurrió un error al restablecer la contraseña', 'danger')
        return redirect(url_for('login'))


# ==================== AUTOCOMPLETE SEARCH API ====================

@app.route('/api/search_autocomplete')
def api_search_autocomplete():
    q = request.args.get('q', '')
    try:
        if not q:
            return jsonify([])

        results = Producto.query.filter(
            Producto.disponible.is_(True),
            Producto.nombre.ilike(f"%{q}%")
        ).order_by(Producto.nombre.asc()).limit(10).all()

        suggestions = []
        for p in results:
            categoria_nombre = p.categoria.nombre if p.categoria else None
            suggestions.append({
                "id": p.ID_Producto,
                "nombre": p.nombre,
                "precio": p.precio,
                "imagen": p.imagen,
                "categoria": categoria_nombre
            })
        return jsonify(suggestions)
    except Exception as e:
        app.logger.error(f'Error en autocomplete API: {e}')
        return jsonify([]), 500


# ==================== NOTIFICATIONS (SSE) ====================

@app.route('/notifications/stream')
@login_required
def notifications_stream():
    # Real-time SSE endpoint has been disabled. Return a simple JSON informing clients.
    return jsonify({'status': 'disabled', 'message': 'Real-time notifications have been disabled on this server.'}), 410


# ==================== CARRITO (CON TRACKING) ====================

@app.route('/add_to_cart/<int:producto_id>')
@login_required
def add_to_cart(producto_id):
    try:
        usuario_id = session['user_id']
        producto = Producto.query.get_or_404(producto_id)

        if not producto.disponible or producto.stock <= 0:
            flash(f'{producto.nombre} no está disponible actualmente', 'warning')
            return redirect(url_for('home'))

        item = Carrito.query.filter_by(ID_Users=usuario_id, ID_Producto=producto_id).first()
        cantidad_agregada = 1

        if item:
            if producto.stock >= item.cantidad + 1:
                item.cantidad += 1
            else:
                flash('No hay más stock disponible para este producto', 'warning')
                return redirect(url_for('home'))
        else:
            nuevo = Carrito(ID_Users=usuario_id, ID_Producto=producto_id, cantidad=1)
            db.session.add(nuevo)

        historial = HistorialCarrito(
            ID_Users=usuario_id,
            ID_Producto=producto_id,
            accion='agregar',
            cantidad=cantidad_agregada,
            precio_momento=producto.precio,
            valor_total=producto.precio * cantidad_agregada
        )
        db.session.add(historial)
        db.session.commit()

        actualizar_metricas_usuario(usuario_id)

        if producto.ID_Categoria:
            actualizar_metricas_categoria(producto.ID_Categoria)
        if producto.ID_Subcategoria:
            actualizar_metricas_subcategoria(producto.ID_Subcategoria)

        # compute updated cart count
        try:
            cart_count = Carrito.query.filter_by(ID_Users=usuario_id).count()
        except Exception:
            cart_count = 0

        # If AJAX, return JSON and don't flash or send server-side notification (client shows popup)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
            return jsonify({'status': 'ok', 'cart_count': cart_count, 'producto_id': producto.ID_Producto})

        # Only push a server-side notification for non-AJAX requests.
        try:
            notify_user(usuario_id, {
                'type': 'cart',
                'text': 'Se agregó un producto al carrito',
                'img': producto.imagen or None
            })
        except Exception:
            pass

        flash(f'✓ {producto.nombre} agregado al carrito', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        flash('Error al agregar el producto al carrito', 'danger')
        app.logger.error(f'Error al agregar al carrito: {str(e)}')
        return redirect(url_for('home'))


@app.route('/cart')
@login_required
def cart():
    usuario_id = session['user_id']
    items = Carrito.query.filter_by(ID_Users=usuario_id).all()

    productos = []
    total = 0.0
    for i in items:
        producto = Producto.query.get(i.ID_Producto)
        if producto:
            subtotal = producto.precio * i.cantidad
            productos.append({
                "ID_Carrito": i.ID_Carrito,
                "ID_Producto": producto.ID_Producto,
                "imagen": producto.imagen,
                "nombre": producto.nombre,
                "precio": producto.precio,
                "cantidad": i.cantidad,
                "subtotal": subtotal,
                "stock_disponible": producto.stock
            })
            total += subtotal

    wallet = Wallet.query.filter_by(ID_Users=usuario_id).first()
    saldo = wallet.saldo if wallet else 0.0

    return render_template('cart.html', productos=productos, total=total, saldo=saldo)


@app.route('/update_cart_quantity/<int:cart_id>', methods=['POST'])
@login_required
def update_cart_quantity(cart_id):
    try:
        usuario_id = session['user_id']
        nueva_cantidad = int(request.form.get('cantidad', 1))

        item = Carrito.query.filter_by(ID_Carrito=cart_id, ID_Users=usuario_id).first_or_404()
        producto = Producto.query.get(item.ID_Producto)

        if not producto.disponible:
            flash('Producto no disponible', 'warning')
            return redirect(url_for('cart'))

        removed_flag = False
        if nueva_cantidad <= 0:
            historial = HistorialCarrito(
                ID_Users=usuario_id,
                ID_Producto=item.ID_Producto,
                accion='quitar',
                cantidad=item.cantidad,
                precio_momento=producto.precio,
                valor_total=producto.precio * item.cantidad
            )
            db.session.add(historial)
            db.session.delete(item)
            removed_flag = True
            flash('Producto eliminado del carrito', 'info')

        elif nueva_cantidad > producto.stock:
            flash(f'Solo hay {producto.stock} unidades disponibles', 'warning')

        else:
            diferencia = nueva_cantidad - item.cantidad

            if diferencia > 0:
                historial = HistorialCarrito(
                    ID_Users=usuario_id,
                    ID_Producto=item.ID_Producto,
                    accion='agregar',
                    cantidad=diferencia,
                    precio_momento=producto.precio,
                    valor_total=producto.precio * diferencia
                )
            else:
                historial = HistorialCarrito(
                    ID_Users=usuario_id,
                    ID_Producto=item.ID_Producto,
                    accion='quitar',
                    cantidad=abs(diferencia),
                    precio_momento=producto.precio,
                    valor_total=producto.precio * abs(diferencia)
                )

            db.session.add(historial)
            item.cantidad = nueva_cantidad
            flash('Cantidad actualizada', 'success')

        db.session.commit()
        actualizar_metricas_usuario(usuario_id)

        # Notify via SSE and return JSON if AJAX
        try:
            cart_count = Carrito.query.filter_by(ID_Users=usuario_id).count()
        except Exception:
            cart_count = 0

        # Choose action type based on whether item was removed
        action_type = 'removed' if removed_flag else 'quantity_changed'
        producto_id_for_notify = item.ID_Producto if not removed_flag else (item.ID_Producto if item and hasattr(item, 'ID_Producto') else None)
        try:
            notify_user(usuario_id, {
                'type': 'cart_update',
                'action': action_type,
                'cart_id': cart_id,
                'producto_id': producto_id_for_notify,
                'new_quantity': None if removed_flag else nueva_cantidad,
                'cart_count': cart_count
            })
        except Exception:
            pass

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
            # compute new subtotal and total
            try:
                productos = Carrito.query.filter_by(ID_Users=usuario_id).all()
                total = 0.0
                for it in productos:
                    prod = Producto.query.get(it.ID_Producto)
                    if prod:
                        total += (prod.precio * it.cantidad)
                if removed_flag:
                    return jsonify({'status': 'removed', 'cart_id': cart_id, 'producto_id': producto_id_for_notify, 'cart_count': cart_count, 'total': total})
                return jsonify({'status': 'ok', 'cart_id': cart_id, 'new_quantity': nueva_cantidad, 'cart_count': cart_count, 'total': total})
            except Exception:
                if removed_flag:
                    return jsonify({'status': 'removed', 'cart_id': cart_id, 'producto_id': producto_id_for_notify, 'cart_count': cart_count})
                return jsonify({'status': 'ok', 'cart_id': cart_id, 'new_quantity': nueva_cantidad, 'cart_count': cart_count})

    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar cantidad', 'danger')
        app.logger.error(f'Error al actualizar cantidad: {str(e)}')

    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    try:
        usuario_id = session['user_id']
        item = Carrito.query.filter_by(ID_Carrito=cart_id, ID_Users=usuario_id).first_or_404()
        producto = Producto.query.get(item.ID_Producto)

        historial = HistorialCarrito(
            ID_Users=usuario_id,
            ID_Producto=item.ID_Producto,
            accion='quitar',
            cantidad=item.cantidad,
            precio_momento=producto.precio if producto else 0,
            valor_total=(producto.precio * item.cantidad) if producto else 0
        )
        db.session.add(historial)

        db.session.delete(item)
        db.session.commit()

        actualizar_metricas_usuario(usuario_id)

        # If AJAX request, return JSON and send SSE update
        try:
            cart_count = Carrito.query.filter_by(ID_Users=usuario_id).count()
        except Exception:
            cart_count = 0

        try:
            notify_user(usuario_id, {
                'type': 'cart_update',
                'action': 'removed',
                'cart_id': cart_id,
                'producto_id': producto.ID_Producto if producto else None,
                'cart_count': cart_count
            })
        except Exception:
            pass

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
            return jsonify({'status': 'removed', 'cart_id': cart_id, 'producto_id': producto.ID_Producto if producto else None, 'cart_count': cart_count})

        flash('Item eliminado del carrito', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar item', 'danger')
        app.logger.error(f'Error al eliminar item: {str(e)}')

    return redirect(url_for('cart'))


@app.route('/clear_cart')
@login_required
def clear_cart():
    """VACIAR CARRITO = ABANDONAR"""
    try:
        usuario_id = session['user_id']
        items = Carrito.query.filter_by(ID_Users=usuario_id).all()

        for item in items:
            producto = Producto.query.get(item.ID_Producto)
            historial = HistorialCarrito(
                ID_Users=usuario_id,
                ID_Producto=item.ID_Producto,
                accion='abandonar',
                cantidad=item.cantidad,
                precio_momento=producto.precio if producto else 0,
                valor_total=(producto.precio * item.cantidad) if producto else 0
            )
            db.session.add(historial)

        Carrito.query.filter_by(ID_Users=usuario_id).delete()
        db.session.commit()

        actualizar_metricas_usuario(usuario_id)

        flash('Carrito vaciado', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Error al vaciar carrito', 'danger')
        app.logger.error(f'Error al vaciar carrito: {str(e)}')

    return redirect(url_for('cart'))


@app.route('/comprar', methods=['POST'])
@login_required
def comprar():
    usuario_id = session['user_id']
    try:
        items = Carrito.query.filter_by(ID_Users=usuario_id).all()
        if not items:
            flash("Tu carrito está vacío", "warning")
            return redirect(url_for('cart'))

        total = 0.0
        for item in items:
            producto = Producto.query.get(item.ID_Producto)
            if not producto:
                flash("Un producto en tu carrito ya no existe", "danger")
                return redirect(url_for('cart'))
            if producto.stock < item.cantidad:
                flash(f'Stock insuficiente para {producto.nombre}', 'danger')
                return redirect(url_for('cart'))
            total += producto.precio * item.cantidad

        wallet = Wallet.query.filter_by(ID_Users=usuario_id).first()

        if not wallet or wallet.saldo < total:
            saldo_faltante = total - (wallet.saldo if wallet else 0)
            flash(f'Saldo insuficiente. Te faltan ${saldo_faltante:.2f}. Por favor recarga tu wallet.', 'danger')
            return redirect(url_for('wallet'))

        saldo_anterior = wallet.saldo
        wallet.saldo -= total

        pedido = Pedido(ID_Users=usuario_id, total=total)
        db.session.add(pedido)
        db.session.flush()

        transaccion = TransaccionWallet(
            ID_Wallet=wallet.ID_Wallet,
            ID_Users=usuario_id,
            tipo='compra',
            monto=-total,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=wallet.saldo,
            descripcion=f'Compra - Pedido #{pedido.ID_Pedido}',
            ID_Pedido=pedido.ID_Pedido
        )
        db.session.add(transaccion)

        categorias_afectadas = set()
        subcategorias_afectadas = set()

        for item in items:
            producto = Producto.query.get(item.ID_Producto)

            detalle = DetallePedido(
                ID_Pedido=pedido.ID_Pedido,
                ID_Producto=producto.ID_Producto,
                cantidad=item.cantidad,
                precio_unitario=producto.precio
            )
            db.session.add(detalle)

            producto.stock -= item.cantidad

            historial_compra = HistorialCarrito(
                ID_Users=usuario_id,
                ID_Producto=producto.ID_Producto,
                accion='comprar',
                cantidad=item.cantidad,
                precio_momento=producto.precio,
                valor_total=producto.precio * item.cantidad,
                ID_Pedido=pedido.ID_Pedido
            )
            db.session.add(historial_compra)

            if producto.ID_Categoria:
                categorias_afectadas.add(producto.ID_Categoria)
            if producto.ID_Subcategoria:
                subcategorias_afectadas.add(producto.ID_Subcategoria)

        Carrito.query.filter_by(ID_Users=usuario_id).delete()

        db.session.commit()

        actualizar_metricas_usuario(usuario_id)

        for cat_id in categorias_afectadas:
            actualizar_metricas_categoria(cat_id)

        for sub_id in subcategorias_afectadas:
            actualizar_metricas_subcategoria(sub_id)

        try:
            notify_user(usuario_id, f'Compra realizada. Pedido #{pedido.ID_Pedido}')
        except Exception:
            pass

        flash(f"✓ Compra realizada con éxito. Pedido #{pedido.ID_Pedido}", "success")
        return redirect(url_for('historial'))

    except Exception as e:
        db.session.rollback()
        flash("Error al procesar la compra", "danger")
        app.logger.error(f'Error en comprar: {str(e)}')
        return redirect(url_for('cart'))


@app.route('/historial')
@login_required
def historial():
    usuario_id = session['user_id']
    pedidos = Pedido.query.filter_by(ID_Users=usuario_id).order_by(Pedido.fecha.desc()).all()
    return render_template("historial.html", pedidos=pedidos)


@app.route('/historial_acciones')
@login_required
def historial_acciones():
    # Server-side: return the user's persisted actions (last 50) and render page.
    try:
        usuario_id = session.get('user_id')
        server_actions = ActionHistory.query.filter_by(ID_Users=usuario_id).order_by(ActionHistory.fecha.desc()).limit(50).all()
        actions = []
        for a in server_actions:
            actions.append({
                'id': a.ID_Action,
                'accion': a.accion,
                'nombre': a.nombre,
                'producto_id': a.producto_id,
                'meta': a.meta,
                'fecha': a.fecha.isoformat() if a.fecha else None
            })
        return render_template('historial_acciones.html', server_actions=actions)
    except Exception as e:
        app.logger.error(f'Error cargando historial de acciones del usuario: {e}')
        # Fallback: render the client-side only page
        return render_template('historial_acciones.html')


# ==================== PRODUCT DETAIL ====================

@app.route('/product/<int:producto_id>')
def product_detail(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    categoria = Categoria.query.get(producto.ID_Categoria) if producto.ID_Categoria else None
    subcategoria = Subcategoria.query.get(producto.ID_Subcategoria) if producto.ID_Subcategoria else None

    related_products = []
    if producto.ID_Categoria:
        related_products = Producto.query.filter(
            Producto.ID_Categoria == producto.ID_Categoria,
            Producto.ID_Producto != producto.ID_Producto,
            Producto.disponible.is_(True)
        ).order_by(Producto.nombre.asc()).limit(6).all()

    return render_template('product.html', producto=producto, categoria=categoria,
                         subcategoria=subcategoria, related_products=related_products)


@app.route('/api/log_action', methods=['POST'])
def api_log_action():
    """Endpoint para recibir logs de acciones desde el cliente.
    Se acepta JSON con campos: action/accion (string), producto_id (int), nombre (string), meta (obj)
    Si el usuario está en sesión se registra su ID en la fila.
    """
    try:
        data = request.get_json(silent=True) or {}
        accion = data.get('accion') or data.get('action')
        producto_id = data.get('producto_id') or data.get('ID_Producto')
        nombre = data.get('nombre') or data.get('name')
        meta_obj = data.get('meta')
        meta = json.dumps(meta_obj) if meta_obj is not None else None
        user_id = session.get('user_id')

        if not accion:
            return jsonify({'error': 'accion missing'}), 400

        ah = ActionHistory(
            ID_Users=user_id,
            accion=accion,
            producto_id=producto_id,
            nombre=nombre,
            meta=meta
        )
        db.session.add(ah)
        db.session.commit()

        return jsonify({'status': 'ok', 'id': ah.ID_Action})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error en /api/log_action: {e}')
        return jsonify({'error': 'server error'}), 500


@app.route('/admin/historial_acciones')
@admin_required
def admin_historial_acciones():
    page = request.args.get('page', 1, type=int)
    per_page = 25
    try:
        query = ActionHistory.query.order_by(ActionHistory.fecha.desc())
        pag = query.paginate(page=page, per_page=per_page, error_out=False)
        return render_template('admin/historial_acciones.html', actions=pag)
    except Exception as e:
        app.logger.error(f'Error al mostrar historial de acciones: {e}')
        flash('No se pudo cargar el historial de acciones', 'danger')
        return redirect(url_for('admin_dashboard'))


# ==================== WALLET (CON TRACKING) ====================

@app.route('/wallet')
@login_required
def wallet():
    usuario_id = session['user_id']
    wallet = Wallet.query.filter_by(ID_Users=usuario_id).first()
    return render_template('wallet.html', wallet=wallet)


@app.route('/recargar_saldo', methods=['POST'])
@login_required
def recargar_saldo():
    try:
        usuario_id = session['user_id']
        monto = float(request.form.get('monto', 0))

        if monto <= 0:
            flash('El monto debe ser mayor a 0', 'warning')
            return redirect(url_for('wallet'))

        if monto < ValidationLimits.MIN_RECARGA:
            flash(f'El monto mínimo de recarga es ${ValidationLimits.MIN_RECARGA}', 'warning')
            return redirect(url_for('wallet'))

        if monto > ValidationLimits.MAX_RECARGA:
            flash(f'El monto máximo es ${ValidationLimits.MAX_RECARGA:,}', 'warning')
            return redirect(url_for('wallet'))

        wallet = Wallet.query.filter_by(ID_Users=usuario_id).first()
        saldo_anterior = wallet.saldo
        wallet.saldo += monto

        transaccion = TransaccionWallet(
            ID_Wallet=wallet.ID_Wallet,
            ID_Users=usuario_id,
            tipo='recarga',
            monto=monto,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=wallet.saldo,
            descripcion='Recarga de saldo'
        )
        db.session.add(transaccion)
        db.session.commit()

        actualizar_metricas_usuario(usuario_id)

        try:
            notify_user(usuario_id, f'Se recargaron ${monto:.2f} en tu wallet')
        except Exception:
            pass

        flash(f'¡Saldo recargado! Se agregaron ${monto:.2f} a tu wallet', 'success')
        return redirect(url_for('wallet'))

    except Exception as e:
        db.session.rollback()
        flash('Error al recargar saldo', 'danger')
        app.logger.error(f'Error al recargar saldo: {str(e)}')
        return redirect(url_for('wallet'))


# ==================== MI PERFIL ====================

@app.route('/perfil')
@login_required
def perfil():
    usuario_id = session['user_id']
    usuario = Usuario.query.get_or_404(usuario_id)
    wallet = Wallet.query.filter_by(ID_Users=usuario_id).first()

    total_pedidos = Pedido.query.filter_by(ID_Users=usuario_id).count()

    ultimos_pedidos = Pedido.query.filter_by(ID_Users=usuario_id)\
        .order_by(Pedido.fecha.desc()).limit(5).all()

    ultimas_transacciones = TransaccionWallet.query.filter_by(ID_Users=usuario_id)\
        .order_by(TransaccionWallet.fecha.desc()).limit(5).all()

    return render_template('perfil.html',
                         usuario=usuario,
                         wallet=wallet,
                         total_pedidos=total_pedidos,
                         ultimos_pedidos=ultimos_pedidos,
                         ultimas_transacciones=ultimas_transacciones)


@app.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    usuario_id = session['user_id']
    usuario = Usuario.query.get_or_404(usuario_id)

    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            password_actual = request.form.get('password_actual')
            password_nueva = request.form.get('password_nueva')

            if nombre and len(nombre) >= ValidationLimits.MIN_NOMBRE_LENGTH:
                usuario.nombre = nombre
                session['user_name'] = nombre

            if email and email != usuario.email:
                existe = Usuario.query.filter_by(email=email).first()
                if existe:
                    flash('Este email ya está registrado', 'danger')
                    return redirect(url_for('editar_perfil'))
                usuario.email = email
                session['user_email'] = email

            if password_actual and password_nueva:
                if check_password_hash(usuario.password, password_actual):
                    if len(password_nueva) >= ValidationLimits.MIN_PASSWORD_LENGTH:
                        usuario.password = generate_password_hash(password_nueva, method='pbkdf2:sha256')
                        flash('Contraseña actualizada correctamente', 'success')
                    else:
                        flash(f'La nueva contraseña debe tener al menos {ValidationLimits.MIN_PASSWORD_LENGTH} caracteres', 'warning')
                else:
                    flash('La contraseña actual es incorrecta', 'danger')
                    return redirect(url_for('editar_perfil'))

            db.session.commit()
            flash('Perfil actualizado correctamente', 'success')
            return redirect(url_for('perfil'))

        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar perfil', 'danger')
            app.logger.error(f'Error al actualizar perfil: {str(e)}')

    return render_template('editar_perfil.html', usuario=usuario)


# ==================== WISHLIST ====================

@app.route('/add_to_wishlist/<int:producto_id>')
@login_required
def add_to_wishlist(producto_id):
    try:
        usuario_id = session['user_id']
        producto = Producto.query.get_or_404(producto_id)

        existente = Wishlist.query.filter_by(
            ID_Users=usuario_id,
            ID_Producto=producto_id
        ).first()

        if existente:
            flash(f'{producto.nombre} ya está en tu lista de deseos', 'info')
            return redirect(url_for('home'))

        nuevo_item = Wishlist(ID_Users=usuario_id, ID_Producto=producto_id)
        db.session.add(nuevo_item)
        db.session.commit()

        # Si es petición AJAX, devolver JSON con nuevo contador
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
            try:
                wishlist_total = Wishlist.query.filter_by(ID_Users=usuario_id).count()
            except Exception:
                wishlist_total = 0
            return jsonify({
                'status': 'added',
                'producto_id': producto_id,
                'wishlist_count': wishlist_total
            })

        flash(f'✓ {producto.nombre} agregado a tu lista de deseos', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        db.session.rollback()
        flash('Error al agregar a la lista de deseos', 'danger')
        app.logger.error(f'Error al agregar a wishlist: {str(e)}')
        return redirect(url_for('home'))


@app.route('/remove_from_wishlist/<int:producto_id>')
@login_required
def remove_from_wishlist(producto_id):
    try:
        usuario_id = session['user_id']
        item = Wishlist.query.filter_by(
            ID_Users=usuario_id,
            ID_Producto=producto_id
        ).first_or_404()

        db.session.delete(item)
        db.session.commit()

        # Responder JSON para peticiones AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
            try:
                wishlist_total = Wishlist.query.filter_by(ID_Users=usuario_id).count()
            except Exception:
                wishlist_total = 0
            return jsonify({
                'status': 'removed',
                'producto_id': producto_id,
                'wishlist_count': wishlist_total
            })

        flash('Producto eliminado de tu lista de deseos', 'info')
        return redirect(url_for('wishlist'))

    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar de la lista de deseos', 'danger')
        app.logger.error(f'Error al eliminar de wishlist: {str(e)}')
        return redirect(url_for('wishlist'))


@app.route('/wishlist')
@login_required
def wishlist():
    usuario_id = session['user_id']
    wishlist_items = Wishlist.query.filter_by(ID_Users=usuario_id).all()

    productos = []
    for item in wishlist_items:
        producto = Producto.query.get(item.ID_Producto)
        if producto:
            productos.append({
                "ID_Producto": producto.ID_Producto,
                "nombre": producto.nombre,
                "precio": producto.precio,
                "imagen": producto.imagen,
                "disponible": producto.disponible,
                "stock": producto.stock,
                "fecha_agregado": item.fecha_agregado
            })

    return render_template('wishlist.html', productos=productos)


@app.route('/wishlist_to_cart/<int:producto_id>')
@login_required
def wishlist_to_cart(producto_id):
    """Mover producto de wishlist al carrito"""
    try:
        usuario_id = session['user_id']

        wishlist_item = Wishlist.query.filter_by(
            ID_Users=usuario_id,
            ID_Producto=producto_id
        ).first_or_404()

        producto = Producto.query.get_or_404(producto_id)

        item_carrito = Carrito.query.filter_by(
            ID_Users=usuario_id,
            ID_Producto=producto_id
        ).first()

        if item_carrito:
            if producto.stock >= item_carrito.cantidad + 1:
                item_carrito.cantidad += 1
            else:
                flash('No hay suficiente stock disponible', 'warning')
                return redirect(url_for('wishlist'))
        else:
            nuevo_carrito = Carrito(ID_Users=usuario_id, ID_Producto=producto_id, cantidad=1)
            db.session.add(nuevo_carrito)

        historial = HistorialCarrito(
            ID_Users=usuario_id,
            ID_Producto=producto_id,
            accion='agregar',
            cantidad=1,
            precio_momento=producto.precio,
            valor_total=producto.precio
        )
        db.session.add(historial)

        db.session.delete(wishlist_item)
        db.session.commit()

        actualizar_metricas_usuario(usuario_id)

        try:
            notify_user(usuario_id, f'"{producto.nombre}" movido de wishlist al carrito')
        except Exception:
            pass

        flash(f'✓ {producto.nombre} movido al carrito', 'success')
        return redirect(url_for('wishlist'))

    except Exception as e:
        db.session.rollback()
        flash('Error al mover producto al carrito', 'danger')
        app.logger.error(f'Error en wishlist_to_cart: {str(e)}')
        return redirect(url_for('wishlist'))


# ==================== PANEL DE ADMINISTRACIÓN ====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_usuarios = Usuario.query.count()
    total_productos = Producto.query.count()
    total_pedidos = Pedido.query.count()
    total_ventas = db.session.query(db.func.sum(Pedido.total)).scalar() or 0

    pedidos_recientes = Pedido.query.order_by(Pedido.fecha.desc()).limit(5).all()

    # ✅ NUEVOS DATOS PARA GRÁFICA COMPARATIVA
    # Métricas generales
    total_productos_vendidos = db.session.query(
        db.func.sum(DetallePedido.cantidad)
    ).scalar() or 0

    total_abandonos = db.session.query(
        db.func.sum(HistorialCarrito.cantidad)
    ).filter(HistorialCarrito.accion == 'abandonar').scalar() or 0

    productos_en_carritos = db.session.query(
        db.func.sum(Carrito.cantidad)
    ).scalar() or 0

    # Datos para gráfica de los últimos 30 días
    hace_30_dias = datetime.utcnow() - timedelta(days=30)

    # Ventas por día
    ventas_diarias = db.session.query(
        db.func.date(Pedido.fecha).label('fecha'),
        db.func.coalesce(db.func.sum(DetallePedido.cantidad), 0).label('vendidos')
    ).join(DetallePedido).filter(
        Pedido.fecha >= hace_30_dias
    ).group_by(db.func.date(Pedido.fecha)).order_by('fecha').all()

    # Abandonos por día
    abandonos_diarios = db.session.query(
        db.func.date(HistorialCarrito.fecha).label('fecha'),
        db.func.coalesce(db.func.sum(HistorialCarrito.cantidad), 0).label('abandonados')
    ).filter(
        HistorialCarrito.accion == 'abandonar',
        HistorialCarrito.fecha >= hace_30_dias
    ).group_by(db.func.date(HistorialCarrito.fecha)).order_by('fecha').all()

    # Métricas de categorías para el dashboard
    categorias_metricas = []
    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.orden).all()

    for cat in categorias:
        metricas = MetricaCategoria.query.filter_by(ID_Categoria=cat.ID_Categoria).first()
        categorias_metricas.append({
            'nombre': cat.nombre,
            'icono': cat.icono,
            'productos_activos': metricas.productos_activos if metricas else Producto.query.filter_by(ID_Categoria=cat.ID_Categoria, disponible=True).count(),
            'total_vendidos': metricas.total_productos_vendidos if metricas else 0,
            'ingresos': metricas.ingresos_totales if metricas else 0,
            'tasa_conversion': metricas.tasa_conversion if metricas else 0
        })

    now = datetime.utcnow()
    last7 = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    last30 = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    last90 = (now - timedelta(days=90)).strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%d')

    return render_template('admin/dashboard.html',
                         total_usuarios=total_usuarios,
                         total_productos=total_productos,
                         total_pedidos=total_pedidos,
                         total_ventas=total_ventas,
                         pedidos_recientes=pedidos_recientes,
                         categorias_metricas=categorias_metricas,
                         # ✅ Nuevos datos para gráfica
                         total_productos_vendidos=total_productos_vendidos,
                         total_abandonos=total_abandonos,
                         productos_en_carritos=productos_en_carritos,
                         ventas_diarias=ventas_diarias,
                         abandonos_diarios=abandonos_diarios,
                         now=now_str,
                         last7=last7,
                         last30=last30,
                         last90=last90)


@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@app.route('/admin/productos')
@admin_required
def admin_productos():
    productos = Producto.query.all()
    return render_template('admin/productos.html', productos=productos)


@app.route('/admin/productos/eliminar/<int:producto_id>')
@admin_required
def admin_eliminar_producto(producto_id):
    try:
        producto = Producto.query.get_or_404(producto_id)

        detalle_existente = DetallePedido.query.filter_by(ID_Producto=producto_id).first()
        if detalle_existente:
            flash('No se puede eliminar este producto porque pertenece a pedidos históricos.', 'danger')
            return redirect(url_for('admin_productos'))

        Carrito.query.filter_by(ID_Producto=producto_id).delete()
        Wishlist.query.filter_by(ID_Producto=producto_id).delete()
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar producto', 'danger')
        app.logger.error(f'Error al eliminar producto: {str(e)}')

    return redirect(url_for('admin_productos'))


@app.route('/admin/pedidos')
@admin_required
def admin_pedidos():
    pedidos = Pedido.query.order_by(Pedido.fecha.desc()).all()
    return render_template('admin/pedidos.html', pedidos=pedidos)


@app.route('/admin/usuarios/agregar_saldo/<int:usuario_id>', methods=['POST'])
@admin_required
def admin_agregar_saldo(usuario_id):
    try:
        monto = float(request.form.get('monto', 0))
        wallet = Wallet.query.filter_by(ID_Users=usuario_id).first()

        if wallet and monto > 0:
            saldo_anterior = wallet.saldo
            wallet.saldo += monto

            transaccion = TransaccionWallet(
                ID_Wallet=wallet.ID_Wallet,
                ID_Users=usuario_id,
                tipo='admin',
                monto=monto,
                saldo_anterior=saldo_anterior,
                saldo_nuevo=wallet.saldo,
                descripcion='Recarga administrativa por admin'
            )
            db.session.add(transaccion)
            db.session.commit()

            actualizar_metricas_usuario(usuario_id)

            try:
                notify_user(usuario_id, f'Se agregó saldo por un admin: ${monto:.2f}')
            except Exception:
                pass

            flash('Saldo agregado exitosamente', 'success')
        else:
            flash('Wallet no encontrada o monto inválido', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('Error al agregar saldo', 'danger')
        app.logger.error(f'Error al agregar saldo: {str(e)}')

    return redirect(url_for('admin_usuarios'))


# ==========================================
# GESTIÓN DE CATEGORÍAS - ADMIN
# ==========================================

@app.route('/admin/categorias')
@admin_required
def admin_categorias():
    categorias = Categoria.query.order_by(Categoria.orden, Categoria.nombre).all()
    return render_template('admin/categorias.html', categorias=categorias)


@app.route('/admin/categorias/referencia')
@admin_required
def admin_categorias_referencia():
    categorias = Categoria.query.order_by(Categoria.orden, Categoria.nombre).all()
    return render_template('admin/categorias_referencia.html', categorias=categorias)


@app.route('/admin/categorias/agregar', methods=['GET', 'POST'])
@admin_required
def admin_agregar_categoria():
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            icono = request.form.get('icono', 'fa-box')
            orden = int(request.form.get('orden', 0))
            activa = request.form.get('activa', 'on') == 'on'

            existe = Categoria.query.filter_by(nombre=nombre).first()
            if existe:
                flash(f'Ya existe una categoría con el nombre "{nombre}"', 'warning')
                return redirect(url_for('admin_agregar_categoria'))

            nueva_categoria = Categoria(
                nombre=nombre,
                descripcion=descripcion,
                icono=icono,
                orden=orden,
                activa=activa
            )

            db.session.add(nueva_categoria)
            db.session.commit()

            metricas = MetricaCategoria(ID_Categoria=nueva_categoria.ID_Categoria)
            db.session.add(metricas)
            db.session.commit()

            flash(f'✓ Categoría "{nombre}" creada exitosamente', 'success')
            return redirect(url_for('admin_categorias'))

        except ValueError as e:
            flash(f'Error en los datos: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear categoría: {str(e)}', 'danger')
            app.logger.error(f'Error al crear categoría: {str(e)}')

    return render_template('admin/agregar_categoria.html')


@app.route('/admin/categorias/editar/<int:categoria_id>', methods=['GET', 'POST'])
@admin_required
def admin_editar_categoria(categoria_id):
    categoria = Categoria.query.get_or_404(categoria_id)

    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')

            existe = Categoria.query.filter(
                Categoria.nombre == nombre,
                Categoria.ID_Categoria != categoria_id
            ).first()

            if existe:
                flash(f'Ya existe otra categoría con el nombre "{nombre}"', 'warning')
                return redirect(url_for('admin_editar_categoria', categoria_id=categoria_id))

            categoria.nombre = nombre
            categoria.descripcion = request.form.get('descripcion')
            categoria.icono = request.form.get('icono', 'fa-box')
            categoria.orden = int(request.form.get('orden', 0))
            categoria.activa = request.form.get('activa') == 'on'

            db.session.commit()
            flash(f'✓ Categoría "{nombre}" actualizada exitosamente', 'success')
            return redirect(url_for('admin_categorias'))

        except ValueError as e:
            flash(f'Error en los datos: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar categoría: {str(e)}', 'danger')
            app.logger.error(f'Error al actualizar categoría: {str(e)}')

    return render_template('admin/editar_categoria.html', categoria=categoria)


@app.route('/admin/categorias/eliminar/<int:categoria_id>')
@admin_required
def admin_eliminar_categoria(categoria_id):
    try:
        categoria = Categoria.query.get_or_404(categoria_id)

        productos_count = Producto.query.filter_by(ID_Categoria=categoria_id).count()
        if productos_count > 0:
            flash(f'No se puede eliminar: la categoría "{categoria.nombre}" tiene {productos_count} producto(s) asociado(s)', 'danger')
            return redirect(url_for('admin_categorias'))

        nombre = categoria.nombre
        db.session.delete(categoria)
        db.session.commit()

        flash(f'✓ Categoría "{nombre}" eliminada exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar categoría: {str(e)}', 'danger')
        app.logger.error(f'Error al eliminar categoría: {str(e)}')

    return redirect(url_for('admin_categorias'))


# ==========================================
# GESTIÓN DE SUBCATEGORÍAS - ADMIN
# ==========================================

@app.route('/admin/subcategorias/agregar', methods=['GET', 'POST'])
@admin_required
def admin_agregar_subcategoria():
    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()

    if request.method == 'POST':
        try:
            ID_Categoria = int(request.form.get('ID_Categoria'))
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            orden = int(request.form.get('orden', 0))
            activa = request.form.get('activa', 'on') == 'on'

            categoria_padre = Categoria.query.get(ID_Categoria)
            if not categoria_padre:
                flash('La categoría seleccionada no existe', 'danger')
                return redirect(url_for('admin_agregar_subcategoria'))

            existe = Subcategoria.query.filter_by(
                ID_Categoria=ID_Categoria,
                nombre=nombre
            ).first()

            if existe:
                flash(f'Ya existe una subcategoría "{nombre}" en la categoría "{categoria_padre.nombre}"', 'warning')
                return redirect(url_for('admin_agregar_subcategoria'))

            nueva_subcategoria = Subcategoria(
                ID_Categoria=ID_Categoria,
                nombre=nombre,
                descripcion=descripcion,
                orden=orden,
                activa=activa
            )

            db.session.add(nueva_subcategoria)
            db.session.commit()

            metricas = MetricaSubcategoria(
                ID_Subcategoria=nueva_subcategoria.ID_Subcategoria,
                ID_Categoria=ID_Categoria
            )
            db.session.add(metricas)
            db.session.commit()

            flash(f'✓ Subcategoría "{nombre}" creada en "{categoria_padre.nombre}"', 'success')
            return redirect(url_for('admin_categorias'))

        except ValueError as e:
            flash(f'Error en los datos: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear subcategoría: {str(e)}', 'danger')
            app.logger.error(f'Error al crear subcategoría: {str(e)}')

    return render_template('admin/agregar_subcategoria.html', categorias=categorias)


@app.route('/admin/subcategorias/editar/<int:subcategoria_id>', methods=['GET', 'POST'])
@admin_required
def admin_editar_subcategoria(subcategoria_id):
    subcategoria = Subcategoria.query.get_or_404(subcategoria_id)
    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()

    if request.method == 'POST':
        try:
            ID_Categoria = int(request.form.get('ID_Categoria'))
            nombre = request.form.get('nombre')

            existe = Subcategoria.query.filter(
                Subcategoria.ID_Categoria == ID_Categoria,
                Subcategoria.nombre == nombre,
                Subcategoria.ID_Subcategoria != subcategoria_id
            ).first()

            if existe:
                flash(f'Ya existe otra subcategoría con el nombre "{nombre}" en esta categoría', 'warning')
                return redirect(url_for('admin_editar_subcategoria', subcategoria_id=subcategoria_id))

            subcategoria.ID_Categoria = ID_Categoria
            subcategoria.nombre = nombre
            subcategoria.descripcion = request.form.get('descripcion')
            subcategoria.orden = int(request.form.get('orden', 0))
            subcategoria.activa = request.form.get('activa') == 'on'

            metricas = MetricaSubcategoria.query.filter_by(ID_Subcategoria=subcategoria_id).first()
            if metricas:
                metricas.ID_Categoria = ID_Categoria

            db.session.commit()
            flash(f'✓ Subcategoría "{nombre}" actualizada exitosamente', 'success')
            return redirect(url_for('admin_categorias'))

        except ValueError as e:
            flash(f'Error en los datos: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar subcategoría: {str(e)}', 'danger')
            app.logger.error(f'Error al actualizar subcategoría: {str(e)}')

    return render_template('admin/editar_subcategoria.html',
                         subcategoria=subcategoria,
                         categorias=categorias)


@app.route('/admin/subcategorias/eliminar/<int:subcategoria_id>')
@admin_required
def admin_eliminar_subcategoria(subcategoria_id):
    try:
        subcategoria = Subcategoria.query.get_or_404(subcategoria_id)

        productos_count = Producto.query.filter_by(ID_Subcategoria=subcategoria_id).count()
        if productos_count > 0:
            flash(f'No se puede eliminar: la subcategoría "{subcategoria.nombre}" tiene {productos_count} producto(s) asociado(s)', 'danger')
            return redirect(url_for('admin_categorias'))

        nombre = subcategoria.nombre
        db.session.delete(subcategoria)
        db.session.commit()

        flash(f'✓ Subcategoría "{nombre}" eliminada exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar subcategoría: {str(e)}', 'danger')
        app.logger.error(f'Error al eliminar subcategoría: {str(e)}')

    return redirect(url_for('admin_categorias'))


# ==========================================
# GESTIÓN DE PRODUCTOS - ADMIN
# ==========================================

@app.route('/admin/productos/agregar', methods=['GET', 'POST'])
@admin_required
def admin_agregar_producto():
    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.orden, Categoria.nombre).all()

    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            precio = float(request.form.get('precio'))
            stock = int(request.form.get('stock'))
            disponible = request.form.get('disponible') == 'on'

            ID_Categoria = request.form.get('ID_Categoria')
            ID_Subcategoria = request.form.get('ID_Subcategoria')

            if ID_Categoria and ID_Categoria.strip():
                ID_Categoria = int(ID_Categoria)
            else:
                ID_Categoria = None

            if ID_Subcategoria and ID_Subcategoria.strip():
                ID_Subcategoria = int(ID_Subcategoria)
            else:
                ID_Subcategoria = None

            if ID_Subcategoria and not ID_Categoria:
                subcategoria = Subcategoria.query.get(ID_Subcategoria)
                if subcategoria:
                    ID_Categoria = subcategoria.ID_Categoria
                    flash('Se asignó automáticamente la categoría de la subcategoría seleccionada', 'info')

            imagen_file = request.files.get('imagen_file')
            imagen_path = None

            if imagen_file and imagen_file.filename:
                if allowed_file(imagen_file.filename):
                    filename = secure_filename(imagen_file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    imagen_file.save(save_path)
                    imagen_path = f"img/{filename}"
                else:
                    flash('Tipo de archivo no permitido. Use: png, jpg, jpeg, gif, webp', 'warning')
                    return redirect(url_for('admin_agregar_producto'))
            else:
                imagen_path = request.form.get('imagen') or None

            descripcion = request.form.get('descripcion')

            nuevo_producto = Producto(
                nombre=nombre,
                precio=precio,
                stock=stock,
                imagen=imagen_path,
                disponible=disponible,
                ID_Categoria=ID_Categoria,
                ID_Subcategoria=ID_Subcategoria,
                descripcion=descripcion
            )

            db.session.add(nuevo_producto)
            db.session.commit()

            flash(f'✓ Producto "{nombre}" agregado exitosamente', 'success')
            return redirect(url_for('admin_productos'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {str(e)}', 'danger')
            app.logger.error(f'Error de validación en agregar producto: {str(e)}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar producto: {str(e)}', 'danger')
            app.logger.error(f'Error al agregar producto: {str(e)}')

    return render_template('admin/agregar_producto.html', categorias=categorias)


@app.route('/admin/productos/editar/<int:producto_id>', methods=['GET', 'POST'])
@admin_required
def admin_editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.orden, Categoria.nombre).all()

    if request.method == 'POST':
        try:
            producto.nombre = request.form.get('nombre')
            producto.precio = float(request.form.get('precio'))
            producto.stock = int(request.form.get('stock'))
            producto.disponible = request.form.get('disponible') == 'on'
            producto.descripcion = request.form.get('descripcion')

            ID_Categoria = request.form.get('ID_Categoria')
            ID_Subcategoria = request.form.get('ID_Subcategoria')

            if ID_Categoria and ID_Categoria.strip():
                producto.ID_Categoria = int(ID_Categoria)
            else:
                producto.ID_Categoria = None

            if ID_Subcategoria and ID_Subcategoria.strip():
                producto.ID_Subcategoria = int(ID_Subcategoria)
            else:
                producto.ID_Subcategoria = None

            if producto.ID_Subcategoria and not producto.ID_Categoria:
                subcategoria = Subcategoria.query.get(producto.ID_Subcategoria)
                if subcategoria:
                    producto.ID_Categoria = subcategoria.ID_Categoria

            imagen_file = request.files.get('imagen_file')
            if imagen_file and imagen_file.filename:
                if allowed_file(imagen_file.filename):
                    filename = secure_filename(imagen_file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    imagen_file.save(save_path)
                    producto.imagen = f"img/{filename}"
                else:
                    flash('Tipo de archivo no permitido', 'warning')
                    return redirect(url_for('admin_editar_producto', producto_id=producto_id))
            else:
                nueva_url = request.form.get('imagen')
                if nueva_url:
                    producto.imagen = nueva_url

            db.session.commit()
            flash(f'✓ Producto "{producto.nombre}" actualizado exitosamente', 'success')
            return redirect(url_for('admin_productos'))

        except ValueError as e:
            flash(f'Error en los datos: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
            app.logger.error(f'Error al actualizar producto: {str(e)}')

    return render_template('admin/editar_producto.html', producto=producto, categorias=categorias)


# ==========================================
# RUTA HOME (con filtros y paginación)
# ==========================================

@app.route('/home')
def home():
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'nombre')
    categoria_id = request.args.get('categoria', type=int)
    subcategoria_id = request.args.get('subcategoria', type=int)

    query = Producto.query

    if search_query:
        query = query.filter(Producto.nombre.ilike(f'%{search_query}%'))

    if categoria_id == -1:
        query = query.filter(Producto.ID_Categoria.is_(None))
    elif categoria_id:
        query = query.filter(Producto.ID_Categoria == categoria_id)

    if subcategoria_id == -1:
        query = query.filter(Producto.ID_Subcategoria.is_(None))
    elif subcategoria_id:
        query = query.filter(Producto.ID_Subcategoria == subcategoria_id)

    if sort_by == 'precio_asc':
        query = query.order_by(Producto.precio.asc())
    elif sort_by == 'precio_desc':
        query = query.order_by(Producto.precio.desc())
    elif sort_by == 'stock':
        query = query.order_by(Producto.stock.desc())
    else:
        query = query.order_by(Producto.nombre.asc())

    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.orden).all()

    productos_sin_categoria = Producto.query.filter(Producto.ID_Categoria.is_(None)).count()

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = query.filter_by(disponible=True)
    productos = query.paginate(page=page, per_page=per_page, error_out=False)

    # Obtener IDs de wishlist del usuario (para marcar corazones)
    wishlist_ids = set()
    user_id = session.get('user_id')
    if user_id:
        try:
            rows = Wishlist.query.with_entities(Wishlist.ID_Producto).filter_by(ID_Users=user_id).all()
            wishlist_ids = set(r[0] for r in rows)
        except Exception:
            wishlist_ids = set()

    return render_template('home.html',
                         productos=productos,
                         search_query=search_query,
                         sort_by=sort_by,
                         categorias=categorias,
                         categoria_actual=categoria_id,
                         subcategoria_actual=subcategoria_id,
                         productos_sin_categoria=productos_sin_categoria,
                         wishlist_ids=wishlist_ids)


# ==========================================
# API para obtener subcategorías (AJAX)
# ==========================================

@app.route('/api/subcategorias/<int:categoria_id>')
def api_subcategorias(categoria_id):
    """Retorna las subcategorías de una categoría en formato JSON"""
    try:
        subcategorias = Subcategoria.query.filter_by(
            ID_Categoria=categoria_id,
            activa=True
        ).order_by(Subcategoria.orden, Subcategoria.nombre).all()

        return jsonify([sub.to_dict() for sub in subcategorias])
    except Exception as e:
        app.logger.error(f'Error en API subcategorias: {str(e)}')
        return jsonify([]), 500


@app.route('/admin/analytics/categoria/<int:categoria_id>')
@admin_required
def admin_analytics_categoria_detalle(categoria_id):
    try:
        categoria = Categoria.query.get_or_404(categoria_id)
        metricas = MetricaCategoria.query.filter_by(ID_Categoria=categoria_id).first()

        if not metricas:
            actualizar_metricas_categoria(categoria_id)
            metricas = MetricaCategoria.query.filter_by(ID_Categoria=categoria_id).first()

        # Productos de la categoría
        productos = db.session.query(
            Producto.ID_Producto,
            Producto.nombre,
            Producto.imagen,
            Producto.precio,
            Producto.stock,
            db.func.coalesce(db.func.sum(DetallePedido.cantidad), 0).label('total_vendido'),
            db.func.coalesce(db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario), 0).label('ingresos')
        ).outerjoin(
            DetallePedido, DetallePedido.ID_Producto == Producto.ID_Producto
        ).filter(
            Producto.ID_Categoria == categoria_id
        ).group_by(Producto.ID_Producto
        ).order_by(db.desc('total_vendido')
        ).all()

        # Subcategorías
        subcategorias = db.session.query(
            Subcategoria,
            MetricaSubcategoria
        ).outerjoin(
            MetricaSubcategoria, MetricaSubcategoria.ID_Subcategoria == Subcategoria.ID_Subcategoria
        ).filter(
            Subcategoria.ID_Categoria == categoria_id
        ).all()

        # Ventas diarias de la categoría
        hace_30_dias = datetime.utcnow() - timedelta(days=30)
        ventas_diarias = db.session.query(
            db.func.date(Pedido.fecha).label('fecha'),
            db.func.coalesce(db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario), 0).label('ingresos'),
            db.func.coalesce(db.func.sum(DetallePedido.cantidad), 0).label('unidades')
        ).join(
            DetallePedido, DetallePedido.ID_Pedido == Pedido.ID_Pedido
        ).join(
            Producto, Producto.ID_Producto == DetallePedido.ID_Producto
        ).filter(
            Producto.ID_Categoria == categoria_id,
            Pedido.fecha >= hace_30_dias
        ).group_by(db.func.date(Pedido.fecha)
        ).order_by('fecha').all()

        # Top clientes
        top_clientes = db.session.query(
            Usuario.nombre,
            Usuario.email,
            db.func.coalesce(db.func.sum(DetallePedido.cantidad), 0).label('productos_comprados'),
            db.func.coalesce(db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario), 0).label('total_gastado')
        ).join(
            Pedido, Pedido.ID_Users == Usuario.ID_Users
        ).join(
            DetallePedido, DetallePedido.ID_Pedido == Pedido.ID_Pedido
        ).join(
            Producto, Producto.ID_Producto == DetallePedido.ID_Producto
        ).filter(
            Producto.ID_Categoria == categoria_id
        ).group_by(Usuario.ID_Users
        ).order_by(db.desc('total_gastado')
        ).limit(10).all()

        return render_template('admin/analytics_categoria_detalle.html',
            categoria=categoria,
            metricas=metricas,
            productos=productos,
            subcategorias=subcategorias,
            ventas_diarias=ventas_diarias,
            top_clientes=top_clientes
        )

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        app.logger.error(f'Error en detalle categoría: {str(e)}')
        return redirect(url_for('admin_analytics'))


@app.route('/admin/actualizar_metricas_categorias')
@admin_required
def admin_actualizar_metricas_categorias():
    try:
        actualizar_todas_metricas_categorias()
        flash('✓ Métricas de categorías actualizadas exitosamente', 'success')
    except Exception as e:
        flash(f'Error al actualizar métricas: {str(e)}', 'danger')
        app.logger.error(f'Error actualizando métricas: {str(e)}')

    return redirect(url_for('admin_analytics_categorias'))


# ==================== PANEL DE ANALYTICS GENERAL ====================

# ==================== PANEL DE ANALYTICS INTEGRADO (CON CATEGORÍAS) ====================

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    try:
        # === MÉTRICAS GENERALES ===
        total_usuarios = Usuario.query.count()
        total_productos = Producto.query.count()
        total_pedidos = Pedido.query.count()
        total_ventas = db.session.query(db.func.sum(Pedido.total)).scalar() or 0

        ticket_promedio_global = total_ventas / total_pedidos if total_pedidos > 0 else 0

        # === SEGMENTACIÓN DE USUARIOS ===
        usuarios_por_segmento = db.session.query(
            Usuario.segmento_cliente,
            db.func.count(Usuario.ID_Users).label('cantidad')
        ).group_by(Usuario.segmento_cliente).all()

        segmentacion = {seg: cant for seg, cant in usuarios_por_segmento}

        # === TOP CLIENTES ===
        top_clientes = Usuario.query.filter(
            Usuario.total_compras > 0
        ).order_by(Usuario.total_gastado.desc()).limit(10).all()

        # === PRODUCTOS MÁS VENDIDOS ===
        productos_mas_vendidos = db.session.query(
            Producto.nombre,
            Producto.imagen,
            Producto.precio,
            db.func.sum(DetallePedido.cantidad).label('total_vendido'),
            db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario).label('ingresos')
        ).join(DetallePedido, DetallePedido.ID_Producto == Producto.ID_Producto
        ).group_by(Producto.ID_Producto
        ).order_by(db.desc('total_vendido')
        ).limit(10).all()

        # === PRODUCTOS BAJO STOCK ===
        productos_bajo_stock = Producto.query.filter(
            Producto.stock > 0,
            Producto.stock <= 10,
            Producto.disponible == True
        ).order_by(Producto.stock.asc()).limit(10).all()

        # === PRODUCTOS ABANDONADOS ===
        productos_abandonados = db.session.query(
            Producto.nombre,
            Producto.imagen,
            Producto.precio,
            db.func.count(HistorialCarrito.ID_Historial).label('veces_agregado'),
            db.func.sum(HistorialCarrito.valor_total).label('valor_perdido')
        ).join(HistorialCarrito, HistorialCarrito.ID_Producto == Producto.ID_Producto
        ).filter(
            HistorialCarrito.accion == 'abandonar'
        ).group_by(Producto.ID_Producto
        ).order_by(db.desc('valor_perdido')
        ).limit(10).all()

        # === MÉTRICAS DE WALLET ===
        total_recargado = db.session.query(
            db.func.sum(TransaccionWallet.monto)
        ).filter(TransaccionWallet.tipo == 'recarga').scalar() or 0

        total_recargas = db.session.query(
            db.func.count(TransaccionWallet.ID_Transaccion)
        ).filter(TransaccionWallet.tipo == 'recarga').scalar() or 0

        recarga_promedio_global = total_recargado / total_recargas if total_recargas > 0 else 0

        saldo_total_usuarios = db.session.query(
            db.func.sum(Wallet.saldo)
        ).scalar() or 0

        # === MÉTRICAS DE CONVERSIÓN ===
        total_productos_agregados = db.session.query(
            db.func.sum(HistorialCarrito.cantidad)
        ).filter(HistorialCarrito.accion == 'agregar').scalar() or 0

        total_productos_comprados = db.session.query(
            db.func.sum(DetallePedido.cantidad)
        ).scalar() or 0

        tasa_conversion_global = (total_productos_comprados / total_productos_agregados * 100) if total_productos_agregados > 0 else 0

        total_abandonos = db.session.query(
            db.func.count(db.distinct(HistorialCarrito.ID_Users))
        ).filter(HistorialCarrito.accion == 'abandonar').scalar() or 0

        valor_abandonos = db.session.query(
            db.func.sum(HistorialCarrito.valor_total)
        ).filter(HistorialCarrito.accion == 'abandonar').scalar() or 0

        # === VENTAS DIARIAS (ÚLTIMOS 30 DÍAS) ===
        hace_30_dias = datetime.utcnow() - timedelta(days=30)
        ventas_diarias = db.session.query(
            db.func.date(Pedido.fecha).label('fecha'),
            db.func.sum(Pedido.total).label('total_dia'),
            db.func.count(Pedido.ID_Pedido).label('pedidos_dia')
        ).filter(Pedido.fecha >= hace_30_dias
        ).group_by(db.func.date(Pedido.fecha)
        ).order_by('fecha').all()

        # === USUARIOS NUEVOS DIARIOS ===
        usuarios_nuevos_diarios = db.session.query(
            db.func.date(Usuario.fecha_registro).label('fecha'),
            db.func.count(Usuario.ID_Users).label('nuevos')
        ).filter(Usuario.fecha_registro >= hace_30_dias
        ).group_by(db.func.date(Usuario.fecha_registro)
        ).order_by('fecha').all()

        # === PEDIDOS RECIENTES ===
        pedidos_recientes = Pedido.query.order_by(
            Pedido.fecha.desc()
        ).limit(10).all()

        # === USUARIOS ACTIVOS HOY ===
        usuarios_activos_hoy = Usuario.query.filter(
            Usuario.ultima_actividad >= datetime.utcnow() - timedelta(days=1)
        ).count()

        # ✅ === ANALYTICS DE CATEGORÍAS (INTEGRADO) ===

        # Categorías por ingresos
        categorias_por_ingresos = db.session.query(
            Categoria.ID_Categoria,
            Categoria.nombre,
            Categoria.icono,
            MetricaCategoria.ingresos_totales,
            MetricaCategoria.total_productos_vendidos,
            MetricaCategoria.total_pedidos,
            MetricaCategoria.tasa_conversion,
            MetricaCategoria.total_agregados_carrito,
            MetricaCategoria.valor_abandonos
        ).join(
            MetricaCategoria, MetricaCategoria.ID_Categoria == Categoria.ID_Categoria
        ).filter(
            Categoria.activa == True
        ).order_by(MetricaCategoria.ingresos_totales.desc()).all()

        # Mejor conversión
        mejor_conversion = db.session.query(
            Categoria.nombre,
            Categoria.icono,
            MetricaCategoria.tasa_conversion,
            MetricaCategoria.total_agregados_carrito,
            MetricaCategoria.total_productos_vendidos
        ).join(
            MetricaCategoria, MetricaCategoria.ID_Categoria == Categoria.ID_Categoria
        ).filter(
            Categoria.activa == True,
            MetricaCategoria.total_agregados_carrito > 0
        ).order_by(MetricaCategoria.tasa_conversion.desc()).first()

        # Más abandonos
        mas_abandonos = db.session.query(
            Categoria.nombre,
            Categoria.icono,
            MetricaCategoria.valor_abandonos,
            MetricaCategoria.total_abandonos
        ).join(
            MetricaCategoria, MetricaCategoria.ID_Categoria == Categoria.ID_Categoria
        ).filter(
            Categoria.activa == True
        ).order_by(MetricaCategoria.valor_abandonos.desc()).limit(5).all()

        # Top productos por categoría
        productos_top_por_categoria = {}
        categorias = Categoria.query.filter_by(activa=True).all()

        for cat in categorias:
            productos = db.session.query(
                Producto.nombre,
                Producto.imagen,
                Producto.precio,
                db.func.coalesce(db.func.sum(DetallePedido.cantidad), 0).label('total_vendido'),
                db.func.coalesce(db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario), 0).label('ingresos')
            ).outerjoin(
                DetallePedido, DetallePedido.ID_Producto == Producto.ID_Producto
            ).filter(
                Producto.ID_Categoria == cat.ID_Categoria
            ).group_by(Producto.ID_Producto
            ).order_by(db.desc('total_vendido')
            ).limit(10).all()

            if productos and any(p.total_vendido > 0 for p in productos):
                productos_top_por_categoria[cat.nombre] = [p for p in productos if p.total_vendido > 0]

        # Ranking de subcategorías
        subcategorias_ranking = db.session.query(
            Subcategoria.nombre,
            Categoria.nombre.label('categoria_nombre'),
            Categoria.icono,
            MetricaSubcategoria.ingresos_totales,
            MetricaSubcategoria.total_productos_vendidos,
            MetricaSubcategoria.tasa_conversion
        ).join(
            Categoria, Categoria.ID_Categoria == Subcategoria.ID_Categoria
        ).join(
            MetricaSubcategoria, MetricaSubcategoria.ID_Subcategoria == Subcategoria.ID_Subcategoria
        ).filter(
            Subcategoria.activa == True
        ).order_by(MetricaSubcategoria.ingresos_totales.desc()).limit(15).all()

        # Distribución de ventas
        distribucion_ventas = []
        total_ventas_global = db.session.query(
            db.func.sum(MetricaCategoria.ingresos_totales)
        ).scalar() or 1

        for cat in categorias:
            metricas = MetricaCategoria.query.filter_by(ID_Categoria=cat.ID_Categoria).first()
            if metricas and metricas.ingresos_totales > 0:
                porcentaje = (metricas.ingresos_totales / total_ventas_global) * 100
                distribucion_ventas.append({
                    'nombre': cat.nombre,
                    'ingresos': metricas.ingresos_totales,
                    'porcentaje': porcentaje,
                    'icono': cat.icono
                })

        # Productos con mejor conversión
        productos_mejor_conversion = db.session.query(
            Producto.nombre,
            Producto.imagen,
            Categoria.nombre.label('categoria'),
            db.func.coalesce(db.func.sum(DetallePedido.cantidad), 0).label('vendidos'),
            db.func.coalesce(db.func.sum(
                db.case(
                    (HistorialCarrito.accion == 'agregar', HistorialCarrito.cantidad),
                    else_=0
                )
            ), 0).label('agregados')
        ).outerjoin(
            Categoria, Categoria.ID_Categoria == Producto.ID_Categoria
        ).outerjoin(
            DetallePedido, DetallePedido.ID_Producto == Producto.ID_Producto
        ).outerjoin(
            HistorialCarrito, HistorialCarrito.ID_Producto == Producto.ID_Producto
        ).group_by(Producto.ID_Producto).all()

        productos_conversion = []
        for p in productos_mejor_conversion:
            vendidos = p.vendidos or 0
            agregados = p.agregados or 0
            if agregados > 0 and vendidos > 0:
                conversion = (vendidos / agregados) * 100
                productos_conversion.append({
                    'nombre': p.nombre,
                    'imagen': p.imagen,
                    'categoria': p.categoria or 'Sin categoría',
                    'vendidos': vendidos,
                    'agregados': agregados,
                    'conversion': conversion
                })

        productos_conversion.sort(key=lambda x: x['conversion'], reverse=True)
        productos_conversion = productos_conversion[:10]

        # Categorías más agregadas
        categorias_mas_agregadas = db.session.query(
            Categoria.nombre,
            Categoria.icono,
            MetricaCategoria.total_agregados_carrito,
            MetricaCategoria.total_productos_vendidos,
            MetricaCategoria.tasa_conversion
        ).join(
            MetricaCategoria, MetricaCategoria.ID_Categoria == Categoria.ID_Categoria
        ).filter(
            Categoria.activa == True
        ).order_by(MetricaCategoria.total_agregados_carrito.desc()).limit(5).all()

        return render_template('admin/analytics.html',
            # Métricas generales
            total_usuarios=total_usuarios,
            total_productos=total_productos,
            total_pedidos=total_pedidos,
            total_ventas=total_ventas,
            ticket_promedio_global=ticket_promedio_global,
            segmentacion=segmentacion,
            top_clientes=top_clientes,
            productos_mas_vendidos=productos_mas_vendidos,
            productos_bajo_stock=productos_bajo_stock,
            productos_abandonados=productos_abandonados,
            total_recargado=total_recargado,
            total_recargas=total_recargas,
            recarga_promedio_global=recarga_promedio_global,
            saldo_total_usuarios=saldo_total_usuarios,
            tasa_conversion_global=tasa_conversion_global,
            total_abandonos=total_abandonos,
            valor_abandonos=valor_abandonos,
            ventas_diarias=ventas_diarias,
            usuarios_nuevos_diarios=usuarios_nuevos_diarios,
            pedidos_recientes=pedidos_recientes,
            usuarios_activos_hoy=usuarios_activos_hoy,
            # ✅ Analytics de categorías (integrado)
            categorias_por_ingresos=categorias_por_ingresos,
            mejor_conversion=mejor_conversion,
            mas_abandonos=mas_abandonos,
            productos_top_por_categoria=productos_top_por_categoria,
            subcategorias_ranking=subcategorias_ranking,
            distribucion_ventas=distribucion_ventas,
            productos_mejor_conversion=productos_conversion,
            categorias_mas_agregadas=categorias_mas_agregadas
        )

    except Exception as e:
        flash(f'Error al cargar analytics: {str(e)}', 'danger')
        app.logger.error(f'Error en analytics: {str(e)}')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/usuario/<int:usuario_id>/metricas')
@admin_required
def admin_usuario_metricas(usuario_id):
    try:
        usuario = Usuario.query.get_or_404(usuario_id)

        transacciones = TransaccionWallet.query.filter_by(
            ID_Users=usuario_id
        ).order_by(TransaccionWallet.fecha.desc()).limit(50).all()

        recargas = [t for t in transacciones if t.tipo == 'recarga']
        compras = [t for t in transacciones if t.tipo == 'compra']
        admin_recargas = [t for t in transacciones if t.tipo == 'admin']

        historial_carrito = db.session.query(
            HistorialCarrito,
            Producto.nombre.label('producto_nombre')
        ).join(Producto).filter(
            HistorialCarrito.ID_Users == usuario_id
        ).order_by(HistorialCarrito.fecha.desc()).limit(100).all()

        agregados = [(h[0], h[1]) for h in historial_carrito if h[0].accion == 'agregar']
        quitados = [(h[0], h[1]) for h in historial_carrito if h[0].accion == 'quitar']
        comprados = [(h[0], h[1]) for h in historial_carrito if h[0].accion == 'comprar']
        abandonados = [(h[0], h[1]) for h in historial_carrito if h[0].accion == 'abandonar']

        productos_favoritos = db.session.query(
            Producto.nombre,
            Producto.imagen,
            db.func.sum(DetallePedido.cantidad).label('total_comprado'),
            db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario).label('gasto_total')
        ).join(DetallePedido).join(Pedido).filter(
            Pedido.ID_Users == usuario_id
        ).group_by(Producto.ID_Producto).order_by(
            db.desc('total_comprado')
        ).limit(10).all()

        productos_no_comprados = db.session.query(
            Producto.nombre,
            Producto.imagen,
            Producto.precio,
            db.func.sum(HistorialCarrito.cantidad).label('veces_agregado'),
            db.func.sum(HistorialCarrito.valor_total).label('valor_total')
        ).join(HistorialCarrito).filter(
            HistorialCarrito.ID_Users == usuario_id,
            HistorialCarrito.accion == 'abandonar'
        ).group_by(Producto.ID_Producto).order_by(
            db.desc('veces_agregado')
        ).limit(10).all()

        if usuario.total_compras > 1:
            pedidos_fechas = [p.fecha for p in usuario.pedidos]
            pedidos_fechas.sort()
            diferencias = [(pedidos_fechas[i+1] - pedidos_fechas[i]).days for i in range(len(pedidos_fechas)-1)]
            promedio_dias_entre_compras = sum(diferencias) / len(diferencias) if diferencias else 0
        else:
            promedio_dias_entre_compras = 0

        return render_template('admin/usuario_metricas.html',
            usuario=usuario,
            transacciones=transacciones,
            recargas=recargas,
            compras=compras,
            admin_recargas=admin_recargas,
            historial_carrito=historial_carrito,
            agregados=agregados,
            quitados=quitados,
            comprados=comprados,
            abandonados=abandonados,
            productos_favoritos=productos_favoritos,
            productos_no_comprados=productos_no_comprados,
            promedio_dias_entre_compras=promedio_dias_entre_compras
        )

    except Exception as e:
        flash(f'Error al cargar métricas del usuario: {str(e)}', 'danger')
        app.logger.error(f'Error en métricas de usuario: {str(e)}')
        return redirect(url_for('admin_usuarios'))


# ==================== EXPORTAR CSV ====================

@app.route('/admin/exportar/usuarios_csv')
@admin_required
def exportar_usuarios_csv():
    try:
        si = StringIO()
        writer = csv.writer(si)

        writer.writerow([
            'ID_Usuario', 'Nombre', 'Email', 'Fecha_Registro', 'Segmento',
            'Total_Compras', 'Total_Gastado', 'Ticket_Promedio',
            'Total_Recargas', 'Dinero_Recargado', 'Recarga_Promedio',
            'Productos_Carrito_Actual', 'Valor_Carrito_Actual',
            'Total_Productos_Agregados', 'Carritos_Abandonados',
            'Tasa_Conversion', 'Dias_Desde_Ultima_Compra', 'Saldo_Actual'
        ])

        usuarios = Usuario.query.all()
        for u in usuarios:
            writer.writerow([
                u.ID_Users,
                u.nombre,
                u.email,
                u.fecha_registro.strftime('%Y-%m-%d') if u.fecha_registro else '',
                u.segmento_cliente,
                u.total_compras,
                f'{u.total_gastado:.2f}',
                f'{u.ticket_promedio:.2f}',
                u.total_recargas,
                f'{u.dinero_recargado_total:.2f}',
                f'{u.recarga_promedio:.2f}',
                u.productos_carrito_actual,
                f'{u.valor_carrito_actual:.2f}',
                u.productos_agregados_carrito_total,
                u.carritos_abandonados,
                f'{u.tasa_conversion:.2f}',
                u.dias_desde_ultima_compra or '',
                f'{u.wallet.saldo:.2f}' if u.wallet else '0.00'
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=usuarios_analytics.csv"
        output.headers["Content-type"] = "text/csv"

        return output

    except Exception as e:
        flash(f'Error al exportar CSV: {str(e)}', 'danger')
        app.logger.error(f'Error en exportar CSV: {str(e)}')
        return redirect(url_for('admin_analytics'))


@app.route('/admin/exportar/productos_csv')
@admin_required
def exportar_productos_csv():
    try:
        si = StringIO()
        writer = csv.writer(si)

        writer.writerow([
            'ID_Producto', 'Nombre', 'Precio', 'Stock', 'Disponible',
            'Total_Vendido', 'Ingresos_Totales',
            'Veces_Agregado_Carrito', 'Veces_Abandonado',
            'Tasa_Conversion_Producto'
        ])

        productos = Producto.query.all()
        for p in productos:
            total_vendido = db.session.query(
                db.func.sum(DetallePedido.cantidad)
            ).filter(DetallePedido.ID_Producto == p.ID_Producto).scalar() or 0

            ingresos = db.session.query(
                db.func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario)
            ).filter(DetallePedido.ID_Producto == p.ID_Producto).scalar() or 0

            veces_agregado = db.session.query(
                db.func.sum(HistorialCarrito.cantidad)
            ).filter(
                HistorialCarrito.ID_Producto == p.ID_Producto,
                HistorialCarrito.accion == 'agregar'
            ).scalar() or 0

            veces_abandonado = db.session.query(
                db.func.sum(HistorialCarrito.cantidad)
            ).filter(
                HistorialCarrito.ID_Producto == p.ID_Producto,
                HistorialCarrito.accion == 'abandonar'
            ).scalar() or 0

            tasa_conv = (total_vendido / veces_agregado * 100) if veces_agregado > 0 else 0

            writer.writerow([
                p.ID_Producto,
                p.nombre,
                f'{p.precio:.2f}',
                p.stock,
                'Sí' if p.disponible else 'No',
                total_vendido,
                f'{ingresos:.2f}',
                veces_agregado,
                veces_abandonado,
                f'{tasa_conv:.2f}%'
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=productos_analytics.csv"
        output.headers["Content-type"] = "text/csv"

        return output

    except Exception as e:
        flash(f'Error al exportar CSV: {str(e)}', 'danger')
        app.logger.error(f'Error en exportar CSV: {str(e)}')
        return redirect(url_for('admin_analytics'))


@app.route('/admin/exportar/ventas_csv')
@admin_required
def exportar_ventas_csv():
    """Exporta ventas (detalles de pedidos) en formato CSV. Parámetros GET opcionales: desde=YYYY-MM-DD, hasta=YYYY-MM-DD"""
    try:
        # If the unified form requested a simple export, redirect to the simple exporter
        formato_req = request.args.get('formato') or request.args.get('format')
        if formato_req and formato_req.lower() == 'simple':
            return redirect(url_for('exportar_ventas_simple_csv', desde=request.args.get('desde'), hasta=request.args.get('hasta')))

        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        fmt = '%Y-%m-%d'

        q = Pedido.query
        if desde:
            try:
                d_from = datetime.strptime(desde, fmt)
                q = q.filter(Pedido.fecha >= d_from)
            except Exception:
                pass
        if hasta:
            try:
                d_to = datetime.strptime(hasta, fmt)
                # incluir todo el día
                d_to_end = d_to.replace(hour=23, minute=59, second=59)
                q = q.filter(Pedido.fecha <= d_to_end)
            except Exception:
                pass

        pedidos = q.order_by(Pedido.fecha.desc()).all()

        si = StringIO()
        writer = csv.writer(si)

        writer.writerow([
            'ID_Pedido', 'Fecha', 'ID_Usuario', 'Email_Usuario', 'ID_Producto', 'Nombre_Producto',
            'Cantidad', 'Precio_Unitario', 'Subtotal_Item', 'Total_Pedido', 'Categoria', 'Subcategoria'
        ])

        for pedido in pedidos:
            usuario = Usuario.query.get(pedido.ID_Users) if pedido.ID_Users else None
            detalles = DetallePedido.query.filter_by(ID_Pedido=pedido.ID_Pedido).all()
            total_pedido = pedido.total
            if not detalles:
                # registrar fila del pedido sin items
                writer.writerow([
                    pedido.ID_Pedido,
                    pedido.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    usuario.ID_Users if usuario else '',
                    usuario.email if usuario else '',
                    '', '', '', '', '',
                    f'{total_pedido:.2f}', '', ''
                ])
            else:
                for d in detalles:
                    producto = Producto.query.get(d.ID_Producto)
                    categoria = None
                    subcat = None
                    if producto:
                        categoria = Categoria.query.get(producto.ID_Categoria) if producto.ID_Categoria else None
                        subcat = Subcategoria.query.get(producto.ID_Subcategoria) if producto.ID_Subcategoria else None
                    subtotal = (d.cantidad or 0) * (d.precio_unitario or 0)
                    writer.writerow([
                        pedido.ID_Pedido,
                        pedido.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                        usuario.ID_Users if usuario else '',
                        usuario.email if usuario else '',
                        producto.ID_Producto if producto else d.ID_Producto,
                        producto.nombre if producto else '',
                        d.cantidad,
                        f'{d.precio_unitario:.2f}',
                        f'{subtotal:.2f}',
                        f'{total_pedido:.2f}',
                        categoria.nombre if categoria else '',
                        subcat.nombre if subcat else ''
                    ])

        filename = 'ventas'
        if desde: filename += f'_{desde}'
        if hasta: filename += f'_{hasta}'
        filename += '.csv'

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename={filename}"
        output.headers["Content-type"] = "text/csv"
        return output

    except Exception as e:
        flash(f'Error al exportar ventas CSV: {str(e)}', 'danger')
        app.logger.error(f'Error en exportar ventas CSV: {str(e)}')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/exportar/ventas_simple_csv')
@admin_required
def exportar_ventas_simple_csv():
    """Exporta resumen de ventas (one-row-per-pedido) en CSV. Parámetros GET opcionales: desde=YYYY-MM-DD, hasta=YYYY-MM-DD.
    Limita el rango a 90 días para evitar exportaciones demasiado grandes.
    """
    try:
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        fmt = '%Y-%m-%d'
        now = datetime.utcnow()

        # Determinar rango por defecto (últimos 30 días)
        if desde:
            try:
                d_from = datetime.strptime(desde, fmt)
            except Exception:
                d_from = now - timedelta(days=30)
        else:
            d_from = now - timedelta(days=30)

        if hasta:
            try:
                d_to = datetime.strptime(hasta, fmt)
            except Exception:
                d_to = now
        else:
            d_to = now

        # incluir todo el día final
        d_to_end = d_to.replace(hour=23, minute=59, second=59)

        # Validar rango máximo
        max_days = 90
        if (d_to_end - d_from).days > max_days:
            flash(f'El rango máximo permitido para exportar es de {max_days} días. Por favor selecciona un rango menor.', 'warning')
            return redirect(url_for('admin_dashboard'))

        pedidos = Pedido.query.filter(Pedido.fecha >= d_from, Pedido.fecha <= d_to_end).order_by(Pedido.fecha.desc()).all()

        si = StringIO()
        writer = csv.writer(si)

        writer.writerow([
            'ID_Pedido', 'Fecha', 'ID_Usuario', 'Email_Usuario', 'Cantidad_Items', 'Productos_Resumen', 'Total_Pedido', 'Estado'
        ])

        for pedido in pedidos:
            usuario = Usuario.query.get(pedido.ID_Users) if pedido.ID_Users else None
            detalles = DetallePedido.query.filter_by(ID_Pedido=pedido.ID_Pedido).all()
            cantidad_items = sum([d.cantidad or 0 for d in detalles]) if detalles else 0
            productos_resumen = ''
            if detalles:
                partes = []
                for d in detalles:
                    prod = Producto.query.get(d.ID_Producto)
                    nombre = prod.nombre if prod else f'ID_{d.ID_Producto}'
                    partes.append(f"{nombre} x{d.cantidad}")
                productos_resumen = '; '.join(partes)

            writer.writerow([
                pedido.ID_Pedido,
                pedido.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                usuario.ID_Users if usuario else '',
                usuario.email if usuario else '',
                cantidad_items,
                productos_resumen,
                f'{pedido.total:.2f}',
                pedido.estado
            ])

        filename = f"ventas_simple_{d_from.strftime('%Y%m%d')}_{d_to.strftime('%Y%m%d')}.csv"
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename={filename}"
        output.headers["Content-type"] = "text/csv"
        return output

    except Exception as e:
        flash(f'Error al exportar ventas (simple) CSV: {str(e)}', 'danger')
        app.logger.error(f'Error en exportar ventas simple CSV: {str(e)}')
        return redirect(url_for('admin_dashboard'))


# ==================== MANEJADORES DE ERRORES ====================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(400)
def bad_request(e):
    return render_template('errors/400.html'), 400


# ==================== INICIALIZACIÓN ====================

def insertar_productos_ejemplo():
    """Inserta datos de ejemplo si la base de datos está vacía"""
    with app.app_context():
        try:
            if Producto.query.count() == 0:
                productos_ejemplo = [
                    Producto(nombre='Tarjeta Gráfica GTX 1650', precio=230,
                            imagen='img/Gtx.png', disponible=True, stock=15),
                    Producto(nombre='Tarjeta gráfica RTX 4090', precio=1800,
                            imagen='img/RTX4090.png', disponible=False, stock=0),
                    Producto(nombre='Monitor Xiaomi G34', precio=500,
                            imagen='img/MonitorXiaomiG34.png', disponible=True, stock=8),
                ]

                for producto in productos_ejemplo:
                    db.session.add(producto)

                db.session.commit()
                print("✓ Productos de ejemplo insertados correctamente")
            else:
                print("✓ Ya existen productos en la base de datos")

            admin = Usuario.query.filter_by(email='admin@axionstore.com').first()
            if not admin:
                hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
                admin = Usuario(
                    nombre='Administrador',
                    email='admin@axionstore.com',
                    password=hashed_password,
                    es_admin=True
                )
                db.session.add(admin)
                db.session.commit()

                wallet = Wallet(ID_Users=admin.ID_Users, saldo=10000.0)
                db.session.add(wallet)
                db.session.commit()
                print("✓ Usuario administrador creado: admin@axionstore.com / admin123")

        except Exception as e:
            db.session.rollback()
            print(f"Error al insertar datos: {str(e)}")


def inicializar_aplicacion():
    """
    Función principal de inicialización que:
    1. Verifica la conexión a la base de datos
    2. Crea las tablas si no existen
    3. Inserta datos de ejemplo
    """
    print("=" * 50)
    print("INICIALIZANDO AXION STORE")
    print("=" * 50)

    with app.app_context():
        # Paso 1: Crear tablas
        print("\n[1/3] Creando/verificando tablas en la base de datos...")
        try:
            db.create_all()
            print("✓ Tablas creadas/verificadas exitosamente")
        except Exception as e:
            print(f"✗ Error al crear tablas: {str(e)}")
            return False

        # Paso 2: Verificar conexión
        print("\n[2/3] Verificando conexión a la base de datos...")
        try:
            db.session.execute(db.text('SELECT 1'))
            print("✓ Conexión establecida correctamente")
        except Exception as e:
            print(f"✗ Error de conexión: {str(e)}")
            return False

        # Paso 3: Insertar datos de ejemplo
        print("\n[3/3] Verificando datos iniciales...")
        insertar_productos_ejemplo()

    print("\n" + "=" * 50)
    print("✓ INICIALIZACIÓN COMPLETADA")
    print("=" * 50)
    return True


# Asegurar esquema antes de la primera petición para evitar errores por columnas faltantes
# Preferimos ejecutar la comprobación antes de la primera petición. Si la versión
# de Flask cargada no soporta `before_first_request` por alguna razón, se ejecuta
# inmediatamente como fallback.
if hasattr(app, 'before_first_request'):
    @app.before_first_request
    def ensure_db_schema():
        try:
            app.logger.info('Running DB schema checks (before first request)')
            crear_tablas_db()
        except Exception as e:
            app.logger.error(f'Error ensuring DB schema before first request: {e}')
else:
    try:
        app.logger.info('Running DB schema checks (immediate fallback)')
        crear_tablas_db()
    except Exception as e:
        try:
            app.logger.error(f'Error ensuring DB schema on import fallback: {e}')
        except Exception:
            pass


@app.context_processor
def inject_user_wishlist():
    """Provide `user_wishlist_ids` set and `wishlist_count` to all templates.
    This lets templates render heart state without extra DB calls in Jinja.
    """
    user_id = session.get('user_id')
    ids = set()
    count = 0
    if user_id:
        try:
            rows = Wishlist.query.with_entities(Wishlist.ID_Producto).filter_by(ID_Users=user_id).all()
            ids = set(r[0] for r in rows)
            count = Wishlist.query.filter_by(ID_Users=user_id).count()
        except Exception:
            ids = set()
            count = 0
    return dict(user_wishlist_ids=ids, wishlist_count=count)


# ==================== PUNTO DE ENTRADA ====================

if __name__ == '__main__':
    # Inicializar la aplicación (crear tablas, datos de ejemplo, etc.)
    if inicializar_aplicacion():
        # Ejecutar el servidor
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Error: No se pudo inicializar la aplicación")

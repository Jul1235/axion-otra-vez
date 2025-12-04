/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.3-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: axion_store
-- ------------------------------------------------------
-- Server version	11.8.3-MariaDB-0+deb13u1 from Debian

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `carrito`
--

DROP TABLE IF EXISTS `carrito`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `carrito` (
  `ID_Carrito` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Users` int(11) NOT NULL,
  `ID_Producto` int(11) NOT NULL,
  `cantidad` int(11) DEFAULT 1,
  PRIMARY KEY (`ID_Carrito`),
  KEY `idx_users` (`ID_Users`),
  KEY `idx_producto` (`ID_Producto`),
  CONSTRAINT `carrito_ibfk_1` FOREIGN KEY (`ID_Users`) REFERENCES `users` (`ID_Users`) ON DELETE CASCADE,
  CONSTRAINT `carrito_ibfk_2` FOREIGN KEY (`ID_Producto`) REFERENCES `producto` (`ID_Producto`) ON DELETE CASCADE,
  CONSTRAINT `CONSTRAINT_1` CHECK (`cantidad` > 0)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `carrito`
--

LOCK TABLES `carrito` WRITE;
/*!40000 ALTER TABLE `carrito` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `carrito` VALUES
(3,2,31,2),
(6,19,9,2);
/*!40000 ALTER TABLE `carrito` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `categoria`
--

DROP TABLE IF EXISTS `categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria` (
  `ID_Categoria` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `icono` varchar(50) DEFAULT NULL COMMENT 'Clase de icono (ej: fa-desktop, fa-headphones)',
  `activa` tinyint(1) DEFAULT 1,
  `orden` int(11) DEFAULT 0 COMMENT 'Para ordenar visualmente',
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`ID_Categoria`),
  UNIQUE KEY `nombre` (`nombre`),
  KEY `idx_nombre` (`nombre`),
  KEY `idx_activa` (`activa`),
  KEY `idx_orden` (`orden`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categoria`
--

LOCK TABLES `categoria` WRITE;
/*!40000 ALTER TABLE `categoria` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `categoria` VALUES
(1,'Componentes PC','Tarjetas gráficas, procesadores, placas base, RAM','fa-microchip',1,1,'2025-11-25 01:00:10'),
(2,'Periféricos','Ratones, teclados, auriculares, webcams','fa-keyboard',1,2,'2025-11-25 01:00:10'),
(3,'Monitores','Pantallas gaming, profesionales, ultrawide','fa-desktop',1,3,'2025-11-25 01:00:10'),
(4,'Almacenamiento','SSD, HDD, NVMe, externos','fa-hdd',1,4,'2025-11-25 01:00:10'),
(5,'Audio','Auriculares, micrófonos, altavoces','fa-headphones',1,5,'2025-11-25 01:00:10'),
(6,'Refrigeración','Ventiladores, AIO, disipadores','fa-fan',1,6,'2025-11-25 01:00:10');
/*!40000 ALTER TABLE `categoria` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `detalle_pedido`
--

DROP TABLE IF EXISTS `detalle_pedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_pedido` (
  `ID_Detalle_Pedido` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Pedido` int(11) NOT NULL,
  `ID_Producto` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio_unitario` float NOT NULL,
  PRIMARY KEY (`ID_Detalle_Pedido`),
  KEY `idx_pedido` (`ID_Pedido`),
  KEY `idx_producto` (`ID_Producto`),
  CONSTRAINT `detalle_pedido_ibfk_1` FOREIGN KEY (`ID_Pedido`) REFERENCES `pedido` (`ID_Pedido`) ON DELETE CASCADE,
  CONSTRAINT `detalle_pedido_ibfk_2` FOREIGN KEY (`ID_Producto`) REFERENCES `producto` (`ID_Producto`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_pedido`
--

LOCK TABLES `detalle_pedido` WRITE;
/*!40000 ALTER TABLE `detalle_pedido` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `detalle_pedido` VALUES
(1,1,7,3,230),
(2,2,70,1,189.99),
(3,2,17,1,380);
/*!40000 ALTER TABLE `detalle_pedido` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `historial_carrito`
--

DROP TABLE IF EXISTS `historial_carrito`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historial_carrito` (
  `ID_Historial` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Users` int(11) NOT NULL,
  `ID_Producto` int(11) NOT NULL,
  `accion` varchar(20) NOT NULL COMMENT 'agregar, quitar, comprar, abandonar',
  `cantidad` int(11) NOT NULL,
  `precio_momento` float NOT NULL,
  `valor_total` float NOT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `ID_Pedido` int(11) DEFAULT NULL,
  PRIMARY KEY (`ID_Historial`),
  KEY `ID_Pedido` (`ID_Pedido`),
  KEY `idx_usuario_fecha` (`ID_Users`,`fecha`),
  KEY `idx_accion` (`accion`),
  KEY `idx_producto` (`ID_Producto`),
  KEY `idx_fecha` (`fecha`),
  CONSTRAINT `historial_carrito_ibfk_1` FOREIGN KEY (`ID_Users`) REFERENCES `users` (`ID_Users`) ON DELETE CASCADE,
  CONSTRAINT `historial_carrito_ibfk_2` FOREIGN KEY (`ID_Producto`) REFERENCES `producto` (`ID_Producto`) ON DELETE CASCADE,
  CONSTRAINT `historial_carrito_ibfk_3` FOREIGN KEY (`ID_Pedido`) REFERENCES `pedido` (`ID_Pedido`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=86 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historial_carrito`
--

LOCK TABLES `historial_carrito` WRITE;
/*!40000 ALTER TABLE `historial_carrito` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `historial_carrito` VALUES
(75,2,31,'agregar',1,549.99,549.99,'2025-11-29 19:09:26',NULL),
(76,2,31,'agregar',1,549.99,549.99,'2025-11-29 19:45:28',NULL),
(77,2,31,'quitar',2,549.99,1099.98,'2025-11-29 19:45:36',NULL),
(78,2,31,'agregar',1,549.99,549.99,'2025-11-29 20:57:25',NULL),
(79,2,31,'agregar',1,549.99,549.99,'2025-11-29 20:57:32',NULL),
(80,1,70,'agregar',1,189.99,189.99,'2025-11-29 21:41:20',NULL),
(81,1,17,'agregar',1,380,380,'2025-11-29 23:58:52',NULL),
(82,1,70,'comprar',1,189.99,189.99,'2025-11-29 23:59:43',2),
(83,1,17,'comprar',1,380,380,'2025-11-29 23:59:43',2),
(84,19,9,'agregar',1,299,299,'2025-11-30 00:14:38',NULL),
(85,19,9,'agregar',1,299,299,'2025-11-30 00:14:44',NULL);
/*!40000 ALTER TABLE `historial_carrito` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `metricas_categoria`
--

DROP TABLE IF EXISTS `metricas_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `metricas_categoria` (
  `ID_Metrica` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Categoria` int(11) NOT NULL,
  `total_productos_vendidos` int(11) DEFAULT 0,
  `total_pedidos` int(11) DEFAULT 0,
  `ingresos_totales` float DEFAULT 0,
  `ticket_promedio` float DEFAULT 0,
  `total_agregados_carrito` int(11) DEFAULT 0,
  `total_abandonos` int(11) DEFAULT 0,
  `valor_abandonos` float DEFAULT 0,
  `tasa_conversion` float DEFAULT 0,
  `productos_activos` int(11) DEFAULT 0,
  `productos_sin_stock` int(11) DEFAULT 0,
  `ultima_actualizacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`ID_Metrica`),
  UNIQUE KEY `unique_metrica_categoria` (`ID_Categoria`),
  KEY `idx_categoria` (`ID_Categoria`),
  KEY `idx_ingresos` (`ingresos_totales`),
  KEY `idx_conversion` (`tasa_conversion`),
  CONSTRAINT `metricas_categoria_ibfk_1` FOREIGN KEY (`ID_Categoria`) REFERENCES `categoria` (`ID_Categoria`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `metricas_categoria`
--

LOCK TABLES `metricas_categoria` WRITE;
/*!40000 ALTER TABLE `metricas_categoria` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `metricas_categoria` VALUES
(1,1,2,1,569.99,569.99,4,0,0,50,47,8,'2025-11-30 02:17:17'),
(2,2,0,0,0,0,0,0,0,0,17,3,'2025-11-30 02:17:17'),
(3,3,0,0,0,0,0,0,0,0,8,0,'2025-11-30 02:17:17'),
(4,4,3,1,690,690,0,0,0,0,15,1,'2025-11-30 02:17:17'),
(5,5,0,0,0,0,0,0,0,0,0,0,'2025-11-30 02:17:17'),
(6,6,0,0,0,0,0,0,0,0,0,0,'2025-11-30 02:17:17');
/*!40000 ALTER TABLE `metricas_categoria` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `metricas_subcategoria`
--

DROP TABLE IF EXISTS `metricas_subcategoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `metricas_subcategoria` (
  `ID_Metrica` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Subcategoria` int(11) NOT NULL,
  `ID_Categoria` int(11) NOT NULL,
  `total_productos_vendidos` int(11) DEFAULT 0,
  `total_pedidos` int(11) DEFAULT 0,
  `ingresos_totales` float DEFAULT 0,
  `ticket_promedio` float DEFAULT 0,
  `total_agregados_carrito` int(11) DEFAULT 0,
  `total_abandonos` int(11) DEFAULT 0,
  `valor_abandonos` float DEFAULT 0,
  `tasa_conversion` float DEFAULT 0,
  `productos_activos` int(11) DEFAULT 0,
  `productos_sin_stock` int(11) DEFAULT 0,
  `ultima_actualizacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`ID_Metrica`),
  UNIQUE KEY `unique_metrica_subcategoria` (`ID_Subcategoria`),
  KEY `idx_subcategoria` (`ID_Subcategoria`),
  KEY `idx_categoria` (`ID_Categoria`),
  KEY `idx_ingresos` (`ingresos_totales`),
  KEY `idx_conversion` (`tasa_conversion`),
  CONSTRAINT `metricas_subcategoria_ibfk_1` FOREIGN KEY (`ID_Subcategoria`) REFERENCES `subcategoria` (`ID_Subcategoria`) ON DELETE CASCADE,
  CONSTRAINT `metricas_subcategoria_ibfk_2` FOREIGN KEY (`ID_Categoria`) REFERENCES `categoria` (`ID_Categoria`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `metricas_subcategoria`
--

LOCK TABLES `metricas_subcategoria` WRITE;
/*!40000 ALTER TABLE `metricas_subcategoria` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `metricas_subcategoria` VALUES
(1,1,1,0,0,0,0,2,0,0,0,9,1,'2025-11-30 02:17:17'),
(2,2,1,0,0,0,0,0,0,0,0,12,2,'2025-11-30 02:17:17'),
(3,3,1,1,1,189.99,189.99,1,0,0,100,8,0,'2025-11-30 02:17:17'),
(4,4,1,1,1,380,380,1,0,0,100,7,1,'2025-11-30 02:17:17'),
(5,5,1,0,0,0,0,0,0,0,0,5,3,'2025-11-30 02:17:17'),
(6,6,1,0,0,0,0,0,0,0,0,6,1,'2025-11-30 02:17:17'),
(7,7,2,0,0,0,0,0,0,0,0,8,1,'2025-11-30 02:17:17'),
(8,8,2,0,0,0,0,0,0,0,0,8,2,'2025-11-30 02:17:17'),
(9,9,2,0,0,0,0,0,0,0,0,1,0,'2025-11-30 02:17:17'),
(10,10,3,0,0,0,0,0,0,0,0,8,0,'2025-11-30 02:17:17'),
(11,11,3,0,0,0,0,0,0,0,0,0,0,'2025-11-30 02:17:17'),
(12,12,3,0,0,0,0,0,0,0,0,0,0,'2025-11-30 02:17:17'),
(13,13,4,3,1,690,690,0,0,0,0,8,0,'2025-11-30 02:17:17'),
(14,14,4,0,0,0,0,0,0,0,0,7,1,'2025-11-30 02:17:17'),
(15,15,5,0,0,0,0,0,0,0,0,0,0,'2025-11-30 02:17:17'),
(16,16,5,0,0,0,0,0,0,0,0,0,0,'2025-11-30 02:17:17');
/*!40000 ALTER TABLE `metricas_subcategoria` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `pedido`
--

DROP TABLE IF EXISTS `pedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pedido` (
  `ID_Pedido` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Users` int(11) NOT NULL,
  `total` float NOT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `estado` varchar(20) DEFAULT 'pagado',
  PRIMARY KEY (`ID_Pedido`),
  KEY `idx_users` (`ID_Users`),
  KEY `idx_fecha` (`fecha`),
  CONSTRAINT `pedido_ibfk_1` FOREIGN KEY (`ID_Users`) REFERENCES `users` (`ID_Users`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pedido`
--

LOCK TABLES `pedido` WRITE;
/*!40000 ALTER TABLE `pedido` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `pedido` VALUES
(1,1,690,'2025-11-25 15:33:29','pagado'),
(2,1,569.99,'2025-11-29 23:59:43','pagado');
/*!40000 ALTER TABLE `pedido` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `producto`
--

DROP TABLE IF EXISTS `producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto` (
  `ID_Producto` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) NOT NULL,
  `precio` float NOT NULL,
  `imagen` varchar(300) DEFAULT NULL,
  `disponible` tinyint(1) DEFAULT 1,
  `stock` int(11) DEFAULT 0,
  `ID_Subcategoria` int(11) DEFAULT NULL,
  `ID_Categoria` int(11) DEFAULT NULL,
  PRIMARY KEY (`ID_Producto`),
  KEY `idx_nombre` (`nombre`),
  KEY `idx_subcategoria` (`ID_Subcategoria`),
  KEY `idx_categoria` (`ID_Categoria`),
  CONSTRAINT `producto_ibfk_1` FOREIGN KEY (`ID_Subcategoria`) REFERENCES `subcategoria` (`ID_Subcategoria`) ON DELETE SET NULL,
  CONSTRAINT `producto_ibfk_2` FOREIGN KEY (`ID_Categoria`) REFERENCES `categoria` (`ID_Categoria`) ON DELETE SET NULL,
  CONSTRAINT `CONSTRAINT_1` CHECK (`stock` >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto`
--

LOCK TABLES `producto` WRITE;
/*!40000 ALTER TABLE `producto` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `producto` VALUES
(1,'Tarjeta Gráfica GTX 1650',230,'img/Gtx.png',1,15,1,1),
(2,'TECLADO LOGITECH K120 CON CABLE USB NEGRO',25,NULL,1,58,8,2),
(3,'Mouse con cable HP 100',45.2,NULL,1,77,7,2),
(4,'PRIME B460M-A R2.0/ tarjeta madre ASUS',120,NULL,1,13,3,1),
(5,'Procesador Intel i9-14900K',887,NULL,1,12,2,1),
(6,'RAM CORSAIR VENGEANCE 16gb ddr5 3200mhz',79.99,NULL,1,65,4,1),
(7,'SAMSUNG SSD 990 pro 2tb',230,NULL,1,35,13,4),
(8,'HDD Seagate BARRACUDA 1TB',55,NULL,0,0,14,4),
(9,'ASUS Tarjetas gráficas AMD Radeon RX 6500 XT',299,NULL,1,12,1,1),
(10,'Fuente De Poder EVGA 600w',65,NULL,1,30,5,1),
(11,'MAG FORGE M100A',179,NULL,1,25,6,1),
(12,'Monitor Samsung 24 PLG Curvo C24F390FHN',199.99,NULL,1,188,10,3),
(13,'Teclado Gamer Mecanico Hp GK100 Rgb',32.99,NULL,1,56,8,2),
(14,'Mouse Logitech G502 X gaming',91,NULL,0,0,7,2),
(15,'Placa Madre Gigabyte H510m H intel Lga 1200',84.99,NULL,1,33,3,1),
(16,'Procesador AMD Ryzen 9 9950X 16 Núcleos 4,30GHz',1341,NULL,1,28,2,1),
(17,'MEMORIA RAM KINGSTON 32GB/ DDR5/ 5200MHz KF556C40BB-32',380,NULL,1,59,4,1),
(18,'SSD M.2 NVMe MP600 PRO NH 1TB PCIe 4.0 (Gen 4) x4',165,NULL,1,35,13,4),
(19,'HDD 1TB 2.5\" SEAGATE SATA3 5400rpm - Model ST1000LM024',187.99,NULL,1,45,14,4),
(20,'Tarjeta gráfica GEFORCE GTX 1660',650,NULL,1,10,1,1),
(21,'Fuente de Poder ASUS TUF Gaming -1200W 80 PLUS Gold - Modular ATX',300,NULL,1,31,5,1),
(22,'Gabinete Gamer Media Torre Tank Master 9600 TB MAX MB ATX Ultra Wide',1850,NULL,0,0,6,1),
(23,'Procesador Intel Core i5-13400F',258,NULL,1,36,2,1),
(24,'Teclado mecánico para juegos K95 RGB PLATINUM XT — CHERRY MX SPEED',199,NULL,1,40,8,2),
(25,'Procesador Intel Core i3-12100F',130,NULL,1,78,2,1),
(26,'Placa madre msi a520m-a pro',199.99,NULL,1,29,3,1),
(27,'PROCESADOR INTEL CORE I5-10400 6 NUCLEOS 4.3 GHZ',250,NULL,0,0,2,1),
(28,'Procesador Intel Core i7-13700K',409,NULL,1,55,2,1),
(29,'Procesador AMD Ryzen 7 7800X3D',410,NULL,1,30,2,1),
(30,'Procesador AMD Ryzen 9 7950X',515,NULL,1,20,2,1),
(31,'ASUS ROG Strix Z790-E Gaming WiFi',549.99,NULL,1,2,NULL,NULL),
(32,'Asus tuf gaming b760-plus wifi',220,NULL,1,27,NULL,NULL),
(33,'Gigabyte Z690 AORUS Elite AX',265,NULL,1,26,NULL,NULL),
(34,'Teclado Mecánico Logitech G915 TKL',299.99,NULL,0,0,8,2),
(35,'Teclado Mecánico Razer BlackWidow V4 Pro',337,NULL,1,62,8,2),
(36,'Mouse Razer DeathAdder V3 Pro Wireless',138,NULL,1,74,7,2),
(37,'Mouse Logitech G502 HERO High Performance',119.99,NULL,1,31,7,2),
(38,'Procesador AMD Modelo 38',279.99,NULL,1,24,2,1),
(39,'RAM Corsair Modelo 39',99.99,NULL,1,58,4,1),
(40,'SSD Kingston Modelo 40',149.99,NULL,1,33,13,4),
(41,'HDD Samsung Modelo 41',59.99,NULL,1,46,14,4),
(42,'Tarjeta Gráfica Nvidia Modelo 42',629.99,NULL,1,12,1,1),
(43,'Fuente Dell Modelo 43',89.99,NULL,1,29,5,1),
(44,'Gabinete MSI Modelo 44',119.99,NULL,1,22,6,1),
(45,'Monitor Samsung Modelo 45',239.99,NULL,1,35,10,3),
(46,'Teclado HP Modelo 46',69.99,NULL,0,0,8,2),
(47,'Mouse Logitech Modelo 47',42.99,NULL,1,79,7,2),
(48,'Placa Madre Gigabyte Modelo 48',169.99,NULL,1,34,3,1),
(49,'Procesador Intel Modelo 49',329.99,NULL,1,20,2,1),
(50,'RAM Kingston Modelo 50',84.99,NULL,1,57,4,1),
(51,'SSD Corsair Modelo 51',129.99,NULL,1,31,13,4),
(52,'HDD Seagate Modelo 52',69.99,NULL,1,44,14,4),
(53,'Tarjeta Gráfica AMD Modelo 53',519.99,NULL,1,13,1,1),
(54,'Fuente Asus Modelo 54',99.99,NULL,0,0,5,1),
(55,'Gabinete LG Modelo 55',95.99,NULL,1,28,6,1),
(56,'Monitor Dell Modelo 56',229.99,NULL,1,38,10,3),
(57,'Teclado Corsair Modelo 57',109.99,NULL,1,42,8,2),
(58,'Mouse HP Modelo 58',37.99,NULL,1,76,7,2),
(59,'Placa Madre MSI Modelo 59',199.99,NULL,1,30,3,1),
(60,'Procesador AMD Modelo 60',289.99,NULL,1,19,2,1),
(61,'RAM Kingston Modelo 61',79.99,NULL,1,59,4,1),
(62,'SSD Samsung Modelo 62',139.99,NULL,1,32,13,4),
(63,'HDD Seagate Modelo 63',49.99,NULL,1,47,14,4),
(64,'Tarjeta Gráfica Nvidia Modelo 64',599.99,NULL,1,11,1,1),
(65,'Fuente Dell Modelo 65',89.99,NULL,0,0,5,1),
(66,'Gabinete MSI Modelo 66',119.99,NULL,1,23,6,1),
(67,'Monitor LG Modelo 67',219.99,NULL,1,36,10,3),
(68,'Teclado Logitech Modelo 68',84.99,NULL,1,63,8,2),
(69,'Mouse HP Modelo 69',44.99,NULL,1,75,7,2),
(70,'Placa Madre Asus Modelo 70',189.99,NULL,1,28,3,1),
(71,'Procesador Intel Modelo 71',349.99,NULL,0,0,2,1),
(72,'RAM Corsair Modelo 72',94.99,NULL,1,56,4,1),
(73,'SSD Kingston Modelo 73',149.99,NULL,1,34,13,4),
(74,'HDD Samsung Modelo 74',59.99,NULL,1,45,14,4),
(75,'Tarjeta Gráfica AMD Modelo 75',529.99,NULL,1,14,1,1),
(76,'Fuente Asus Modelo 76',99.99,NULL,1,25,5,1),
(77,'Gabinete LG Modelo 77',95.99,NULL,1,27,6,1),
(78,'Monitor Dell Modelo 78',239.99,NULL,1,37,10,3),
(79,'Teclado Corsair Modelo 79',109.99,NULL,1,41,8,2),
(80,'Mouse HP Modelo 80',39.99,NULL,1,77,7,2),
(81,'Placa Madre MSI Modelo 81',199.99,NULL,1,31,3,1),
(82,'Procesador AMD Modelo 82',279.99,NULL,1,23,2,1),
(83,'RAM Kingston Modelo 83',89.99,NULL,0,0,4,1),
(84,'SSD Corsair Modelo 84',129.99,NULL,1,33,13,4),
(85,'HDD Seagate Modelo 85',69.99,NULL,1,46,14,4),
(86,'Tarjeta Gráfica Nvidia Modelo 86',619.99,NULL,1,12,1,1),
(87,'Fuente Dell Modelo 87',89.99,NULL,1,27,5,1),
(88,'Gabinete MSI Modelo 88',119.99,NULL,1,24,6,1),
(89,'Monitor LG Modelo 89',219.99,NULL,1,39,10,3),
(90,'Teclado Logitech Modelo 90',84.99,NULL,1,61,8,2),
(91,'Mouse HP Modelo 91',42.99,NULL,1,74,7,2),
(92,'Placa Madre Asus Modelo 92',189.99,NULL,1,32,3,1),
(93,'Procesador Intel Modelo 93',329.99,NULL,1,22,2,1),
(94,'RAM Corsair Modelo 94',94.99,NULL,1,55,4,1),
(95,'SSD Kingston Modelo 95',149.99,NULL,1,35,13,4),
(96,'HDD Samsung Modelo 96',59.99,NULL,1,44,14,4),
(97,'Tarjeta Gráfica AMD Modelo 97',539.99,NULL,1,13,1,1),
(98,'Fuente Asus Modelo 98',99.99,NULL,0,0,5,1),
(99,'Audífonos HyperX Cloud II Wireless',192.32,NULL,1,28,9,2),
(100,'Monitor Dell 19 Lcd Refurbish Clase A Vga',120,NULL,1,36,10,3),
(101,'Tarjeta gráfica RTX 4090',1800,'img/RTX4090.png',0,0,1,1),
(102,'Monitor Xiaomi G34',500,'img/MonitorXiaomiG34.png',1,8,10,3);
/*!40000 ALTER TABLE `producto` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `subcategoria`
--

DROP TABLE IF EXISTS `subcategoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `subcategoria` (
  `ID_Subcategoria` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Categoria` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `activa` tinyint(1) DEFAULT 1,
  `orden` int(11) DEFAULT 0,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`ID_Subcategoria`),
  UNIQUE KEY `unique_subcategoria` (`ID_Categoria`,`nombre`),
  KEY `idx_categoria` (`ID_Categoria`),
  KEY `idx_nombre` (`nombre`),
  KEY `idx_activa` (`activa`),
  CONSTRAINT `subcategoria_ibfk_1` FOREIGN KEY (`ID_Categoria`) REFERENCES `categoria` (`ID_Categoria`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subcategoria`
--

LOCK TABLES `subcategoria` WRITE;
/*!40000 ALTER TABLE `subcategoria` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `subcategoria` VALUES
(1,1,'Tarjetas Gráficas','GPUs NVIDIA y AMD',1,1,'2025-11-25 01:00:10'),
(2,1,'Procesadores','CPUs Intel y AMD',1,2,'2025-11-25 01:00:10'),
(3,1,'Placas Base','Motherboards ATX, mATX, Mini-ITX',1,3,'2025-11-25 01:00:10'),
(4,1,'Memoria RAM','DDR4, DDR5',1,4,'2025-11-25 01:00:10'),
(5,1,'Fuentes de Poder','PSU certificadas 80+ Bronze, Gold, Platinum',1,5,'2025-11-25 01:00:10'),
(6,1,'Gabinetes','Cases gaming y profesionales',1,6,'2025-11-25 01:00:10'),
(7,2,'Ratones','Ratones ópticos y wireless',1,1,'2025-11-25 01:00:10'),
(8,2,'Teclados','Mecánicos, de membrana, wireless',1,2,'2025-11-25 01:00:10'),
(9,2,'Auriculares','Gaming y profesionales',1,3,'2025-11-25 01:00:10'),
(10,3,'Gaming','Alta frecuencia 144Hz+',1,1,'2025-11-25 01:00:10'),
(11,3,'Profesionales','Color accuracy, 4K',1,2,'2025-11-25 01:00:10'),
(12,3,'Ultrawide','Pantallas 21:9 y 32:9',1,3,'2025-11-25 01:00:10'),
(13,4,'SSD','Discos sólidos SATA y NVMe',1,1,'2025-11-25 01:00:10'),
(14,4,'HDD','Discos mecánicos',1,2,'2025-11-25 01:00:10'),
(15,5,'Auriculares Gaming','Con micrófono integrado',1,1,'2025-11-25 01:00:10'),
(16,5,'Auriculares Profesionales','Para producción musical',1,2,'2025-11-25 01:00:10');
/*!40000 ALTER TABLE `subcategoria` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `transacciones_wallet`
--

DROP TABLE IF EXISTS `transacciones_wallet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `transacciones_wallet` (
  `ID_Transaccion` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Wallet` int(11) NOT NULL,
  `ID_Users` int(11) NOT NULL,
  `tipo` varchar(20) NOT NULL COMMENT 'recarga, compra, admin',
  `monto` float NOT NULL,
  `saldo_anterior` float NOT NULL,
  `saldo_nuevo` float NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `ID_Pedido` int(11) DEFAULT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`ID_Transaccion`),
  KEY `ID_Pedido` (`ID_Pedido`),
  KEY `idx_wallet` (`ID_Wallet`),
  KEY `idx_usuario_tipo` (`ID_Users`,`tipo`),
  KEY `idx_fecha` (`fecha`),
  KEY `idx_tipo` (`tipo`),
  CONSTRAINT `transacciones_wallet_ibfk_1` FOREIGN KEY (`ID_Wallet`) REFERENCES `wallet` (`ID_Wallet`) ON DELETE CASCADE,
  CONSTRAINT `transacciones_wallet_ibfk_2` FOREIGN KEY (`ID_Users`) REFERENCES `users` (`ID_Users`) ON DELETE CASCADE,
  CONSTRAINT `transacciones_wallet_ibfk_3` FOREIGN KEY (`ID_Pedido`) REFERENCES `pedido` (`ID_Pedido`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transacciones_wallet`
--

LOCK TABLES `transacciones_wallet` WRITE;
/*!40000 ALTER TABLE `transacciones_wallet` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `transacciones_wallet` VALUES
(1,1,1,'compra',-690,11998,11308,'Compra - Pedido #1',1,'2025-11-25 15:33:29'),
(2,1,1,'compra',-569.99,11308,10738,'Compra - Pedido #2',2,'2025-11-29 23:59:43');
/*!40000 ALTER TABLE `transacciones_wallet` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `ID_Users` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password` varchar(200) NOT NULL,
  `fecha_registro` datetime DEFAULT current_timestamp(),
  `es_admin` tinyint(1) DEFAULT 0,
  `total_compras` int(11) DEFAULT 0,
  `total_gastado` float DEFAULT 0,
  `ticket_promedio` float DEFAULT 0,
  `ultimo_pedido_fecha` datetime DEFAULT NULL,
  `dias_desde_ultima_compra` int(11) DEFAULT NULL,
  `total_recargas` int(11) DEFAULT 0,
  `dinero_recargado_total` float DEFAULT 0,
  `recarga_promedio` float DEFAULT 0,
  `ultima_recarga_fecha` datetime DEFAULT NULL,
  `productos_carrito_actual` int(11) DEFAULT 0,
  `valor_carrito_actual` float DEFAULT 0,
  `productos_agregados_carrito_total` int(11) DEFAULT 0,
  `carritos_abandonados` int(11) DEFAULT 0,
  `tasa_conversion` float DEFAULT 0,
  `segmento_cliente` varchar(50) DEFAULT 'nuevo',
  `ultima_actividad` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`ID_Users`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_email` (`email`),
  KEY `idx_segmento` (`segmento_cliente`),
  KEY `idx_total_gastado` (`total_gastado`),
  KEY `idx_ultima_actividad` (`ultima_actividad`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `users` VALUES
(1,'Administrador','admin@axionstore.com','pbkdf2:sha256:600000$b81e5VbpFcAz5JAP$2a3475a1cabc2b1664c9bc19aa708fd3c799743c127b9c2c22d4a9611f9a06ac','2025-11-24 00:00:00',1,2,1259.99,629.995,'2025-11-29 23:59:43',0,0,0,0,NULL,0,0,2,0,250,'activo','2025-11-29 23:59:43'),
(2,'Hola','hola@gmail.com','pbkdf2:sha256:600000$gfAK2AyBHcHDFsoU$77a5c03ecf55097747f13a72f13142bf05ecb9c3793edc05ccb6b4a63d1636c1','2025-11-24 00:00:00',0,0,0,0,NULL,1,0,0,0,NULL,2,1099.98,4,0,0,'nuevo','2025-11-29 20:57:32'),
(13,'Aranza Ascanio','aranzaascanio582@gmail.com','pbkdf2:sha256:600000$ROfl8tionyrE3Ut3$982cf2a4bd9e61182d80af1ba25246348617a25af41a81ea940c1c241df7ad6d','2025-11-24 00:00:00',0,0,0,0,NULL,NULL,0,0,0,NULL,0,0,0,0,0,'nuevo','2025-11-25 01:00:10'),
(14,'Leonardo Escobar','alexanderccyt@gmail.com','pbkdf2:sha256:600000$h71Zbh6sJBSxziwz$af8cc2765016b12eb768e4f3e91d541d28bd2be0bd94363f217913d1ff100546','2025-11-24 00:00:00',0,0,0,0,NULL,NULL,0,0,0,NULL,0,0,0,0,0,'nuevo','2025-11-25 01:00:10'),
(15,'Stephany Rodríguez','alexyfifi1@gmail.com','pbkdf2:sha256:600000$mfKIGS9EtLCAFkKP$7e0772f455756e8bcaee630b990f877fcffebd1549f017b1212a3f2eba3ee55a','2025-11-24 00:00:00',0,0,0,0,NULL,NULL,0,0,0,NULL,0,0,0,0,0,'nuevo','2025-11-25 01:00:10'),
(16,'probando esto','a@las2.am','pbkdf2:sha256:600000$sVea1uQN2kBfExFb$b2a72c70e3ba7781a80eeb8626d820c18df6338618be836b731a03f4794b024b','2025-11-25 05:55:45',0,0,0,0,NULL,NULL,0,0,0,NULL,0,0,0,0,0,'nuevo','2025-11-25 05:55:45'),
(17,'Ñema','123@gmail.com','pbkdf2:sha256:600000$rx4VEY4hINXQfwhC$7ac6849b75d7da06c19719b6863e53f2d543c61d86c66b796f7bfb3d95baafa7','2025-11-25 15:43:05',0,0,0,0,NULL,NULL,0,0,0,NULL,0,0,0,0,0,'nuevo','2025-11-25 15:43:05'),
(18,'juan peres','tu@gmail.com','pbkdf2:sha256:1000000$VXK5Urglxz1mfZ5x$959658695052340528d0c749ab8c7f236ab0903a8af5bef9d2d48957aefc0a41','2025-11-30 00:12:36',0,0,0,0,NULL,NULL,0,0,0,NULL,0,0,0,0,0,'nuevo','2025-11-30 00:12:36'),
(19,'nigegermas','sdadadada@gmail.com','pbkdf2:sha256:1000000$VNzfMVhy0DYOV9I2$f868ff841a948ebef4175d473656eec8f193008ba4841b7284b55c3e8b542ed6','2025-11-30 00:13:48',0,0,0,0,NULL,NULL,0,0,0,NULL,2,598,2,0,0,'nuevo','2025-11-30 00:14:44');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `wallet`
--

DROP TABLE IF EXISTS `wallet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `wallet` (
  `ID_Wallet` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Users` int(11) NOT NULL,
  `saldo` float DEFAULT 50,
  PRIMARY KEY (`ID_Wallet`),
  KEY `idx_users` (`ID_Users`),
  CONSTRAINT `wallet_ibfk_1` FOREIGN KEY (`ID_Users`) REFERENCES `users` (`ID_Users`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wallet`
--

LOCK TABLES `wallet` WRITE;
/*!40000 ALTER TABLE `wallet` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `wallet` VALUES
(1,1,10738),
(2,2,163.02),
(13,13,50),
(14,14,50),
(15,15,50),
(16,16,50),
(17,17,50),
(18,18,50),
(19,19,50);
/*!40000 ALTER TABLE `wallet` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `wishlist`
--

DROP TABLE IF EXISTS `wishlist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `wishlist` (
  `ID_Wishlist` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Users` int(11) NOT NULL,
  `ID_Producto` int(11) NOT NULL,
  `fecha_agregado` datetime DEFAULT NULL,
  PRIMARY KEY (`ID_Wishlist`),
  UNIQUE KEY `unique_user_product_wishlist` (`ID_Users`,`ID_Producto`),
  KEY `ix_wishlist_ID_Producto` (`ID_Producto`),
  KEY `ix_wishlist_ID_Users` (`ID_Users`),
  CONSTRAINT `wishlist_ibfk_1` FOREIGN KEY (`ID_Users`) REFERENCES `users` (`ID_Users`),
  CONSTRAINT `wishlist_ibfk_2` FOREIGN KEY (`ID_Producto`) REFERENCES `producto` (`ID_Producto`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wishlist`
--

LOCK TABLES `wishlist` WRITE;
/*!40000 ALTER TABLE `wishlist` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `wishlist` VALUES
(1,2,31,'2025-11-29 20:57:16'),
(2,1,31,'2025-11-29 21:42:33');
/*!40000 ALTER TABLE `wishlist` ENABLE KEYS */;
UNLOCK TABLES;
commit;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-12-01 10:14:22

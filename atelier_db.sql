-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Nov 20, 2026 at 01:53 AM
-- Server version: 8.0.45
-- PHP Version: 8.3.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `atelier_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `compras_insumos`
--

CREATE TABLE `compras_insumos` (
  `id_compra` int NOT NULL,
  `id_proveedor` int NOT NULL,
  `id_material` int NOT NULL,
  `id_usuario_solicita` int NOT NULL,
  `cantidad` decimal(10,2) NOT NULL,
  `costo_total` decimal(10,2) NOT NULL,
  `estado` enum('Solicitado','Aprobado','Recibido','Cancelado') COLLATE utf8mb4_unicode_ci DEFAULT 'Solicitado',
  `fecha_compra` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `detalle_orden_produccion`
--

CREATE TABLE `detalle_orden_produccion` (
  `id_detalle` int NOT NULL,
  `id_pedido` int NOT NULL,
  `id_producto` int NOT NULL,
  `cantidad` int NOT NULL DEFAULT '1',
  `subtotal` decimal(10,2) NOT NULL,
  `id_operario_asignado` int DEFAULT NULL,
  `fase_kanban` enum('Pendiente','Corte y Armado','Barnizado y Secado','Control Calidad','Terminado') COLLATE utf8mb4_unicode_ci DEFAULT 'Pendiente',
  `horas_invertidas` decimal(5,2) DEFAULT '0.00',
  `calificacion_cliente` tinyint DEFAULT NULL,
  `comentario_resena` text COLLATE utf8mb4_unicode_ci,
  `fecha_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `detalle_orden_produccion`
--

INSERT INTO `detalle_orden_produccion` (`id_detalle`, `id_pedido`, `id_producto`, `cantidad`, `subtotal`, `id_operario_asignado`, `fase_kanban`, `horas_invertidas`, `calificacion_cliente`, `comentario_resena`, `fecha_actualizacion`) VALUES
(1, 101, 1, 2, 3700.00, 6, 'Corte y Armado', 4.50, NULL, NULL, '2026-11-19 18:25:50'),
(2, 101, 2, 1, 7400.00, 7, 'Barnizado y Secado', 12.00, NULL, NULL, '2026-11-19 18:25:50'),
(3, 102, 3, 1, 12900.00, NULL, 'Pendiente', 0.00, NULL, NULL, '2026-11-19 18:25:50'),
(4, 103, 5, 1, 9800.00, 7, 'Control Calidad', 15.50, 5, 'Excelente acabado en la madera y puntualidad en la entrega.', '2026-11-19 18:25:50');

-- --------------------------------------------------------

--
-- Table structure for table `logistica_instalacion`
--

CREATE TABLE `logistica_instalacion` (
  `id_envio` int NOT NULL,
  `id_pedido` int NOT NULL,
  `id_chofer` int DEFAULT NULL,
  `id_instalador` int DEFAULT NULL,
  `direccion_entrega` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_programada` datetime DEFAULT NULL,
  `estado_entrega` enum('Programado','En Ruta','Instalando','Finalizado') COLLATE utf8mb4_unicode_ci DEFAULT 'Programado',
  `evidencia_foto_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `materia_prima`
--

CREATE TABLE `materia_prima` (
  `id_material` int NOT NULL,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `unidad_medida` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stock_actual` decimal(10,2) NOT NULL DEFAULT '0.00',
  `stock_minimo` decimal(10,2) NOT NULL DEFAULT '5.00',
  `costo_unitario` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `materia_prima`
--

INSERT INTO `materia_prima` (`id_material`, `nombre`, `unidad_medida`, `stock_actual`, `stock_minimo`, `costo_unitario`) VALUES
(1, 'Tablón Madera de Pino 2.40m', 'Piezas', 45.00, 10.00, 320.00),
(2, 'Tablón Parota / Caoba', 'Piezas', 18.00, 5.00, 1450.00),
(3, 'Resina Epóxica Cristal', 'Litros', 12.00, 4.00, 580.00),
(4, 'Hoja Melamina Nogal 16mm', 'Hojas', 30.00, 8.00, 890.00),
(5, 'Laca Poliuretano Mate', 'Litros', 20.00, 5.00, 410.00),
(6, 'Kit Correderas y Bisagras', 'Juegos', 50.00, 15.00, 185.00);

-- --------------------------------------------------------

--
-- Table structure for table `pedidos`
--

CREATE TABLE `pedidos` (
  `id_pedido` int NOT NULL,
  `id_cliente` int NOT NULL,
  `id_vendedor` int DEFAULT NULL,
  `total` decimal(10,2) NOT NULL,
  `estado_pedido` enum('Cotizacion','Pagado','En Produccion','Listo Envio','Entregado') COLLATE utf8mb4_unicode_ci DEFAULT 'Pagado',
  `fecha_pedido` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `pedidos`
--

INSERT INTO `pedidos` (`id_pedido`, `id_cliente`, `id_vendedor`, `total`, `estado_pedido`, `fecha_pedido`) VALUES
(101, 5, 3, 11100.00, 'En Produccion', '2026-11-19 18:25:50'),
(102, 5, 3, 12900.00, 'Pagado', '2026-11-19 18:25:50'),
(103, 5, 3, 9800.00, 'En Produccion', '2026-11-19 18:25:50'),
(104, 5, 3, 14800.00, 'Cotizacion', '2026-11-19 18:25:50');

-- --------------------------------------------------------

--
-- Table structure for table `productos`
--

CREATE TABLE `productos` (
  `id_producto` int NOT NULL,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_unicode_ci,
  `categoria` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `precio_venta` decimal(10,2) NOT NULL,
  `tiempo_estimado_horas` int NOT NULL,
  `requiere_instalacion` tinyint(1) DEFAULT '0',
  `imagen_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `activo` tinyint(1) DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `productos`
--

INSERT INTO `productos` (`id_producto`, `nombre`, `descripcion`, `categoria`, `precio_venta`, `tiempo_estimado_horas`, `requiere_instalacion`, `imagen_url`, `activo`) VALUES
(1, 'Silla de Comedor Clásica', 'Silla ergonómica de madera de pino estufado con acabado en laca mate.', 'Comedor', 1850.00, 6, 0, 'assets/img/silla.jpg', 1),
(2, 'Mesa de Centro con Resina Epóxica', 'Tablón natural de parota con río de resina cristal y pulido espejo.', 'Sala', 7400.00, 18, 0, 'assets/img/mesa_resina.jpg', 1),
(3, 'Clóset Modular de Melamina', 'Clóset de 2.40m x 2.00m con cajoneras, maletero y tapacantos PVC.', 'Recámara', 12900.00, 14, 1, 'assets/img/closet.jpg', 1),
(4, 'Escritorio de Oficina Minimalista', 'Cubierta de madera sólida con 3 cajones y correderas de extensión.', 'Oficina', 5200.00, 10, 0, 'assets/img/escritorio.jpg', 1),
(5, 'Puerta Principal de Madera Sólida', 'Puerta exterior en caoba machihembrada con sellador UV y marco.', 'Exterior', 9800.00, 16, 1, 'assets/img/puerta.jpg', 1);

-- --------------------------------------------------------

--
-- Table structure for table `proveedores`
--

CREATE TABLE `proveedores` (
  `id_proveedor` int NOT NULL,
  `nombre_empresa` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `contacto` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `telefono` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `categoria_insumo` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `proveedores`
--

INSERT INTO `proveedores` (`id_proveedor`, `nombre_empresa`, `contacto`, `telefono`, `categoria_insumo`) VALUES
(1, 'Maderas del Bajío S.A.', 'Ing. Marcos Ruiz', '4772223344', 'Madera Sólida y Tablones'),
(2, 'Recubrimientos y Resinas MX', 'Lic. Sofía Díaz', '4775556677', 'Barnices, Lacas y Epóxicos'),
(3, 'Tableros y Herrajes Industriales', 'Jorge Méndez', '4778889900', 'Melamina y Correderas');

-- --------------------------------------------------------

--
-- Table structure for table `receta_proceso_producto`
--

CREATE TABLE `receta_proceso_producto` (
  `id_receta` int NOT NULL,
  `id_producto` int NOT NULL,
  `id_material` int NOT NULL,
  `cantidad_necesaria` decimal(10,2) NOT NULL,
  `orden_fase` int NOT NULL,
  `id_rol_responsable` int NOT NULL,
  `instruccion_tecnica` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `receta_proceso_producto`
--

INSERT INTO `receta_proceso_producto` (`id_receta`, `id_producto`, `id_material`, `cantidad_necesaria`, `orden_fase`, `id_rol_responsable`, `instruccion_tecnica`) VALUES
(1, 1, 1, 1.50, 1, 6, 'Corte, torneado de patas y ensamble con espiga'),
(2, 1, 5, 0.40, 2, 7, 'Aplicación de tinte y dos manos de laca mate'),
(3, 2, 2, 1.00, 1, 6, 'Cepillado, canteado y preparación de molde'),
(4, 2, 3, 3.50, 2, 7, 'Vaciado de resina epóxica, curado 24h y pulido'),
(5, 3, 4, 3.00, 1, 6, 'Corte optimizado de hojas de melamina y enchapado'),
(6, 3, 6, 4.00, 2, 8, 'Traslado en piezas y armado modular en domicilio'),
(7, 4, 1, 2.00, 1, 6, 'Armado de cubierta y ensamble de cajonera'),
(8, 4, 6, 3.00, 2, 6, 'Instalación de correderas telescópicas'),
(9, 5, 2, 2.50, 1, 6, 'Machihembrado, prensado y molduras'),
(10, 5, 5, 1.20, 2, 7, 'Sellador para intemperie y montaje en marco por instalador');

-- --------------------------------------------------------

--
-- Table structure for table `roles`
--

CREATE TABLE `roles` (
  `id_rol` int NOT NULL,
  `nombre_rol` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `roles`
--

INSERT INTO `roles` (`id_rol`, `nombre_rol`, `descripcion`) VALUES
(1, 'Administrador', 'Control total, KPIs y gestión de usuarios'),
(2, 'Almacen', 'Control de inventario y entregas de material'),
(3, 'Ventas', 'CRM, cotizaciones y seguimiento de clientes'),
(4, 'Compras', 'Requisiciones y órdenes a proveedores'),
(5, 'Cliente', 'Compra en PWA y rastreo en tiempo real'),
(6, 'Carpintero', 'Corte, ensamble y armado en taller'),
(7, 'Barnizador', 'Tinte, laca, sellador y resina epóxica'),
(8, 'Instalador', 'Armado y montaje en domicilio'),
(9, 'Logistica', 'Rutas, fletes y entregas');

-- --------------------------------------------------------

--
-- Table structure for table `usuarios`
--

CREATE TABLE `usuarios` (
  `id_usuario` int NOT NULL,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `direccion` text COLLATE utf8mb4_unicode_ci,
  `id_rol` int NOT NULL,
  `activo` tinyint(1) DEFAULT '1',
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `usuarios`
--

INSERT INTO `usuarios` (`id_usuario`, `nombre`, `email`, `password_hash`, `telefono`, `direccion`, `id_rol`, `activo`, `fecha_registro`) VALUES
(1, 'Admin General', 'admin@atelier.com', 'admin123', '4771000001', 'Taller Central León', 1, 1, '2026-11-19 18:25:50'),
(2, 'Carlos Almacén', 'almacen@atelier.com', '123456', '4771000002', 'Bodega 1', 2, 1, '2026-11-19 18:25:50'),
(3, 'Laura Ventas', 'ventas@atelier.com', '123456', '4771000003', 'Oficina Comercial', 3, 1, '2026-11-19 18:25:50'),
(4, 'Roberto Compras', 'compras@atelier.com', '123456', '4771000004', 'Oficina Compras', 4, 1, '2026-11-19 18:25:50'),
(5, 'Ana Cliente', 'cliente@gmail.com', '123456', '4771000005', 'Blvd. Campestre #410, León', 5, 1, '2026-11-19 18:25:50'),
(6, 'José Carpintero', 'carpintero@atelier.com', '123456', '4771000006', 'Área Corte y Armado', 6, 1, '2026-11-19 18:25:50'),
(7, 'Miguel Barnizador', 'barniz@atelier.com', '123456', '4771000007', 'Cabina de Acabados', 7, 1, '2026-11-19 18:25:50'),
(8, 'Pedro Instalador', 'instalador@atelier.com', '123456', '4771000008', 'Unidad Móvil 1', 8, 1, '2026-11-19 18:25:50'),
(9, 'Luis Logística', 'logistica@atelier.com', '123456', '4771000009', 'Patio Maniobras', 9, 1, '2026-11-19 18:25:50'),
(10, 'Romote', 'romo@atelier.com', '12345', '4771234567', 'Carpintero', 6, 1, '2026-11-20 01:21:22'),
(12, 'Kevin', 'kevin@atelier.com', '123456', '4772536984', 'Logistica', 9, 1, '2026-11-20 01:46:52');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `compras_insumos`
--
ALTER TABLE `compras_insumos`
  ADD PRIMARY KEY (`id_compra`),
  ADD KEY `id_proveedor` (`id_proveedor`),
  ADD KEY `id_material` (`id_material`),
  ADD KEY `id_usuario_solicita` (`id_usuario_solicita`);

--
-- Indexes for table `detalle_orden_produccion`
--
ALTER TABLE `detalle_orden_produccion`
  ADD PRIMARY KEY (`id_detalle`),
  ADD KEY `id_pedido` (`id_pedido`),
  ADD KEY `id_producto` (`id_producto`),
  ADD KEY `id_operario_asignado` (`id_operario_asignado`);

--
-- Indexes for table `logistica_instalacion`
--
ALTER TABLE `logistica_instalacion`
  ADD PRIMARY KEY (`id_envio`),
  ADD KEY `id_pedido` (`id_pedido`),
  ADD KEY `id_chofer` (`id_chofer`),
  ADD KEY `id_instalador` (`id_instalador`);

--
-- Indexes for table `materia_prima`
--
ALTER TABLE `materia_prima`
  ADD PRIMARY KEY (`id_material`);

--
-- Indexes for table `pedidos`
--
ALTER TABLE `pedidos`
  ADD PRIMARY KEY (`id_pedido`),
  ADD KEY `id_cliente` (`id_cliente`),
  ADD KEY `id_vendedor` (`id_vendedor`);

--
-- Indexes for table `productos`
--
ALTER TABLE `productos`
  ADD PRIMARY KEY (`id_producto`);

--
-- Indexes for table `proveedores`
--
ALTER TABLE `proveedores`
  ADD PRIMARY KEY (`id_proveedor`);

--
-- Indexes for table `receta_proceso_producto`
--
ALTER TABLE `receta_proceso_producto`
  ADD PRIMARY KEY (`id_receta`),
  ADD KEY `id_producto` (`id_producto`),
  ADD KEY `id_material` (`id_material`),
  ADD KEY `id_rol_responsable` (`id_rol_responsable`);

--
-- Indexes for table `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id_rol`),
  ADD UNIQUE KEY `nombre_rol` (`nombre_rol`);

--
-- Indexes for table `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id_usuario`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `id_rol` (`id_rol`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `compras_insumos`
--
ALTER TABLE `compras_insumos`
  MODIFY `id_compra` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `detalle_orden_produccion`
--
ALTER TABLE `detalle_orden_produccion`
  MODIFY `id_detalle` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `logistica_instalacion`
--
ALTER TABLE `logistica_instalacion`
  MODIFY `id_envio` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `materia_prima`
--
ALTER TABLE `materia_prima`
  MODIFY `id_material` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `pedidos`
--
ALTER TABLE `pedidos`
  MODIFY `id_pedido` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=105;

--
-- AUTO_INCREMENT for table `productos`
--
ALTER TABLE `productos`
  MODIFY `id_producto` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `proveedores`
--
ALTER TABLE `proveedores`
  MODIFY `id_proveedor` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `receta_proceso_producto`
--
ALTER TABLE `receta_proceso_producto`
  MODIFY `id_receta` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `roles`
--
ALTER TABLE `roles`
  MODIFY `id_rol` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id_usuario` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `compras_insumos`
--
ALTER TABLE `compras_insumos`
  ADD CONSTRAINT `compras_insumos_ibfk_1` FOREIGN KEY (`id_proveedor`) REFERENCES `proveedores` (`id_proveedor`),
  ADD CONSTRAINT `compras_insumos_ibfk_2` FOREIGN KEY (`id_material`) REFERENCES `materia_prima` (`id_material`),
  ADD CONSTRAINT `compras_insumos_ibfk_3` FOREIGN KEY (`id_usuario_solicita`) REFERENCES `usuarios` (`id_usuario`);

--
-- Constraints for table `detalle_orden_produccion`
--
ALTER TABLE `detalle_orden_produccion`
  ADD CONSTRAINT `detalle_orden_produccion_ibfk_1` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`) ON DELETE CASCADE,
  ADD CONSTRAINT `detalle_orden_produccion_ibfk_2` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`),
  ADD CONSTRAINT `detalle_orden_produccion_ibfk_3` FOREIGN KEY (`id_operario_asignado`) REFERENCES `usuarios` (`id_usuario`);

--
-- Constraints for table `logistica_instalacion`
--
ALTER TABLE `logistica_instalacion`
  ADD CONSTRAINT `logistica_instalacion_ibfk_1` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`) ON DELETE CASCADE,
  ADD CONSTRAINT `logistica_instalacion_ibfk_2` FOREIGN KEY (`id_chofer`) REFERENCES `usuarios` (`id_usuario`),
  ADD CONSTRAINT `logistica_instalacion_ibfk_3` FOREIGN KEY (`id_instalador`) REFERENCES `usuarios` (`id_usuario`);

--
-- Constraints for table `pedidos`
--
ALTER TABLE `pedidos`
  ADD CONSTRAINT `pedidos_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `usuarios` (`id_usuario`),
  ADD CONSTRAINT `pedidos_ibfk_2` FOREIGN KEY (`id_vendedor`) REFERENCES `usuarios` (`id_usuario`);

--
-- Constraints for table `receta_proceso_producto`
--
ALTER TABLE `receta_proceso_producto`
  ADD CONSTRAINT `receta_proceso_producto_ibfk_1` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`) ON DELETE CASCADE,
  ADD CONSTRAINT `receta_proceso_producto_ibfk_2` FOREIGN KEY (`id_material`) REFERENCES `materia_prima` (`id_material`),
  ADD CONSTRAINT `receta_proceso_producto_ibfk_3` FOREIGN KEY (`id_rol_responsable`) REFERENCES `roles` (`id_rol`);

--
-- Constraints for table `usuarios`
--
ALTER TABLE `usuarios`
  ADD CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id_rol`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

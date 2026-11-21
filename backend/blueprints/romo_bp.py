from flask import Blueprint, request, jsonify


def crear_blueprint_romo(conectar_db):
    romo_bp = Blueprint('romo', __name__)

    FASES_VALIDAS = [
        'Pendiente',
        'Corte y Armado',
        'Barnizado y Secado',
        'Control Calidad',
        'Terminado'
    ]

    # =====================================================================
    # MÓDULOS 1 Y 2: PRODUCCIÓN KANBAN (ARMADO Y PINTURA/ACABADOS)
    # =====================================================================

    @romo_bp.route('/api/produccion/catalogos', methods=['GET'])
    def catalogos_produccion():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            # Rol 6 = Carpintero, Rol 7 = Barnizador
            cursor.execute("""
                SELECT u.id_usuario, u.nombre, u.id_rol, r.nombre_rol
                FROM usuarios u
                INNER JOIN roles r ON u.id_rol = r.id_rol
                WHERE u.id_rol IN (6, 7) AND u.activo = 1
                ORDER BY u.nombre ASC
            """)
            operarios = cursor.fetchall()

            return jsonify({
                'success': True,
                'fases': FASES_VALIDAS,
                'operarios': operarios
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @romo_bp.route('/api/produccion/ordenes', methods=['GET'])
    def listar_ordenes_produccion():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT d.id_detalle,
                       d.id_pedido,
                       d.id_producto,
                       d.cantidad,
                       d.subtotal,
                       d.id_operario_asignado,
                       d.fase_kanban,
                       d.horas_invertidas,
                       d.fecha_actualizacion,
                       p.estado_pedido,
                       c.nombre AS cliente_nombre,
                       pr.nombre AS producto_nombre,
                       pr.categoria AS producto_categoria,
                       pr.tiempo_estimado_horas,
                       op.nombre AS operario_nombre
                FROM detalle_orden_produccion d
                INNER JOIN pedidos p ON d.id_pedido = p.id_pedido
                INNER JOIN usuarios c ON p.id_cliente = c.id_usuario
                INNER JOIN productos pr ON d.id_producto = pr.id_producto
                LEFT JOIN usuarios op ON d.id_operario_asignado = op.id_usuario
                WHERE p.estado_pedido != 'Cotizacion'
                ORDER BY d.id_pedido ASC, d.id_detalle ASC
            """)
            ordenes = cursor.fetchall()

            for o in ordenes:
                o['subtotal'] = float(o['subtotal'])
                o['horas_invertidas'] = float(o['horas_invertidas'] or 0)
                o['operario_nombre'] = o['operario_nombre'] or 'Sin asignar'
                o['fecha_actualizacion'] = str(o['fecha_actualizacion'])[:16] if o['fecha_actualizacion'] else ''

            return jsonify({'success': True, 'ordenes': ordenes}), 200
        except Exception as e:
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @romo_bp.route('/api/produccion/ordenes/<int:id_detalle>', methods=['PUT'])
    def actualizar_orden_produccion(id_detalle):
        data = request.get_json(silent=True) or {}
        nueva_fase = data.get('fase_kanban')
        id_operario = data.get('id_operario_asignado')
        horas = float(data.get('horas_invertidas', 0) or 0)

        if nueva_fase not in FASES_VALIDAS:
            return jsonify({'success': False, 'mensaje': 'Fase Kanban inválida.'}), 400

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id_pedido FROM detalle_orden_produccion WHERE id_detalle = %s", (id_detalle,))
            actual = cursor.fetchone()
            if not actual:
                return jsonify({'success': False, 'mensaje': 'Orden de producción no encontrada.'}), 404

            cursor.execute("""
                UPDATE detalle_orden_produccion
                SET fase_kanban = %s,
                    id_operario_asignado = %s,
                    horas_invertidas = %s
                WHERE id_detalle = %s
            """, (
                nueva_fase,
                int(id_operario) if id_operario else None,
                horas,
                id_detalle
            ))

            # Sincronizar estado general del pedido en tabla pedidos
            id_pedido = actual['id_pedido']
            cursor.execute("""
                SELECT COUNT(*) AS pendientes
                FROM detalle_orden_produccion
                WHERE id_pedido = %s AND fase_kanban != 'Terminado'
            """, (id_pedido,))
            pendientes = cursor.fetchone()['pendientes']

            if pendientes == 0:
                cursor.execute(
                    "UPDATE pedidos SET estado_pedido = 'Listo Envio' WHERE id_pedido = %s AND estado_pedido != 'Entregado'",
                    (id_pedido,)
                )
            elif nueva_fase != 'Pendiente':
                cursor.execute(
                    "UPDATE pedidos SET estado_pedido = 'En Produccion' WHERE id_pedido = %s AND estado_pedido = 'Pagado'",
                    (id_pedido,)
                )

            conn.commit()
            return jsonify({
                'success': True,
                'mensaje': f'Orden #{id_detalle} actualizada a "{nueva_fase}".'
            }), 200
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    # =====================================================================
    # MÓDULO 3: CATÁLOGO DE PRODUCTOS Y RECETAS DE PRODUCCIÓN (BOM)
    # =====================================================================

    @romo_bp.route('/api/recetas', methods=['GET'])
    def listar_productos_y_recetas():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM productos ORDER BY id_producto ASC")
            productos = cursor.fetchall()
            for p in productos:
                p['precio_venta'] = float(p['precio_venta'])

            cursor.execute("""
                SELECT r.id_receta, r.id_producto, r.id_material,
                       r.cantidad_necesaria, r.orden_fase,
                       r.id_rol_responsable, r.instruccion_tecnica,
                       m.nombre AS material_nombre, m.unidad_medida,
                       rol.nombre_rol
                FROM receta_proceso_producto r
                INNER JOIN materia_prima m ON r.id_material = m.id_material
                INNER JOIN roles rol ON r.id_rol_responsable = rol.id_rol
                ORDER BY r.id_producto ASC, r.orden_fase ASC
            """)
            recetas = cursor.fetchall()
            for rec in recetas:
                rec['cantidad_necesaria'] = float(rec['cantidad_necesaria'])

            cursor.execute("SELECT id_material, nombre, unidad_medida FROM materia_prima ORDER BY nombre ASC")
            materiales = cursor.fetchall()

            cursor.execute("SELECT id_rol, nombre_rol FROM roles WHERE id_rol IN (6, 7, 8) ORDER BY id_rol ASC")
            roles_taller = cursor.fetchall()

            return jsonify({
                'success': True,
                'productos': productos,
                'recetas': recetas,
                'materiales': materiales,
                'roles_taller': roles_taller
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @romo_bp.route('/api/recetas/productos', methods=['POST'])
    def crear_producto():
        data = request.get_json(silent=True) or {}
        nombre = (data.get('nombre') or '').strip()
        if not nombre:
            return jsonify({'success': False, 'mensaje': 'El nombre del mueble es obligatorio.'}), 400

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO productos
                    (nombre, descripcion, categoria, precio_venta, tiempo_estimado_horas, requiere_instalacion, imagen_url, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """, (
                nombre,
                data.get('descripcion') or '',
                data.get('categoria') or 'General',
                float(data.get('precio_venta', 0)),
                int(data.get('tiempo_estimado_horas', 8)),
                1 if data.get('requiere_instalacion') else 0,
                data.get('imagen_url') or 'assets/img/mueble.jpg'
            ))
            conn.commit()
            return jsonify({'success': True, 'mensaje': 'Mueble agregado al catálogo.', 'id_producto': cursor.lastrowid}), 201
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @romo_bp.route('/api/recetas/pasos', methods=['POST'])
    def agregar_paso_receta():
        data = request.get_json(silent=True) or {}
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO receta_proceso_producto
                    (id_producto, id_material, cantidad_necesaria, orden_fase, id_rol_responsable, instruccion_tecnica)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                int(data['id_producto']),
                int(data['id_material']),
                float(data['cantidad_necesaria']),
                int(data.get('orden_fase', 1)),
                int(data['id_rol_responsable']),
                (data.get('instruccion_tecnica') or '').strip()
            ))
            conn.commit()
            return jsonify({'success': True, 'mensaje': 'Paso e insumo agregados a la receta.'}), 201
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @romo_bp.route('/api/recetas/pasos/<int:id_receta>', methods=['DELETE'])
    def eliminar_paso_receta(id_receta):
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM receta_proceso_producto WHERE id_receta = %s", (id_receta,))
            conn.commit()
            return jsonify({'success': True, 'mensaje': 'Paso eliminado de la receta.'}), 200
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    return romo_bp
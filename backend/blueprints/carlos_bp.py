import re
from flask import Blueprint, request, jsonify


def crear_blueprint_carlos(conectar_db):
    carlos_bp = Blueprint('carlos', __name__)

    def obtener_estados_entrega(cursor):
        """Lee los valores exactos del ENUM estado_entrega directo de MySQL."""
        cursor.execute("SHOW COLUMNS FROM logistica_instalacion LIKE 'estado_entrega'")
        col = cursor.fetchone()
        if col and col.get('Type'):
            valores = re.findall(r"'([^']+)'", col['Type'])
            if valores:
                return valores
        return ['Programado', 'En Ruta', 'Instalando', 'Finalizado']

    def formatear_fecha_mysql(fecha_str):
        if not fecha_str:
            return None
        limpia = str(fecha_str).strip().replace('T', ' ')
        if len(limpia) == 16:
            limpia += ':00'
        return limpia

    @carlos_bp.route('/api/carlos/prueba', methods=['GET'])
    def prueba_carlos():
        return jsonify({
            'success': True,
            'mensaje': 'Backend de Carlos conectado correctamente'
        }), 200

    # =====================================================================
    # MÓDULO 1: COTIZACIONES Y VENTAS (CRM)
    # =====================================================================

    @carlos_bp.route('/api/cotizaciones/catalogos', methods=['GET'])
    def obtener_catalogos_cotizaciones():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id_usuario, nombre, email, telefono, direccion
                FROM usuarios
                WHERE id_rol = 5 AND activo = 1
                ORDER BY nombre ASC
            """)
            clientes = cursor.fetchall()

            cursor.execute("""
                SELECT id_usuario, nombre, email
                FROM usuarios
                WHERE id_rol IN (1, 3) AND activo = 1
                ORDER BY nombre ASC
            """)
            vendedores = cursor.fetchall()

            cursor.execute("""
                SELECT id_producto, nombre, categoria, precio_venta,
                       tiempo_estimado_horas, requiere_instalacion
                FROM productos
                WHERE activo = 1
                ORDER BY nombre ASC
            """)
            productos = cursor.fetchall()

            return jsonify({
                'success': True,
                'clientes': clientes,
                'vendedores': vendedores,
                'productos': productos
            }), 200
        except Exception as e:
            print(f"[ERROR] CATALOGOS COTIZACIONES: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/cotizaciones', methods=['GET'])
    def listar_cotizaciones():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT p.id_pedido, p.id_cliente, p.id_vendedor, p.total,
                       p.estado_pedido, p.fecha_pedido,
                       c.nombre AS cliente_nombre, c.email AS cliente_email,
                       c.telefono AS cliente_telefono, c.direccion AS cliente_direccion,
                       v.nombre AS vendedor_nombre
                FROM pedidos p
                INNER JOIN usuarios c ON p.id_cliente = c.id_usuario
                LEFT JOIN usuarios v ON p.id_vendedor = v.id_usuario
                ORDER BY (p.estado_pedido = 'Cotizacion') DESC, p.id_pedido DESC
            """)
            pedidos = cursor.fetchall()

            cursor.execute("""
                SELECT d.id_detalle, d.id_pedido, d.id_producto, d.cantidad,
                       d.subtotal, d.fase_kanban,
                       pr.nombre AS producto_nombre, pr.categoria,
                       pr.precio_venta, pr.tiempo_estimado_horas
                FROM detalle_orden_produccion d
                INNER JOIN productos pr ON d.id_producto = pr.id_producto
                ORDER BY d.id_detalle ASC
            """)
            detalles = cursor.fetchall()

            detalles_por_pedido = {}
            for det in detalles:
                det['subtotal'] = float(det['subtotal'])
                det['precio_venta'] = float(det['precio_venta'])
                detalles_por_pedido.setdefault(det['id_pedido'], []).append(det)

            lista = []
            for ped in pedidos:
                items = detalles_por_pedido.get(ped['id_pedido'], [])
                horas_totales = sum(
                    int(it['tiempo_estimado_horas']) * int(it['cantidad']) for it in items
                )
                lista.append({
                    'id_pedido': ped['id_pedido'],
                    'id_cliente': ped['id_cliente'],
                    'cliente_nombre': ped['cliente_nombre'],
                    'cliente_email': ped['cliente_email'],
                    'cliente_telefono': ped['cliente_telefono'] or 'Sin teléfono',
                    'cliente_direccion': ped['cliente_direccion'] or 'Sin dirección registrada',
                    'vendedor_nombre': ped['vendedor_nombre'] or 'Tienda en Línea (PWA)',
                    'total': float(ped['total']),
                    'estado_pedido': ped['estado_pedido'],
                    'fecha_pedido': str(ped['fecha_pedido'])[:16] if ped['fecha_pedido'] else '',
                    'horas_estimadas': horas_totales,
                    'items': items
                })

            cotizaciones_activas = [x for x in lista if x['estado_pedido'] == 'Cotizacion']
            pedidos_cerrados = [x for x in lista if x['estado_pedido'] != 'Cotizacion']
            total_oportunidades = len(lista)
            tasa_conversion = round(
                (len(pedidos_cerrados) / total_oportunidades) * 100, 1
            ) if total_oportunidades > 0 else 0.0

            resumen = {
                'cotizaciones_activas': len(cotizaciones_activas),
                'monto_cotizado': round(sum(x['total'] for x in cotizaciones_activas), 2),
                'pedidos_cerrados': len(pedidos_cerrados),
                'monto_cerrado': round(sum(x['total'] for x in pedidos_cerrados), 2),
                'tasa_conversion': tasa_conversion
            }

            return jsonify({'success': True, 'cotizaciones': lista, 'resumen': resumen}), 200
        except Exception as e:
            print(f"[ERROR] LISTAR COTIZACIONES: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/cotizaciones', methods=['POST'])
    def crear_cotizacion():
        data = request.get_json(silent=True) or {}
        id_cliente = data.get('id_cliente')
        id_vendedor = data.get('id_vendedor')
        items = data.get('items') or []

        if not id_cliente:
            return jsonify({'success': False, 'mensaje': 'Selecciona un cliente.'}), 400
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({'success': False, 'mensaje': 'Agrega al menos un mueble a la cotización.'}), 400

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            lineas = []
            total = 0.0
            for item in items:
                id_prod = int(item.get('id_producto'))
                cant = int(item.get('cantidad', 1))
                if cant <= 0:
                    return jsonify({'success': False, 'mensaje': 'Las cantidades deben ser mayores a 0.'}), 400

                cursor.execute(
                    "SELECT id_producto, precio_venta FROM productos WHERE id_producto = %s AND activo = 1",
                    (id_prod,)
                )
                prod = cursor.fetchone()
                if not prod:
                    return jsonify({'success': False, 'mensaje': f'Producto #{id_prod} no disponible.'}), 404

                subtotal = round(float(prod['precio_venta']) * cant, 2)
                total += subtotal
                lineas.append((id_prod, cant, subtotal))

            total = round(total, 2)
            cursor.execute("""
                INSERT INTO pedidos (id_cliente, id_vendedor, total, estado_pedido, fecha_pedido)
                VALUES (%s, %s, %s, 'Cotizacion', NOW())
            """, (int(id_cliente), int(id_vendedor) if id_vendedor else None, total))
            nuevo_id_pedido = cursor.lastrowid

            for id_prod, cant, subtotal in lineas:
                cursor.execute("""
                    INSERT INTO detalle_orden_produccion
                        (id_pedido, id_producto, cantidad, subtotal, id_operario_asignado, fase_kanban, horas_invertidas)
                    VALUES (%s, %s, %s, %s, NULL, 'Pendiente', 0.00)
                """, (nuevo_id_pedido, id_prod, cant, subtotal))

            conn.commit()
            return jsonify({
                'success': True,
                'mensaje': f'Cotización #{nuevo_id_pedido} creada correctamente.',
                'id_pedido': nuevo_id_pedido,
                'total': total
            }), 201
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] CREAR COTIZACION: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/cotizaciones/<int:id_pedido>/aprobar', methods=['PUT'])
    def aprobar_cotizacion(id_pedido):
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT estado_pedido FROM pedidos WHERE id_pedido = %s", (id_pedido,))
            pedido = cursor.fetchone()
            if not pedido:
                return jsonify({'success': False, 'mensaje': 'Cotización no encontrada.'}), 404
            if pedido['estado_pedido'] != 'Cotizacion':
                return jsonify({'success': False, 'mensaje': 'Este folio ya fue convertido anteriormente.'}), 400

            cursor.execute("UPDATE pedidos SET estado_pedido = 'Pagado' WHERE id_pedido = %s", (id_pedido,))
            conn.commit()
            return jsonify({
                'success': True,
                'mensaje': f'Cotización #{id_pedido} aprobada y convertida a pedido Pagado.'
            }), 200
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] APROBAR COTIZACION: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/cotizaciones/<int:id_pedido>', methods=['DELETE'])
    def eliminar_cotizacion(id_pedido):
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT estado_pedido FROM pedidos WHERE id_pedido = %s", (id_pedido,))
            pedido = cursor.fetchone()
            if not pedido:
                return jsonify({'success': False, 'mensaje': 'Cotización no encontrada.'}), 404
            if pedido['estado_pedido'] != 'Cotizacion':
                return jsonify({'success': False, 'mensaje': 'Solo se pueden eliminar cotizaciones pendientes.'}), 400

            cursor.execute("DELETE FROM pedidos WHERE id_pedido = %s", (id_pedido,))
            conn.commit()
            return jsonify({
                'success': True,
                'mensaje': f'Cotización #{id_pedido} eliminada correctamente.'
            }), 200
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] ELIMINAR COTIZACION: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    # =====================================================================
    # MÓDULO 2: LOGÍSTICA E INSTALACIONES
    # =====================================================================

    @carlos_bp.route('/api/logistica/catalogos', methods=['GET'])
    def obtener_catalogos_logistica():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            estados = obtener_estados_entrega(cursor)

            cursor.execute("""
                SELECT id_usuario, nombre, telefono, direccion
                FROM usuarios
                WHERE id_rol = 9 AND activo = 1
                ORDER BY nombre ASC
            """)
            choferes = cursor.fetchall()

            cursor.execute("""
                SELECT id_usuario, nombre, telefono, direccion
                FROM usuarios
                WHERE id_rol = 8 AND activo = 1
                ORDER BY nombre ASC
            """)
            instaladores = cursor.fetchall()

            cursor.execute("""
                SELECT p.id_pedido, p.estado_pedido, p.total,
                       c.nombre AS cliente_nombre,
                       c.telefono AS cliente_telefono,
                       c.direccion AS cliente_direccion
                FROM pedidos p
                INNER JOIN usuarios c ON p.id_cliente = c.id_usuario
                WHERE p.estado_pedido != 'Cotizacion'
                ORDER BY p.id_pedido DESC
            """)
            pedidos = cursor.fetchall()
            for p in pedidos:
                p['total'] = float(p['total'])

            return jsonify({
                'success': True,
                'estados': estados,
                'choferes': choferes,
                'instaladores': instaladores,
                'pedidos': pedidos
            }), 200
        except Exception as e:
            print(f"[ERROR] CATALOGOS LOGISTICA: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/logistica', methods=['GET'])
    def listar_logistica():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            estados = obtener_estados_entrega(cursor)
            estado_final = estados[-1] if estados else 'Finalizado'

            cursor.execute("""
                SELECT l.id_envio,
                       l.id_pedido,
                       l.id_chofer,
                       l.id_instalador,
                       l.direccion_entrega,
                       l.fecha_programada,
                       l.estado_entrega,
                       l.evidencia_foto_url,
                       p.total AS pedido_total,
                       p.estado_pedido,
                       c.nombre AS cliente_nombre,
                       c.telefono AS cliente_telefono,
                       ch.nombre AS chofer_nombre,
                       inst.nombre AS instalador_nombre
                FROM logistica_instalacion l
                INNER JOIN pedidos p ON l.id_pedido = p.id_pedido
                INNER JOIN usuarios c ON p.id_cliente = c.id_usuario
                LEFT JOIN usuarios ch ON l.id_chofer = ch.id_usuario
                LEFT JOIN usuarios inst ON l.id_instalador = inst.id_usuario
                ORDER BY l.id_envio DESC
            """)
            envios = cursor.fetchall()

            lista = []
            for env in envios:
                fecha_txt = str(env['fecha_programada'])[:16] if env['fecha_programada'] else ''
                lista.append({
                    'id_envio': env['id_envio'],
                    'id_pedido': env['id_pedido'],
                    'id_chofer': env['id_chofer'],
                    'id_instalador': env['id_instalador'],
                    'direccion_entrega': env['direccion_entrega'],
                    'fecha_programada': fecha_txt,
                    'fecha_input': fecha_txt.replace(' ', 'T') if fecha_txt else '',
                    'estado_entrega': env['estado_entrega'],
                    'evidencia_foto_url': env['evidencia_foto_url'] or '',
                    'pedido_total': float(env['pedido_total']),
                    'estado_pedido': env['estado_pedido'],
                    'cliente_nombre': env['cliente_nombre'],
                    'cliente_telefono': env['cliente_telefono'] or 'Sin teléfono',
                    'chofer_nombre': env['chofer_nombre'] or 'Sin asignar',
                    'instalador_nombre': env['instalador_nombre'] or 'No requerido / Sin asignar'
                })

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM pedidos p
                LEFT JOIN logistica_instalacion l ON p.id_pedido = l.id_pedido
                WHERE p.estado_pedido NOT IN ('Cotizacion', 'Entregado')
                  AND l.id_envio IS NULL
            """)
            pendientes_programar = cursor.fetchone()['total']

            resumen = {
                'programados': sum(1 for x in lista if x['estado_entrega'] == 'Programado'),
                'en_curso': sum(1 for x in lista if x['estado_entrega'] in ('En Ruta', 'Instalando')),
                'finalizados': sum(1 for x in lista if x['estado_entrega'] == estado_final),
                'pendientes_programar': pendientes_programar
            }

            return jsonify({
                'success': True,
                'envios': lista,
                'estados': estados,
                'estado_final': estado_final,
                'resumen': resumen
            }), 200
        except Exception as e:
            print(f"[ERROR] LISTAR LOGISTICA: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/logistica', methods=['POST'])
    def crear_envio():
        data = request.get_json(silent=True) or {}
        id_pedido = data.get('id_pedido')
        id_chofer = data.get('id_chofer')
        id_instalador = data.get('id_instalador')
        direccion = (data.get('direccion_entrega') or '').strip()
        fecha_programada = formatear_fecha_mysql(data.get('fecha_programada'))

        if not id_pedido:
            return jsonify({'success': False, 'mensaje': 'Selecciona un pedido.'}), 400
        if not direccion:
            return jsonify({'success': False, 'mensaje': 'Escribe la dirección de entrega.'}), 400

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                INSERT INTO logistica_instalacion
                    (id_pedido, id_chofer, id_instalador, direccion_entrega, fecha_programada, estado_entrega, evidencia_foto_url)
                VALUES (%s, %s, %s, %s, %s, 'Programado', NULL)
            """, (
                int(id_pedido),
                int(id_chofer) if id_chofer else None,
                int(id_instalador) if id_instalador else None,
                direccion,
                fecha_programada
            ))
            nuevo_id = cursor.lastrowid
            conn.commit()
            return jsonify({
                'success': True,
                'mensaje': f'Envío #{nuevo_id} programado correctamente para el pedido #{id_pedido}.',
                'id_envio': nuevo_id
            }), 201
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] CREAR ENVIO: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/logistica/<int:id_envio>', methods=['PUT'])
    def actualizar_envio(id_envio):
        data = request.get_json(silent=True) or {}
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            estados = obtener_estados_entrega(cursor)
            estado_final = estados[-1] if estados else 'Finalizado'

            cursor.execute("SELECT id_pedido FROM logistica_instalacion WHERE id_envio = %s", (id_envio,))
            actual = cursor.fetchone()
            if not actual:
                return jsonify({'success': False, 'mensaje': 'Envío no encontrado.'}), 404

            estado_nuevo = data.get('estado_entrega') or 'Programado'
            if estado_nuevo not in estados:
                return jsonify({'success': False, 'mensaje': f'Estado inválido. Usa uno de: {estados}'}), 400

            direccion = (data.get('direccion_entrega') or '').strip()
            if not direccion:
                return jsonify({'success': False, 'mensaje': 'La dirección de entrega no puede estar vacía.'}), 400

            fecha_prog = formatear_fecha_mysql(data.get('fecha_programada'))
            evidencia = (data.get('evidencia_foto_url') or '').strip() or None

            cursor.execute("""
                UPDATE logistica_instalacion
                SET id_chofer = %s,
                    id_instalador = %s,
                    direccion_entrega = %s,
                    fecha_programada = %s,
                    estado_entrega = %s,
                    evidencia_foto_url = %s
                WHERE id_envio = %s
            """, (
                int(data['id_chofer']) if data.get('id_chofer') else None,
                int(data['id_instalador']) if data.get('id_instalador') else None,
                direccion,
                fecha_prog,
                estado_nuevo,
                evidencia,
                id_envio
            ))

            if estado_nuevo == estado_final:
                cursor.execute(
                    "UPDATE pedidos SET estado_pedido = 'Entregado' WHERE id_pedido = %s",
                    (actual['id_pedido'],)
                )

            conn.commit()
            return jsonify({
                'success': True,
                'mensaje': f'Envío #{id_envio} actualizado a "{estado_nuevo}".'
            }), 200
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] ACTUALIZAR ENVIO: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/logistica/<int:id_envio>', methods=['DELETE'])
    def eliminar_envio(id_envio):
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id_envio FROM logistica_instalacion WHERE id_envio = %s", (id_envio,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'mensaje': 'Envío no encontrado.'}), 404

            cursor.execute("DELETE FROM logistica_instalacion WHERE id_envio = %s", (id_envio,))
            conn.commit()
            return jsonify({
                'success': True,
                'mensaje': f'Envío #{id_envio} eliminado correctamente.'
            }), 200
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] ELIMINAR ENVIO: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    # =====================================================================
    # MÓDULO 3: RESEÑAS Y ENCUESTAS DE SATISFACCIÓN
    # =====================================================================

    @carlos_bp.route('/api/resenas', methods=['GET'])
    def listar_resenas():
        """Lista todos los muebles de pedidos aprobados con su calificación y comentario."""
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
                       d.fase_kanban,
                       d.calificacion_cliente,
                       d.comentario_resena,
                       d.fecha_actualizacion,
                       p.estado_pedido,
                       p.fecha_pedido,
                       c.nombre AS cliente_nombre,
                       c.email AS cliente_email,
                       c.telefono AS cliente_telefono,
                       pr.nombre AS producto_nombre,
                       pr.categoria AS producto_categoria,
                       op.nombre AS operario_nombre
                FROM detalle_orden_produccion d
                INNER JOIN pedidos p ON d.id_pedido = p.id_pedido
                INNER JOIN usuarios c ON p.id_cliente = c.id_usuario
                INNER JOIN productos pr ON d.id_producto = pr.id_producto
                LEFT JOIN usuarios op ON d.id_operario_asignado = op.id_usuario
                WHERE p.estado_pedido != 'Cotizacion'
                ORDER BY d.id_pedido DESC, d.id_detalle DESC
            """)
            filas = cursor.fetchall()

            lista = []
            for f in filas:
                calif = int(f['calificacion_cliente']) if f['calificacion_cliente'] is not None else None
                lista.append({
                    'id_detalle': f['id_detalle'],
                    'id_pedido': f['id_pedido'],
                    'id_producto': f['id_producto'],
                    'producto_nombre': f['producto_nombre'],
                    'producto_categoria': f['producto_categoria'] or 'General',
                    'cantidad': int(f['cantidad']),
                    'subtotal': float(f['subtotal']),
                    'fase_kanban': f['fase_kanban'],
                    'estado_pedido': f['estado_pedido'],
                    'cliente_nombre': f['cliente_nombre'],
                    'cliente_email': f['cliente_email'],
                    'cliente_telefono': f['cliente_telefono'] or 'Sin teléfono',
                    'operario_nombre': f['operario_nombre'] or 'Sin asignar',
                    'calificacion_cliente': calif,
                    'comentario_resena': f['comentario_resena'] or '',
                    'fecha_actualizacion': str(f['fecha_actualizacion'])[:16] if f['fecha_actualizacion'] else ''
                })

            evaluadas = [x for x in lista if x['calificacion_cliente'] is not None]
            pendientes = [x for x in lista if x['calificacion_cliente'] is None]
            total_evaluadas = len(evaluadas)

            promedio = round(
                sum(x['calificacion_cliente'] for x in evaluadas) / total_evaluadas, 1
            ) if total_evaluadas > 0 else 0.0

            positivas = sum(1 for x in evaluadas if x['calificacion_cliente'] >= 4)
            tasa_satisfaccion = round(
                (positivas / total_evaluadas) * 100, 1
            ) if total_evaluadas > 0 else 0.0

            resumen = {
                'promedio_calificacion': promedio,
                'total_resenas': total_evaluadas,
                'pendientes_evaluar': len(pendientes),
                'tasa_satisfaccion': tasa_satisfaccion
            }

            return jsonify({
                'success': True,
                'resenas': lista,
                'resumen': resumen
            }), 200
        except Exception as e:
            print(f"[ERROR] LISTAR RESENAS: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/resenas/<int:id_detalle>', methods=['PUT'])
    def guardar_resena(id_detalle):
        """Registra o actualiza la calificación (1-5) y el comentario del cliente."""
        data = request.get_json(silent=True) or {}
        calificacion = data.get('calificacion_cliente')
        comentario = (data.get('comentario_resena') or '').strip()

        try:
            calificacion_int = int(calificacion)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'mensaje': 'Selecciona una calificación entre 1 y 5 estrellas.'}), 400

        if calificacion_int < 1 or calificacion_int > 5:
            return jsonify({'success': False, 'mensaje': 'La calificación debe estar entre 1 y 5 estrellas.'}), 400

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id_detalle FROM detalle_orden_produccion WHERE id_detalle = %s", (id_detalle,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'mensaje': 'Registro de mueble no encontrado.'}), 404

            cursor.execute("""
                UPDATE detalle_orden_produccion
                SET calificacion_cliente = %s,
                    comentario_resena = %s
                WHERE id_detalle = %s
            """, (calificacion_int, comentario or None, id_detalle))
            conn.commit()

            return jsonify({
                'success': True,
                'mensaje': f'Reseña guardada con {calificacion_int} estrella(s) correctamente.'
            }), 200
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] GUARDAR RESENA: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    @carlos_bp.route('/api/resenas/<int:id_detalle>', methods=['DELETE'])
    def limpiar_resena(id_detalle):
        """Elimina únicamente la calificación y comentario sin borrar la orden de producción."""
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id_detalle FROM detalle_orden_produccion WHERE id_detalle = %s", (id_detalle,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'mensaje': 'Registro no encontrado.'}), 404

            cursor.execute("""
                UPDATE detalle_orden_produccion
                SET calificacion_cliente = NULL,
                    comentario_resena = NULL
                WHERE id_detalle = %s
            """, (id_detalle,))
            conn.commit()

            return jsonify({
                'success': True,
                'mensaje': 'Reseña eliminada; el registro volvió a quedar pendiente de evaluación.'
            }), 200
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] LIMPIAR RESENA: {e}")
            return jsonify({'success': False, 'mensaje': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    return carlos_bp
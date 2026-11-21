from flask import Blueprint, request, jsonify


def crear_blueprint_ecommerce(conectar_db, numero, fases_kanban):
    ecommerce_bp = Blueprint('ecommerce', __name__)

    @ecommerce_bp.route('/api/ecommerce/productos', methods=['GET'])
    def obtener_productos_ecommerce():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.id_producto, p.nombre, p.descripcion, p.categoria,
                       p.precio_venta, p.tiempo_estimado_horas, p.requiere_instalacion,
                       p.imagen_url, p.activo,
                       COALESCE(r.calificacion_promedio, 0) AS calificacion_promedio,
                       COALESCE(r.total_resenas, 0) AS total_resenas
                FROM productos p
                LEFT JOIN (
                    SELECT id_producto,
                           ROUND(AVG(calificacion_cliente), 1) AS calificacion_promedio,
                           COUNT(calificacion_cliente) AS total_resenas
                    FROM detalle_orden_produccion
                    WHERE calificacion_cliente IS NOT NULL
                    GROUP BY id_producto
                ) r ON r.id_producto = p.id_producto
                WHERE p.activo = 1
                ORDER BY p.categoria ASC, p.nombre ASC
            """)
            filas = cursor.fetchall()

            productos = [{
                'id_producto': fila['id_producto'],
                'nombre': fila['nombre'],
                'descripcion': fila['descripcion'],
                'categoria': fila['categoria'],
                'precio_venta': numero(fila['precio_venta']),
                'tiempo_estimado_horas': fila['tiempo_estimado_horas'],
                'requiere_instalacion': bool(fila['requiere_instalacion']),
                'imagen_url': fila['imagen_url'],
                'calificacion_promedio': numero(fila['calificacion_promedio']),
                'total_resenas': int(fila['total_resenas'] or 0)
            } for fila in filas]

            return jsonify({'success': True, 'productos': productos, 'total': len(productos)}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @ecommerce_bp.route('/api/ecommerce/cliente/<int:id_cliente>', methods=['GET'])
    def obtener_cliente_ecommerce(id_cliente):
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id_usuario AS id_cliente, nombre, email, telefono, direccion
                FROM usuarios
                WHERE id_usuario = %s AND activo = 1
            """, (id_cliente,))
            cliente = cursor.fetchone()

            if not cliente:
                return jsonify({'success': False, 'message': 'Cliente no encontrado'}), 404

            return jsonify({'success': True, 'cliente': cliente}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @ecommerce_bp.route('/api/ecommerce/checkout', methods=['POST'])
    def checkout_ecommerce():
        data = request.get_json(silent=True) or {}
        try:
            id_cliente = int(data.get('id_cliente'))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'El cliente es obligatorio para completar el pedido'}), 400

        direccion = (data.get('direccion') or '').strip()
        items = data.get('items') or []
        if not isinstance(items, list) or not items:
            return jsonify({'success': False, 'message': 'El carrito está vacío'}), 400

        cantidades = {}
        for item in items:
            try:
                id_producto = int(item.get('id_producto'))
                cantidad = int(item.get('cantidad'))
            except (TypeError, ValueError):
                return jsonify({'success': False, 'message': 'Los productos y cantidades del carrito no son válidos'}), 400
            if cantidad <= 0:
                return jsonify({'success': False, 'message': 'Las cantidades deben ser mayores a cero'}), 400
            cantidades[id_producto] = cantidades.get(id_producto, 0) + cantidad

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id_usuario, nombre FROM usuarios WHERE id_usuario = %s AND activo = 1", (id_cliente,))
            cliente = cursor.fetchone()
            if not cliente:
                return jsonify({'success': False, 'message': 'El cliente no existe o está inactivo'}), 404

            placeholders = ', '.join(['%s'] * len(cantidades))
            cursor.execute(f"""
                SELECT id_producto, nombre, precio_venta
                FROM productos
                WHERE activo = 1 AND id_producto IN ({placeholders})
            """, tuple(cantidades.keys()))
            productos = {fila['id_producto']: fila for fila in cursor.fetchall()}

            if len(productos) != len(cantidades):
                return jsonify({'success': False, 'message': 'Uno o más productos ya no están disponibles'}), 400

            if direccion:
                cursor.execute("UPDATE usuarios SET direccion = %s WHERE id_usuario = %s", (direccion, id_cliente))

            detalle = []
            total = 0.0
            for id_producto, cantidad in cantidades.items():
                producto = productos[id_producto]
                precio = numero(producto['precio_venta'])
                subtotal = round(precio * cantidad, 2)
                total += subtotal
                detalle.append({
                    'id_producto': id_producto,
                    'nombre': producto['nombre'],
                    'cantidad': cantidad,
                    'precio_venta': precio,
                    'subtotal': subtotal
                })
            total = round(total, 2)

            cursor.execute("""
                INSERT INTO pedidos (id_cliente, id_vendedor, total, estado_pedido, fecha_pedido)
                VALUES (%s, NULL, %s, 'Pagado', NOW())
            """, (id_cliente, total))
            id_pedido = cursor.lastrowid

            for linea in detalle:
                cursor.execute("""
                    INSERT INTO detalle_orden_produccion
                        (id_pedido, id_producto, cantidad, subtotal, id_operario_asignado,
                         fase_kanban, horas_invertidas)
                    VALUES (%s, %s, %s, %s, NULL, 'Pendiente', 0.00)
                """, (id_pedido, linea['id_producto'], linea['cantidad'], linea['subtotal']))

            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Pedido confirmado correctamente',
                'pedido': {
                    'id_pedido': id_pedido,
                    'id_cliente': id_cliente,
                    'cliente': cliente['nombre'],
                    'total': total,
                    'estado_pedido': 'Pagado',
                    'direccion': direccion or None,
                    'items': detalle
                }
            }), 201
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @ecommerce_bp.route('/api/ecommerce/mis-pedidos/<int:id_cliente>', methods=['GET'])
    def obtener_pedidos_cliente(id_cliente):
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.id_pedido, p.total, p.estado_pedido, p.fecha_pedido,
                       d.id_detalle, d.cantidad, d.subtotal, d.fase_kanban,
                       d.horas_invertidas, d.calificacion_cliente, d.comentario_resena,
                       pr.nombre AS producto, pr.categoria, pr.imagen_url
                FROM pedidos p
                INNER JOIN detalle_orden_produccion d ON d.id_pedido = p.id_pedido
                INNER JOIN productos pr ON pr.id_producto = d.id_producto
                WHERE p.id_cliente = %s
                ORDER BY p.fecha_pedido DESC, p.id_pedido DESC, d.id_detalle ASC
            """, (id_cliente,))
            filas = cursor.fetchall()

            pedidos = {}
            orden = []
            for fila in filas:
                id_pedido = fila['id_pedido']
                if id_pedido not in pedidos:
                    pedidos[id_pedido] = {
                        'id_pedido': id_pedido,
                        'total': numero(fila['total']),
                        'estado_pedido': fila['estado_pedido'],
                        'fecha_pedido': fila['fecha_pedido'].isoformat(sep=' ') if fila['fecha_pedido'] else None,
                        'items': []
                    }
                    orden.append(id_pedido)

                fase = fila['fase_kanban'] or 'Pendiente'
                try:
                    fase_indice = fases_kanban.index(fase)
                except ValueError:
                    fase_indice = 0

                pedidos[id_pedido]['items'].append({
                    'id_detalle': fila['id_detalle'],
                    'producto': fila['producto'],
                    'categoria': fila['categoria'],
                    'imagen_url': fila['imagen_url'],
                    'cantidad': fila['cantidad'],
                    'subtotal': numero(fila['subtotal']),
                    'fase_kanban': fase,
                    'fase_indice': fase_indice,
                    'progreso_porcentaje': round((fase_indice / (len(fases_kanban) - 1)) * 100),
                    'horas_invertidas': numero(fila['horas_invertidas']),
                    'calificacion_cliente': fila['calificacion_cliente'],
                    'comentario_resena': fila['comentario_resena'],
                    'puede_resenar': fase == 'Terminado'
                })

            for id_pedido in orden:
                items = pedidos[id_pedido]['items']
                fase_general_indice = min(item['fase_indice'] for item in items)
                pedidos[id_pedido]['fase_general'] = fases_kanban[fase_general_indice]
                pedidos[id_pedido]['fase_general_indice'] = fase_general_indice
                pedidos[id_pedido]['progreso_general'] = round((fase_general_indice / (len(fases_kanban) - 1)) * 100)
                pedidos[id_pedido]['total_articulos'] = sum(item['cantidad'] for item in items)

            return jsonify({
                'success': True,
                'pedidos': [pedidos[id_pedido] for id_pedido in orden],
                'fases': fases_kanban
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @ecommerce_bp.route('/api/ecommerce/resena/<int:id_detalle>', methods=['PUT'])
    def registrar_resena(id_detalle):
        data = request.get_json(silent=True) or {}
        try:
            calificacion = int(data.get('calificacion'))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'La calificación debe ser un número entero'}), 400

        if calificacion < 1 or calificacion > 5:
            return jsonify({'success': False, 'message': 'La calificación debe estar entre 1 y 5 estrellas'}), 400

        comentario = (data.get('comentario') or data.get('comentario_resena') or data.get('resena') or '').strip()

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id_detalle FROM detalle_orden_produccion WHERE id_detalle = %s", (id_detalle,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'Detalle de pedido no encontrado'}), 404

            cursor.execute("""
                UPDATE detalle_orden_produccion
                SET calificacion_cliente = %s, comentario_resena = %s
                WHERE id_detalle = %s
            """, (calificacion, comentario or None, id_detalle))
            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Reseña registrada correctamente',
                'resena': {'id_detalle': id_detalle, 'calificacion': calificacion, 'comentario': comentario or None}
            }), 200
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    return ecommerce_bp
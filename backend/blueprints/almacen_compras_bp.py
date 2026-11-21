from flask import Blueprint, request, jsonify
import mysql.connector


def crear_blueprint_almacen_compras(conectar_db, numero, estados_compra):
    almacen_bp = Blueprint('almacen_compras', __name__)

    @almacen_bp.route('/api/almacen/materiales', methods=['GET'])
    def obtener_materiales_almacen():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT m.id_material,
                       m.nombre,
                       m.unidad_medida,
                       m.stock_actual,
                       m.stock_minimo,
                       m.costo_unitario,
                       COALESCE(comprometido.cantidad_comprometida, 0) AS stock_comprometido
                FROM materia_prima m
                LEFT JOIN (
                    SELECT r.id_material,
                           SUM(r.cantidad_necesaria * d.cantidad) AS cantidad_comprometida
                    FROM detalle_orden_produccion d
                    INNER JOIN receta_proceso_producto r ON r.id_producto = d.id_producto
                    WHERE d.fase_kanban = 'Pendiente'
                    GROUP BY r.id_material
                ) comprometido ON comprometido.id_material = m.id_material
                ORDER BY m.nombre ASC
            """)
            filas = cursor.fetchall()

            materiales = []
            for fila in filas:
                stock_actual = numero(fila['stock_actual'])
                stock_minimo = numero(fila['stock_minimo'])
                costo_unitario = numero(fila['costo_unitario'])
                stock_comprometido = numero(fila['stock_comprometido'])
                stock_disponible = stock_actual - stock_comprometido

                materiales.append({
                    'id_material': fila['id_material'],
                    'nombre': fila['nombre'],
                    'unidad_medida': fila['unidad_medida'],
                    'stock_actual': round(stock_actual, 2),
                    'stock_minimo': round(stock_minimo, 2),
                    'costo_unitario': round(costo_unitario, 2),
                    'stock_comprometido': round(stock_comprometido, 2),
                    'stock_disponible': round(stock_disponible, 2),
                    'valor_inventario': round(stock_actual * costo_unitario, 2),
                    'alerta_stock_bajo': stock_actual <= stock_minimo,
                    'requiere_reorden': stock_disponible < stock_minimo,
                    'porcentaje_vs_minimo': round((stock_actual / stock_minimo) * 100, 1) if stock_minimo > 0 else 100.0
                })

            resumen = {
                'total_materiales': len(materiales),
                'unidades_totales': round(sum(m['stock_actual'] for m in materiales), 2),
                'valor_inventario': round(sum(m['valor_inventario'] for m in materiales), 2),
                'alertas_stock_bajo': sum(1 for m in materiales if m['alerta_stock_bajo']),
                'requieren_reorden': sum(1 for m in materiales if m['requiere_reorden']),
                'comprometido_total': round(sum(m['stock_comprometido'] for m in materiales), 2)
            }

            return jsonify({'success': True, 'materiales': materiales, 'resumen': resumen}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @almacen_bp.route('/api/almacen/materiales', methods=['POST'])
    def registrar_material_almacen():
        data = request.get_json(silent=True) or {}
        nombre = (data.get('nombre') or '').strip()
        unidad_medida = (data.get('unidad_medida') or '').strip()

        if not nombre or not unidad_medida:
            return jsonify({'success': False, 'message': 'El nombre y la unidad de medida son obligatorios'}), 400

        try:
            stock_actual = float(data.get('stock_actual', 0) or 0)
            stock_minimo = float(data.get('stock_minimo', 5) or 0)
            costo_unitario = float(data.get('costo_unitario', 0) or 0)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Los valores de stock y costo deben ser numéricos'}), 400

        if stock_actual < 0 or stock_minimo < 0 or costo_unitario < 0:
            return jsonify({'success': False, 'message': 'El stock y el costo no pueden ser negativos'}), 400

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO materia_prima (nombre, unidad_medida, stock_actual, stock_minimo, costo_unitario)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre, unidad_medida, stock_actual, stock_minimo, costo_unitario))
            conn.commit()
            return jsonify({'success': True, 'message': 'Insumo registrado correctamente', 'id_material': cursor.lastrowid}), 201
        except mysql.connector.Error as err:
            if conn: conn.rollback()
            return jsonify({'success': False, 'message': str(err)}), 500
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @almacen_bp.route('/api/almacen/proveedores', methods=['GET'])
    def obtener_proveedores_almacen():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id_proveedor, nombre_empresa, contacto, telefono, categoria_insumo
                FROM proveedores
                ORDER BY nombre_empresa ASC
            """)
            proveedores = cursor.fetchall()
            return jsonify({'success': True, 'proveedores': proveedores, 'total': len(proveedores)}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @almacen_bp.route('/api/almacen/movimientos', methods=['GET'])
    def obtener_movimientos_almacen():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT c.id_compra, c.cantidad, c.costo_total, c.estado, c.fecha_compra,
                       m.nombre AS material, m.unidad_medida, p.nombre_empresa AS proveedor, u.nombre AS solicitante
                FROM compras_insumos c
                INNER JOIN materia_prima m ON m.id_material = c.id_material
                INNER JOIN proveedores p ON p.id_proveedor = c.id_proveedor
                INNER JOIN usuarios u ON u.id_usuario = c.id_usuario_solicita
                ORDER BY c.fecha_compra DESC, c.id_compra DESC
                LIMIT 20
            """)
            filas = cursor.fetchall()

            movimientos = [{
                'id_compra': fila['id_compra'],
                'material': fila['material'],
                'unidad_medida': fila['unidad_medida'],
                'cantidad': numero(fila['cantidad']),
                'costo_total': numero(fila['costo_total']),
                'estado': fila['estado'],
                'tipo': 'Entrada' if fila['estado'] == 'Recibido' else 'Solicitud',
                'proveedor': fila['proveedor'],
                'solicitante': fila['solicitante'],
                'fecha': fila['fecha_compra'].isoformat(sep=' ') if fila['fecha_compra'] else None
            } for fila in filas]

            return jsonify({'success': True, 'movimientos': movimientos}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @almacen_bp.route('/api/almacen/requisiciones', methods=['GET'])
    def obtener_requisiciones():
        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT c.id_compra, c.id_proveedor, c.id_material, c.id_usuario_solicita,
                       c.cantidad, c.costo_total, c.estado, c.fecha_compra,
                       p.nombre_empresa AS proveedor, p.contacto AS proveedor_contacto,
                       p.telefono AS proveedor_telefono, p.categoria_insumo,
                       m.nombre AS material, m.unidad_medida, m.costo_unitario AS costo_unitario_actual,
                       u.nombre AS solicitante,
                       ROUND(c.costo_total / NULLIF(c.cantidad, 0), 2) AS costo_unitario
                FROM compras_insumos c
                INNER JOIN proveedores p ON p.id_proveedor = c.id_proveedor
                INNER JOIN materia_prima m ON m.id_material = c.id_material
                INNER JOIN usuarios u ON u.id_usuario = c.id_usuario_solicita
                ORDER BY c.fecha_compra DESC, c.id_compra DESC
            """)
            filas = cursor.fetchall()

            requisiciones = [{
                'id_compra': fila['id_compra'],
                'id_proveedor': fila['id_proveedor'],
                'id_material': fila['id_material'],
                'id_usuario_solicita': fila['id_usuario_solicita'],
                'cantidad': numero(fila['cantidad']),
                'costo_total': numero(fila['costo_total']),
                'costo_unitario': numero(fila['costo_unitario']),
                'costo_unitario_actual': numero(fila['costo_unitario_actual']),
                'estado': fila['estado'],
                'fecha_compra': fila['fecha_compra'].isoformat(sep=' ') if fila['fecha_compra'] else None,
                'proveedor': fila['proveedor'],
                'proveedor_contacto': fila['proveedor_contacto'],
                'proveedor_telefono': fila['proveedor_telefono'],
                'categoria_insumo': fila['categoria_insumo'],
                'material': fila['material'],
                'unidad_medida': fila['unidad_medida'],
                'solicitante': fila['solicitante']
            } for fila in filas]

            pendientes = [r for r in requisiciones if r['estado'] in ('Solicitado', 'Aprobado')]
            resumen = {
                'total_requisiciones': len(requisiciones),
                'presupuesto_pendiente': round(sum(r['costo_total'] for r in pendientes), 2),
                'requisiciones_pendientes': len(pendientes),
                'por_aprobar': sum(1 for r in requisiciones if r['estado'] == 'Solicitado'),
                'recibidas': sum(1 for r in requisiciones if r['estado'] == 'Recibido')
            }

            return jsonify({'success': True, 'requisiciones': requisiciones, 'resumen': resumen}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @almacen_bp.route('/api/almacen/requisiciones', methods=['POST'])
    def crear_requisicion():
        data = request.get_json(silent=True) or {}
        try:
            id_proveedor = int(data.get('id_proveedor'))
            id_material = int(data.get('id_material'))
            id_usuario_solicita = int(data.get('id_usuario_solicita'))
            cantidad = float(data.get('cantidad'))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Proveedor, material, solicitante y cantidad son obligatorios'}), 400

        if cantidad <= 0:
            return jsonify({'success': False, 'message': 'La cantidad debe ser mayor a cero'}), 400

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id_proveedor FROM proveedores WHERE id_proveedor = %s", (id_proveedor,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'El proveedor seleccionado no existe'}), 404

            cursor.execute("SELECT id_material, costo_unitario FROM materia_prima WHERE id_material = %s", (id_material,))
            material = cursor.fetchone()
            if not material:
                return jsonify({'success': False, 'message': 'El material seleccionado no existe'}), 404

            cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (id_usuario_solicita,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'El usuario solicitante no existe'}), 404

            costo_unitario = data.get('costo_unitario')
            if costo_unitario is None or costo_unitario == '':
                costo_unitario = material['costo_unitario']
            costo_unitario = float(costo_unitario)
            if costo_unitario < 0:
                return jsonify({'success': False, 'message': 'El costo unitario no puede ser negativo'}), 400

            costo_total = round(cantidad * costo_unitario, 2)

            cursor.execute("""
                INSERT INTO compras_insumos
                    (id_proveedor, id_material, id_usuario_solicita, cantidad, costo_total, estado, fecha_compra)
                VALUES (%s, %s, %s, %s, %s, 'Solicitado', NOW())
            """, (id_proveedor, id_material, id_usuario_solicita, cantidad, costo_total))
            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Requisición creada correctamente',
                'id_compra': cursor.lastrowid,
                'costo_total': costo_total,
                'estado': 'Solicitado'
            }), 201
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    @almacen_bp.route('/api/almacen/requisiciones/<int:id_compra>/estado', methods=['PUT'])
    def actualizar_estado_requisicion(id_compra):
        data = request.get_json(silent=True) or {}
        nuevo_estado = (data.get('estado') or '').strip()

        if nuevo_estado not in estados_compra:
            return jsonify({'success': False, 'message': f"Estado inválido. Usa uno de: {', '.join(estados_compra)}"}), 400

        conn = None
        cursor = None
        try:
            conn = conectar_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id_compra, id_material, cantidad, estado
                FROM compras_insumos
                WHERE id_compra = %s
                FOR UPDATE
            """, (id_compra,))
            requisicion = cursor.fetchone()

            if not requisicion:
                conn.rollback()
                return jsonify({'success': False, 'message': 'Requisición no encontrada'}), 404

            estado_anterior = requisicion['estado']
            stock_nuevo = None

            if nuevo_estado == 'Recibido' and estado_anterior != 'Recibido':
                cursor.execute("""
                    UPDATE materia_prima
                    SET stock_actual = stock_actual + %s
                    WHERE id_material = %s
                """, (requisicion['cantidad'], requisicion['id_material']))

                cursor.execute("SELECT stock_actual FROM materia_prima WHERE id_material = %s", (requisicion['id_material'],))
                fila_stock = cursor.fetchone()
                stock_nuevo = numero(fila_stock['stock_actual']) if fila_stock else None

            cursor.execute("UPDATE compras_insumos SET estado = %s WHERE id_compra = %s", (nuevo_estado, id_compra))
            conn.commit()

            return jsonify({
                'success': True,
                'message': f'Requisición actualizada a {nuevo_estado}',
                'id_compra': id_compra,
                'estado_anterior': estado_anterior,
                'estado': nuevo_estado,
                'stock_actualizado': nuevo_estado == 'Recibido' and estado_anterior != 'Recibido',
                'stock_nuevo': stock_nuevo
            }), 200
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    return almacen_bp
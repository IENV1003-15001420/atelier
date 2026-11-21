from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from decimal import Decimal
from flask.json.provider import DefaultJSONProvider


class AtelierJSONProvider(DefaultJSONProvider):
    """Convierte los decimales de MySQL a nÃºmeros JSON sin romper las rutas existentes."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


app = Flask(__name__)
app.json = AtelierJSONProvider(app)
CORS(app)  # Permite peticiones desde el frontend en Angular

# ConfiguraciÃ³n de base de datos MySQL.
# Se respeta la configuraciÃ³n original del proyecto (liz/root) y, si no existe en el
# equipo local, se prueba el acceso habitual de Laragon/XAMPP (root sin contraseÃ±a).
# TambiÃ©n puede fijarse explícitamente con ATELIER_DB_USER / ATELIER_DB_PASSWORD.
def detectar_db_config():
    host = os.getenv('ATELIER_DB_HOST', 'localhost')
    database = os.getenv('ATELIER_DB_NAME', 'atelier_db')
    usuario_env = os.getenv('ATELIER_DB_USER')

    if usuario_env:
        candidatos = [{
            'host': host,
            'user': usuario_env,
            'password': os.getenv('ATELIER_DB_PASSWORD', ''),
            'database': database,
            'use_pure': True
        }]
    else:
      candidatos = [
    {'host': host, 'user': 'liz', 'password': os.getenv('ATELIER_DB_PASSWORD', 'root'), 'database': database, 'use_pure': True},
    {'host': host, 'user': 'root', 'password': '', 'database': database, 'use_pure': True},
    {'host': '127.0.0.1', 'port': 8889, 'user': 'root', 'password': 'root', 'database': database, 'use_pure': True}
]

    for candidato in candidatos:
        try:
            prueba = mysql.connector.connect(**candidato, connection_timeout=3)
            prueba.close()
            print(f"[OK] MySQL conectado: {candidato['user']}@{candidato['host']}/{database}")
            return candidato
        except Exception:
            continue

    return candidatos[0]


db_config = detectar_db_config()

FASES_KANBAN = ['Pendiente', 'Corte y Armado', 'Barnizado y Secado', 'Control Calidad', 'Terminado']
ESTADOS_COMPRA = ['Solicitado', 'Aprobado', 'Recibido', 'Cancelado']


def conectar_db():
    return mysql.connector.connect(**db_config)


def numero(valor, default=0.0):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    print(f"[LOGIN] INTENTANDO LOGIN | Email recibido: '{email}' | Password recibido: '{password}'")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT u.id_usuario, u.nombre, u.email, u.id_rol, r.nombre_rol 
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            WHERE u.email = %s AND u.password_hash = %s AND u.activo = 1
        """
        cursor.execute(query, (email, password))
        usuario = cursor.fetchone()

        if usuario:
            return jsonify({'success': True, 'usuario': usuario}), 200
        else:
            return jsonify({'success': False, 'message': 'Credenciales invÃ¡lidas o usuario inactivo'}), 401

    except Exception as e:
        print(f"[ERROR] ERROR DE MYSQL: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT SUM(total) AS ventas_mes 
            FROM pedidos 
            WHERE MONTH(fecha_pedido) = MONTH(CURRENT_DATE()) 
            AND YEAR(fecha_pedido) = YEAR(CURRENT_DATE())
        """)
        venta_mes = cursor.fetchone()
        total_ventas = venta_mes['ventas_mes'] if venta_mes['ventas_mes'] else 0

        cursor.execute("SELECT COUNT(*) AS activos FROM pedidos WHERE estado_pedido = 'En Produccion'")
        proyectos = cursor.fetchone()
        total_proyectos = proyectos['activos'] if proyectos else 0

        meses = ['Nov', 'Dic', 'Ene', 'Feb', 'Mar', 'Abr']
        ventas_grafica = [15000, 17500, 16000, 19000, 18000, float(total_ventas)]
        gastos_grafica = [8000, 9000, 8500, 9500, 8800, 9200]

        return jsonify({
            'success': True,
            'ventas_mes': total_ventas,
            'proyectos_activos': total_proyectos,
            'alertas_stock': 3,
            'grafica': {
                'meses': meses,
                'ventas': ventas_grafica,
                'gastos': gastos_grafica
            }
        })

    except Exception as e:
        print(f"[ERROR] ERROR EN DASHBOARD: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT u.id_usuario, u.nombre, u.email, u.telefono, u.direccion, u.activo, u.fecha_registro, r.nombre_rol 
            FROM usuarios u
            LEFT JOIN roles r ON u.id_rol = r.id_rol
            ORDER BY u.id_usuario ASC
        """
        cursor.execute(sql)
        datos = cursor.fetchall()
        
        lista_usuarios = []
        colores = ['bg-[#6b1d24]', 'bg-[#5c4938]', 'bg-[#d8e8f8]', 'bg-gray-200', 'bg-[#e2b887]', 'bg-[#f0b4b8]']
        
        for index, fila in enumerate(datos):
            nombre = fila['nombre'] or 'Sin Nombre'
            partes = nombre.split()
            iniciales = (partes[0][0] + (partes[1][0] if len(partes) > 1 else '')).upper()
            
            color_bg = colores[index % len(colores)]
            color_texto = 'text-white' if color_bg in ['bg-[#6b1d24]', 'bg-[#5c4938]'] else 'text-gray-800'
            
            es_activo = (fila['activo'] == 1)
            estado_texto = 'ACTIVO' if es_activo else 'OFFLINE'

            lista_usuarios.append({
                'id': fila['id_usuario'],
                'iniciales': iniciales,
                'colorBg': color_bg,
                'colorTexto': color_texto,
                'nombre': nombre,
                'correo': fila['email'],
                'rolPrincipal': (fila['nombre_rol'] or 'PERSONAL').upper(),
                'rolSecundario': f"ID Empleado #{fila['id_usuario']}",
                'estacion': fila['direccion'] or 'Taller Central',
                'estacionSub': 'Sede LeÃ³n, Gto.',
                'acceso': f"Tel: {fila['telefono']}" if fila['telefono'] else 'Sin telÃ©fono',
                'accesoSub': f"Reg: {str(fila['fecha_registro'])[:10]}",
                'estado': estado_texto,
                'colorEstado': 'text-emerald-500' if es_activo else 'text-gray-400'
            })
            
        return jsonify({'success': True, 'usuarios': lista_usuarios})
    except Exception as e:
        print(f"[ERROR] ERROR EN USUARIOS: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

@app.route('/api/usuarios', methods=['POST'])
def crear_usuario():
    data = request.get_json()
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        sql = """
            INSERT INTO usuarios (nombre, email, password_hash, telefono, direccion, id_rol, activo, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, 1, NOW())
        """
        valores = (
            data.get('nombre'),
            data.get('email'),
            data.get('password', '123456'),
            data.get('telefono'),
            data.get('direccion'),
            data.get('id_rol')
        )
        cursor.execute(sql, valores)
        conn.commit()
        
        return jsonify({'success': True, 'mensaje': 'Usuario registrado correctamente'}), 201
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return jsonify({'success': False, 'mensaje': 'Ese correo electrÃ³nico ya estÃ¡ registrado en el sistema.'}), 400
        return jsonify({'success': False, 'mensaje': str(err)}), 500
    except Exception as e:
        print(f"[ERROR] ERROR AL CREAR USUARIO: {e}")
        return jsonify({'success': False, 'mensaje': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

# =====================================================================
# MÃ“DULO 1: ALMACÃ‰N E INVENTARIOS
# =====================================================================

@app.route('/api/almacen/materiales', methods=['GET'])
def obtener_materiales_almacen():
    """Lista la materia prima, calcula el stock comprometido en OT pendientes y las alertas."""
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
        print(f"[ERROR] ERROR EN ALMACÃ‰N/MATERIALES: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/almacen/materiales', methods=['POST'])
def registrar_material_almacen():
    """Registra un nuevo insumo de materia prima."""
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
        return jsonify({'success': False, 'message': 'Los valores de stock y costo deben ser numÃ©ricos'}), 400

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

        return jsonify({
            'success': True,
            'message': 'Insumo registrado correctamente',
            'id_material': cursor.lastrowid
        }), 201

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        print(f"[ERROR] ERROR AL REGISTRAR MATERIAL: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/almacen/proveedores', methods=['GET'])
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
        print(f"[ERROR] ERROR EN PROVEEDORES: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/almacen/movimientos', methods=['GET'])
def obtener_movimientos_almacen():
    """Kardex simplificado: entradas y requisiciones recientes de compras_insumos."""
    conn = None
    cursor = None
    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id_compra,
                   c.cantidad,
                   c.costo_total,
                   c.estado,
                   c.fecha_compra,
                   m.nombre AS material,
                   m.unidad_medida,
                   p.nombre_empresa AS proveedor,
                   u.nombre AS solicitante
            FROM compras_insumos c
            INNER JOIN materia_prima m ON m.id_material = c.id_material
            INNER JOIN proveedores p ON p.id_proveedor = c.id_proveedor
            INNER JOIN usuarios u ON u.id_usuario = c.id_usuario_solicita
            ORDER BY c.fecha_compra DESC, c.id_compra DESC
            LIMIT 20
        """)
        filas = cursor.fetchall()

        movimientos = []
        for fila in filas:
            movimientos.append({
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
            })

        return jsonify({'success': True, 'movimientos': movimientos}), 200
    except Exception as e:
        print(f"[ERROR] ERROR EN MOVIMIENTOS: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# =====================================================================
# MÃ“DULO 2: COMPRAS / REQUISICIONES
# =====================================================================

@app.route('/api/almacen/requisiciones', methods=['GET'])
def obtener_requisiciones():
    conn = None
    cursor = None
    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id_compra,
                   c.id_proveedor,
                   c.id_material,
                   c.id_usuario_solicita,
                   c.cantidad,
                   c.costo_total,
                   c.estado,
                   c.fecha_compra,
                   p.nombre_empresa AS proveedor,
                   p.contacto AS proveedor_contacto,
                   p.telefono AS proveedor_telefono,
                   p.categoria_insumo,
                   m.nombre AS material,
                   m.unidad_medida,
                   m.costo_unitario AS costo_unitario_actual,
                   u.nombre AS solicitante,
                   ROUND(c.costo_total / NULLIF(c.cantidad, 0), 2) AS costo_unitario
            FROM compras_insumos c
            INNER JOIN proveedores p ON p.id_proveedor = c.id_proveedor
            INNER JOIN materia_prima m ON m.id_material = c.id_material
            INNER JOIN usuarios u ON u.id_usuario = c.id_usuario_solicita
            ORDER BY c.fecha_compra DESC, c.id_compra DESC
        """)
        filas = cursor.fetchall()

        requisiciones = []
        for fila in filas:
            requisiciones.append({
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
            })

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
        print(f"[ERROR] ERROR EN REQUISICIONES: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/almacen/requisiciones', methods=['POST'])
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
            'message': 'RequisiciÃ³n creada correctamente',
            'id_compra': cursor.lastrowid,
            'costo_total': costo_total,
            'estado': 'Solicitado'
        }), 201

    except Exception as e:
        if conn: conn.rollback()
        print(f"[ERROR] ERROR AL CREAR REQUISICIÃ“N: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/almacen/requisiciones/<int:id_compra>/estado', methods=['PUT'])
def actualizar_estado_requisicion(id_compra):
    data = request.get_json(silent=True) or {}
    nuevo_estado = (data.get('estado') or '').strip()

    if nuevo_estado not in ESTADOS_COMPRA:
        return jsonify({
            'success': False,
            'message': f"Estado invÃ¡lido. Usa uno de: {', '.join(ESTADOS_COMPRA)}"
        }), 400

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
            return jsonify({'success': False, 'message': 'RequisiciÃ³n no encontrada'}), 404

        estado_anterior = requisicion['estado']
        stock_nuevo = None

        # Regla de negocio: la primera vez que pasa a Recibido, la cantidad entra al inventario.
        if nuevo_estado == 'Recibido' and estado_anterior != 'Recibido':
            cursor.execute("""
                UPDATE materia_prima
                SET stock_actual = stock_actual + %s
                WHERE id_material = %s
            """, (requisicion['cantidad'], requisicion['id_material']))

            cursor.execute(
                "SELECT stock_actual FROM materia_prima WHERE id_material = %s",
                (requisicion['id_material'],)
            )
            fila_stock = cursor.fetchone()
            stock_nuevo = numero(fila_stock['stock_actual']) if fila_stock else None

        cursor.execute(
            "UPDATE compras_insumos SET estado = %s WHERE id_compra = %s",
            (nuevo_estado, id_compra)
        )
        conn.commit()

        return jsonify({
            'success': True,
            'message': f'RequisiciÃ³n actualizada a {nuevo_estado}',
            'id_compra': id_compra,
            'estado_anterior': estado_anterior,
            'estado': nuevo_estado,
            'stock_actualizado': nuevo_estado == 'Recibido' and estado_anterior != 'Recibido',
            'stock_nuevo': stock_nuevo
        }), 200

    except Exception as e:
        if conn: conn.rollback()
        print(f"[ERROR] ERROR AL ACTUALIZAR REQUISICIÃ“N: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# =====================================================================
# MÃ“DULO 3: E-COMMERCE PWA
# =====================================================================

@app.route('/api/ecommerce/productos', methods=['GET'])
def obtener_productos_ecommerce():
    conn = None
    cursor = None
    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id_producto,
                   p.nombre,
                   p.descripcion,
                   p.categoria,
                   p.precio_venta,
                   p.tiempo_estimado_horas,
                   p.requiere_instalacion,
                   p.imagen_url,
                   p.activo,
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

        productos = []
        for fila in filas:
            productos.append({
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
            })

        return jsonify({'success': True, 'productos': productos, 'total': len(productos)}), 200
    except Exception as e:
        print(f"[ERROR] ERROR EN CATÁLOGO: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/ecommerce/cliente/<int:id_cliente>', methods=['GET'])
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
        print(f"[ERROR] ERROR EN CLIENTE E-COMMERCE: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/ecommerce/checkout', methods=['POST'])
def checkout_ecommerce():
    data = request.get_json(silent=True) or {}

    try:
        id_cliente = int(data.get('id_cliente'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'El cliente es obligatorio para completar el pedido'}), 400

    direccion = (data.get('direccion') or '').strip()
    items = data.get('items') or []
    if not isinstance(items, list) or not items:
        return jsonify({'success': False, 'message': 'El carrito estÃ¡ vacÃ­o'}), 400

    # Normaliza y agrupa cantidades por producto.
    cantidades = {}
    for item in items:
        try:
            id_producto = int(item.get('id_producto'))
            cantidad = int(item.get('cantidad'))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Los productos y cantidades del carrito no son vÃ¡lidos'}), 400
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
            return jsonify({'success': False, 'message': 'El cliente no existe o estÃ¡ inactivo'}), 404

        placeholders = ', '.join(['%s'] * len(cantidades))
        cursor.execute(f"""
            SELECT id_producto, nombre, precio_venta
            FROM productos
            WHERE activo = 1 AND id_producto IN ({placeholders})
        """, tuple(cantidades.keys()))
        productos = {fila['id_producto']: fila for fila in cursor.fetchall()}

        if len(productos) != len(cantidades):
            return jsonify({'success': False, 'message': 'Uno o mÃ¡s productos ya no estÃ¡n disponibles'}), 400

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
        print(f"[ERROR] ERROR EN CHECKOUT: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/ecommerce/mis-pedidos/<int:id_cliente>', methods=['GET'])
def obtener_pedidos_cliente(id_cliente):
    conn = None
    cursor = None
    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id_pedido,
                   p.total,
                   p.estado_pedido,
                   p.fecha_pedido,
                   d.id_detalle,
                   d.cantidad,
                   d.subtotal,
                   d.fase_kanban,
                   d.horas_invertidas,
                   d.calificacion_cliente,
                   d.comentario_resena,
                   pr.nombre AS producto,
                   pr.categoria,
                   pr.imagen_url
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
                fase_indice = FASES_KANBAN.index(fase)
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
                'progreso_porcentaje': round((fase_indice / (len(FASES_KANBAN) - 1)) * 100),
                'horas_invertidas': numero(fila['horas_invertidas']),
                'calificacion_cliente': fila['calificacion_cliente'],
                'comentario_resena': fila['comentario_resena'],
                'puede_resenar': fase == 'Terminado'
            })

        for id_pedido in orden:
            items = pedidos[id_pedido]['items']
            fase_general_indice = min(item['fase_indice'] for item in items)
            pedidos[id_pedido]['fase_general'] = FASES_KANBAN[fase_general_indice]
            pedidos[id_pedido]['fase_general_indice'] = fase_general_indice
            pedidos[id_pedido]['progreso_general'] = round((fase_general_indice / (len(FASES_KANBAN) - 1)) * 100)
            pedidos[id_pedido]['total_articulos'] = sum(item['cantidad'] for item in items)

        return jsonify({
            'success': True,
            'pedidos': [pedidos[id_pedido] for id_pedido in orden],
            'fases': FASES_KANBAN
        }), 200
    except Exception as e:
        print(f"[ERROR] ERROR EN MIS PEDIDOS: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/ecommerce/resena/<int:id_detalle>', methods=['PUT'])
def registrar_resena(id_detalle):
    data = request.get_json(silent=True) or {}

    try:
        calificacion = int(data.get('calificacion'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'La calificaciÃ³n debe ser un nÃºmero entero'}), 400

    if calificacion < 1 or calificacion > 5:
        return jsonify({'success': False, 'message': 'La calificaciÃ³n debe estar entre 1 y 5 estrellas'}), 400

    comentario = (data.get('comentario') or data.get('comentario_resena') or data.get('resena') or '').strip()

    conn = None
    cursor = None
    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_detalle, id_pedido, id_producto, fase_kanban
            FROM detalle_orden_produccion
            WHERE id_detalle = %s
        """, (id_detalle,))
        detalle = cursor.fetchone()
        if not detalle:
            return jsonify({'success': False, 'message': 'Detalle de pedido no encontrado'}), 404

        cursor.execute("""
            UPDATE detalle_orden_produccion
            SET calificacion_cliente = %s, comentario_resena = %s
            WHERE id_detalle = %s
        """, (calificacion, comentario or None, id_detalle))
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'ReseÃ±a registrada correctamente',
            'resena': {
                'id_detalle': id_detalle,
                'calificacion': calificacion,
                'comentario': comentario or None
            }
        }), 200

    except Exception as e:
        if conn: conn.rollback()
        print(f"[ERROR] ERROR AL REGISTRAR RESEÃ‘A: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

from routes_carlos import crear_blueprint_carlos
app.register_blueprint(crear_blueprint_carlos(conectar_db))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

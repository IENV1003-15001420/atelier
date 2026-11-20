from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)  # Permite peticiones desde el frontend en Angular

# Configuración de base de datos MySQL
db_config = {
    'host': 'localhost',
    'user': 'liz',
    'password': 'root',
    'database': 'atelier_db'
}

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    print(f"➡️ INTENTANDO LOGIN | Email recibido: '{email}' | Password recibido: '{password}'")

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
            return jsonify({'success': False, 'message': 'Credenciales inválidas o usuario inactivo'}), 401

    except Exception as e:
        print(f"🔴 ERROR DE MYSQL: {e}") 
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
        print(f"🔴 ERROR EN DASHBOARD: {e}")
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
                'estacionSub': 'Sede León, Gto.',
                'acceso': f"Tel: {fila['telefono']}" if fila['telefono'] else 'Sin teléfono',
                'accesoSub': f"Reg: {str(fila['fecha_registro'])[:10]}",
                'estado': estado_texto,
                'colorEstado': 'text-emerald-500' if es_activo else 'text-gray-400'
            })
            
        return jsonify({'success': True, 'usuarios': lista_usuarios})
    except Exception as e:
        print(f"🔴 ERROR EN USUARIOS: {e}")
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
            return jsonify({'success': False, 'mensaje': 'Ese correo electrónico ya está registrado en el sistema.'}), 400
        return jsonify({'success': False, 'mensaje': str(err)}), 500
    except Exception as e:
        print(f"🔴 ERROR AL CREAR USUARIO: {e}")
        return jsonify({'success': False, 'mensaje': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
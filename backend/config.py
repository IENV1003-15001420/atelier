import os
from decimal import Decimal
import mysql.connector
from flask.json.provider import DefaultJSONProvider

FASES_KANBAN = ['Pendiente', 'Corte y Armado', 'Barnizado y Secado', 'Control Calidad', 'Terminado']
ESTADOS_COMPRA = ['Solicitado', 'Aprobado', 'Recibido', 'Cancelado']


class AtelierJSONProvider(DefaultJSONProvider):
    """Convierte los decimales de MySQL a números JSON."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


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


def conectar_db():
    return mysql.connector.connect(**db_config)


def numero(valor, default=0.0):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default
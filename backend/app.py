from flask import Flask
from flask_cors import CORS
from config import AtelierJSONProvider, conectar_db, numero, FASES_KANBAN, ESTADOS_COMPRA
from blueprints.auth_usuarios_bp import crear_blueprint_auth_usuarios
from blueprints.almacen_compras_bp import crear_blueprint_almacen_compras
from blueprints.ecommerce_bp import crear_blueprint_ecommerce
from blueprints.carlos_bp import crear_blueprint_carlos
from blueprints.romo_bp import crear_blueprint_romo

app = Flask(__name__)
app.json = AtelierJSONProvider(app)
CORS(app)

app.register_blueprint(crear_blueprint_auth_usuarios(conectar_db))
app.register_blueprint(crear_blueprint_almacen_compras(conectar_db, numero, ESTADOS_COMPRA))
app.register_blueprint(crear_blueprint_ecommerce(conectar_db, numero, FASES_KANBAN))
app.register_blueprint(crear_blueprint_carlos(conectar_db))
app.register_blueprint(crear_blueprint_romo(conectar_db))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
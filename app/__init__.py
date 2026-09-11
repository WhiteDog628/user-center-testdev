from flask import Flask

from config import Config
from app.extensions import db, jwt
from app.routes import api


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    app.register_blueprint(api)

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
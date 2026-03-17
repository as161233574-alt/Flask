from flask import Flask, jsonify
from flask_cors import CORS
from .config import config_map
from .extensions import db, jwt
from .models.user import TokenBlocklist


def create_app(env="development"):
    app = Flask(__name__)
    app.config.from_object(config_map[env])

    # 允许所有来源跨域（移动端 App / 小程序 / H5 均可调用）
    CORS(app, resources={r"/*": {"origins": "*"}},
         supports_credentials=True,
         expose_headers=["Authorization"])

    db.init_app(app)
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return db.session.query(
            TokenBlocklist.query.filter_by(jti=jti).exists()
        ).scalar()

    from .routes.auth import auth_bp
    from .routes.user import user_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/users")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app

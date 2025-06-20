import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from config import config
from app.cache import init_cache

db = SQLAlchemy()
login = LoginManager()
cache = Cache()
login.login_view = "auth.login"


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    print(f"Using config: {config_name}")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app)
    login.init_app(app)
    init_cache(app)

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    return app


from app import models  # noqa: F401, E402

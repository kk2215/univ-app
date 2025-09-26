# app/__init__.py (完全版)

from flask import Flask
from config import Config
from .extensions import db, migrate, login_manager, mail
from .models import User
from sqlalchemy.orm import selectinload

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 拡張機能をアプリに登録
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # ログインしていないユーザーがアクセスした場合のリダイレクト先
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'このページにアクセスするにはログインが必要です。'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).options(
            selectinload(User.subjects)
        ).get(int(user_id))

    # ブループリントの登録
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    return app
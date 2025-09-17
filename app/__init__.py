import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# 拡張機能のインスタンス化
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'default_dev_secret_key'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///default.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # 拡張機能をアプリケーションに連携
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        from . import routes
        from . import models

        # ユーザーローダーの登録
        @login_manager.user_loader
        def load_user(user_id):
            return db.session.query(models.User).get(int(user_id))

        # Blueprintの登録
        app.register_blueprint(routes.bp)

        # ビルドを確実にするための統一コマンドを登録
        from flask_migrate import upgrade
        from seed_db import seed_database
        
        @app.cli.command('setup-db')
        def setup_db_command():
            """データベースのテーブル作成と初期データの投入を両方行います。"""
            print("--- Running database upgrade... ---")
            upgrade()
            print("--- Database upgrade finished. ---")
            
            print("--- Seeding database... ---")
            seed_database(db)
            print("--- Database seeding finished. ---")

    return app
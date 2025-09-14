# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# 最初に拡張機能のインスタンスを作成します
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'


def create_app():
    """アプリケーションファクトリ"""
    app = Flask(__name__, instance_relative_config=True)
    
    # アプリケーションの設定を読み込みます
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'default_dev_secret_key'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///default.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # ★★★ ここが最重要ポイント ★★★
    # 拡張機能をまずアプリケーションに連携させます
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # アプリケーションコンテキスト内で、残りの部分をインポート・登録します
    # これにより循環インポートが完全に解決されます
    with app.app_context():
        from . import routes
        from . import models

        # ユーザーローダーを登録
        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(int(user_id))

        # Blueprintを登録
        app.register_blueprint(routes.bp)

        # カスタムCLIコマンドを登録
        from seed_db import seed_database
        @app.cli.command('seed-db')
        def seed_db_command():
            """データベースに初期データを投入します。"""
            seed_database(db)
            print('データベースの初期化が完了しました。')

    return app
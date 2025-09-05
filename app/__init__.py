import os
from flask import Flask
from .models import db
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # 設定の読み込み
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-for-local-use'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # データベースURIの設定
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        db_path = os.path.join(app.instance_path, 'database.db')
        os.makedirs(app.instance_path, exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # 拡張機能の初期化
    db.init_app(app)
    migrate = Migrate() # <-- Migrateインスタンスを先に作成
    migrate.init_app(app, db) # <-- 正しい変数名 "migrate" を使用

    # ルート（Blueprint）の登録
    from . import routes
    app.register_blueprint(routes.bp)

    return app
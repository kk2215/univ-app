# app/__init__.py

import os
from flask import Flask
from .models import db
from flask_migrate import Migrate

# __name__を'app'としてインスタンスを作成
app = Flask('app', instance_relative_config=True)

# 1. SECRET_KEYの設定
app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-should-be-changed'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# 2. データベースURLの設定
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # RenderのPostgreSQLを使う場合
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # ローカルで動かす場合 (instanceフォルダにdatabase.dbを作成)
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
    os.makedirs(instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'database.db')}"

# 3. 拡張機能の初期化
db.init_app(app)
migrate = Migrate(app, db)

# 4. ルートの登録
from . import routes
app.register_blueprint(routes.bp)
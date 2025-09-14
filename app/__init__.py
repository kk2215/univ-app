import os
from flask import Flask
from .models import db
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# ★ 2. LoginManagerのインスタンスを作成
login_manager = LoginManager()
# ★ 3. ログインしていないユーザーがアクセスした場合にリダイレクトする先を指定
login_manager.login_view = 'main.login' 
# ↑ 'main.login' の部分は、あなたのログインページのルート関数名に合わせてください

# このファイルで定義しているdbやmigrateと同じように追加します
db = SQLAlchemy()
migrate = Migrate()

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
    
    login_manager.init_app(app)
    
    # ルート（Blueprint）の登録
    from . import routes
    app.register_blueprint(routes.bp)

    return app

from .models import User # Userモデルをインポート

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
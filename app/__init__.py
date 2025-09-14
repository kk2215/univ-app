# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# --- 1. 拡張機能のインスタンス化 ---
# まず、主要な拡張機能の「空の」インスタンスを作成します。
# この時点では、まだどのFlaskアプリとも連携していません。
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# ログインしていないユーザーが保護されたページにアクセスした際の
# リダイレクト先を指定します。'main.login'は「main」という名前の
# Blueprintにある「login」という名前のルート関数を指します。
login_manager.login_view = 'main.login'


# --- 2. ユーザーローダー関数の定義 ---
# Flask-Loginが、セッションに保存されたIDから
# 現在のユーザーをどのように見つけるかを定義します。
# この関数は、login_managerインスタンスを作成した後に定義する必要があります。
# Userモデルをここでインポートします。
from .models import User

@login_manager.user_loader
def load_user(user_id):
    # 文字列として保存されているIDを整数に変換して、データベースからユーザーを検索します。
    return User.query.get(int(user_id))


# --- 3. アプリケーションファクトリ関数の定義 ---
# この関数が、Flaskアプリケーションのインスタンスを生成し、
# すべての設定と拡張機能を組み立てる中心的な役割を果たします。
def create_app():
    # Flaskアプリケーションのインスタンスを作成
    app = Flask(__name__, instance_relative_config=True)

    # --- アプリケーションの設定 ---
    # Renderなどの本番環境では、DATABASE_URLやSECRET_KEYは
    # 環境変数から読み込むのが一般的です。
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'default_dev_secret_key'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///default.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # --- 拡張機能をアプリケーションに連携 ---
    # ここが最も重要な部分です。
    # ここで初めて、dbやlogin_managerがappと結びつきます。
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- Blueprintの登録 ---
    # routes.pyなどで定義されたルートをアプリケーションに登録します。
    from . import routes
    app.register_blueprint(routes.bp)

    # アプリケーションのコンテキスト内でモデルを認識させるために、
    # modelsモジュールをインポートすることが推奨される場合があります。
    from . import models

    # 組み立てが完了したアプリケーションインスタンスを返します。
    return app
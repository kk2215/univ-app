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


# app/__init__.py の create_app 関数

def create_app():
    print("--- 1. create_app() が呼び出されました ---")
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'default_dev_secret_key'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///default.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    print("--- 2. db.init_app(app) を呼び出します ---")
    db.init_app(app)
    print("--- 3. db.init_app(app) が完了しました ---")
    
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        from . import routes
        from . import models

        @login_manager.user_loader
        def load_user(user_id):
        # db.session.query() を使うことで、正しく初期化されたdbインスタンスを参照します
         return db.session.query(models.User).get(int(user_id))

        app.register_blueprint(routes.bp)

        from seed_db import seed_database
        
        print("--- 4. seed-db コマンドを登録します ---")
        @app.cli.command('seed-db')
        def seed_db_command():
            """データベースに初期データを投入します。"""
            print("--- 6. seed_db_command が実行されました ---")
            seed_database(db)
            print('データベースの初期化が完了しました。')

    print("--- 5. create_app() が完了します ---")
    return app
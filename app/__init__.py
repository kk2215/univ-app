import os
from flask import Flask
from .models import db
from flask_migrate import Migrate

app = Flask(__name__, instance_relative_config=True)

# 1. 最初にデフォルトのローカルDBを設定
app.config.from_mapping(
    SECRET_KEY='dev', # 開発中は'dev'でOK, 本番では環境変数で上書き
    SQLALCHEMY_DATABASE_URI='sqlite:///instance/database.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# 2. Renderの環境変数があれば、それで設定を上書き
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # RenderのPostgreSQL URL形式をSQLAlchemyが認識できる形式に修正
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url

    # 本番用の強力なSECRET_KEYも環境変数から読み込む
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db.init_app(app)
migrate = Migrate(app, db)

from . import routes
app.register_blueprint(routes.bp)
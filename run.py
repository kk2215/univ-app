# app.py (または run.py)

from flask import Flask
from app.routes import bp
from app.models import db          # <-- 重要パーツ1: models.pyからdbをインポート
from flask_migrate import Migrate  # <-- 重要パーツ2: Migrateをインポート

app = Flask(__name__)
# SECRET_KEYなどの設定
app.config['SECRET_KEY'] = 'a-very-secret-key'
app.config['DATABASE'] = 'database.db' # これはFlask独自の設定なので残してOK

# SQLAlchemyとMigrateの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)         # <-- 重要パーツ3: アプリケーションと紐付け

app.register_blueprint(bp)
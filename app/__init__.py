from flask import Flask
from .models import db
from flask_migrate import Migrate

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'a-very-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

from . import routes
app.register_blueprint(routes.bp)

# __init__.pyのトップレベルでFlask appインスタンスを返す必要はありません
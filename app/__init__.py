import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='your_super_secret_key_change_later',
        DATABASE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.db'),
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app
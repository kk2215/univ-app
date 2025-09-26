# tests/conftest.py

import pytest
from app import create_app, db

@pytest.fixture(scope='module')
def app():
    """Flaskアプリのインスタンスを作成する"""
    app = create_app()
    app.config.update({
        "TESTING": True,
        # テスト用のDB設定（インメモリSQLiteなど）
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", 
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture()
def client(app):
    """テスト用のクライアント（仮想ブラウザ）を作成する"""
    return app.test_client()
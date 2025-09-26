# tests/conftest.py

import pytest
from app import create_app, db
from config import Config

# ▼▼▼ テスト専用の設定クラスを追加 ▼▼▼
class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # ファイルではなくメモリ上のDBを使用
    WTF_CSRF_ENABLED = False # テストではCSRF保護を無効にすると便利

@pytest.fixture(scope='module')
def app():
    """Flaskアプリのインスタンスを作成する"""
    app = create_app(TestConfig) # ▼▼▼ テスト用の設定を渡す ▼▼▼

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture()
def client(app):
    """テスト用のクライアント（仮想ブラウザ）を作成する"""
    return app.test_client()
import os
import sys
from logging.config import fileConfig

from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool

# これにより、スクリプトがappディレクトリ内のモジュールをインポートできるようになります
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Alembic Configオブジェクト。iniファイルへのアクセスを提供します。
config = context.config

# iniファイルからロギング設定を読み込みます
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ▼▼▼ ここからが重要な部分です ▼▼▼
# Flask-SQLAlchemyのdb.metadataをターゲットに設定します
from app.models import db
target_metadata = db.metadata
# ▲▲▲ ここまで ▲▲▲

def run_migrations_offline() -> None:
    """オフラインモードでマイグレーションを実行します。"""
    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """オンラインモードでマイグレーションを実行します。"""
    # connectableはSQLAlchemy Engineオブジェクトです
    connectable = current_app.extensions['sqlalchemy'].engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
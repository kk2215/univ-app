from logging.config import fileConfig

from flask import current_app
from alembic import context

# Alembic Configオブジェクト。iniファイルへのアクセスを提供します。
config = context.config

# iniファイルからロギング設定を読み込みます
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- ここからが重要な修正部分です ---
# Flask-SQLAlchemyのdbオブジェクトをインポートします
from app import db
# すべてのモデルをインポートして、Alembicがテーブルを認識できるようにします
from app.models import (
    User, Subject, University, Faculty, Book, Route, RouteStep, Progress,
    UserContinuousTaskSelection, UserSequentialTaskSelection, StudyLog,
    SubjectStrategy, Weakness, UserHiddenTask, MockExam, OfficialMockExam
)
# Base.metadataの代わりに、Flask-SQLAlchemyのdb.metadataをターゲットにします
target_metadata = db.metadata
# --- ここまで ---

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
    # 実行中のFlaskアプリから直接エンジンを取得します
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
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# この行を追加して、アプリケーションのモデルをインポートできるようにします
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# ▼▼▼ ここからが重要な修正部分です ▼▼▼
# Flaskアプリケーションとdbオブジェクトをインポートします
from app import create_app, db
# すべてのモデルをインポートして、Alembicが認識できるようにします
from app.models import User, Subject, University, Faculty, Book, Route, RouteStep, Progress, UserContinuousTaskSelection, UserSequentialTaskSelection, StudyLog, SubjectStrategy, Weakness, UserHiddenTask, MockExam, OfficialMockExam

# Flaskアプリのインスタンスを作成
app = create_app()

# 設定オブジェクトを取得
config = context.config

# FlaskアプリのコンフィギュレーションをAlembicに設定
config.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])

# Base.metadataの代わりに、Flask-SQLAlchemyのdb.metadataをターゲットにします
target_metadata = db.metadata
# ▲▲▲ ここまでが重要な修正部分です ▲▲▲

def run_migrations_offline() -> None:
    """オフラインモードでマイグレーションを実行します。"""
    url = config.get_main_option("sqlalchemy.url")
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
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
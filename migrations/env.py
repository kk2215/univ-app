from logging.config import fileConfig
from flask import current_app
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app import db
from app.models import (
    User, Subject, University, Faculty, Book, Route, RouteStep, Progress,
    UserContinuousTaskSelection, UserSequentialTaskSelection, StudyLog,
    SubjectStrategy, Weakness, UserHiddenTask, MockExam, OfficialMockExam
)
target_metadata = db.metadata

def run_migrations_offline() -> None:
    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
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
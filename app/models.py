from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ユーザーと科目を繋ぐための中間テーブル（多対多リレーションシップ用）
user_subjects_table = db.Table('user_subjects',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    grade = db.Column(db.String, nullable=False)
    school = db.Column(db.String, nullable=False)
    faculty = db.Column(db.String, nullable=False)
    plan_type = db.Column(db.String, nullable=False)
    course_type = db.Column(db.String)
    prefecture = db.Column(db.String)
    target_exam_date = db.Column(db.Date)
    starting_level = db.Column(db.Integer, nullable=False)
    learning_style = db.Column(db.String)
    subjects = db.relationship('Subject', secondary=user_subjects_table, back_populates='users')

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    users = db.relationship('User', secondary=user_subjects_table, back_populates='subjects')

class University(db.Model):
    __tablename__ = 'universities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    kana_name = db.Column(db.String, nullable=False)
    level = db.Column(db.String, nullable=False)
    info_url = db.Column(db.String)

class Faculty(db.Model):
    __tablename__ = 'faculties'
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=False)
    name = db.Column(db.String, nullable=False)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    youtube_query = db.Column(db.String)
    duration_weeks = db.Column(db.Integer, nullable=False, default=1)
    task_type = db.Column(db.String, nullable=False, default='sequential')

class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    plan_type = db.Column(db.String, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))

class RouteStep(db.Model):
    __tablename__ = 'route_steps'
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    level = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    is_main = db.Column(db.Integer, nullable=False, default=1)

# app/models.py

class Progress(db.Model):
    __tablename__ = 'progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False) # <-- この行を追加
    is_completed = db.Column(db.Integer, nullable=False)

class UserContinuousTaskSelection(db.Model):
    __tablename__ = 'user_continuous_task_selections'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), primary_key=True)
    level = db.Column(db.String, primary_key=True)
    category = db.Column(db.String, primary_key=True)
    selected_task_id = db.Column(db.String, nullable=False)

class UserSequentialTaskSelection(db.Model):
    __tablename__ = 'user_sequential_task_selections'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    group_id = db.Column(db.String, primary_key=True)
    selected_task_id = db.Column(db.String, nullable=False)

class StudyLog(db.Model):
    __tablename__ = 'study_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SubjectStrategy(db.Model):
    __tablename__ = 'subject_strategies'
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), primary_key=True)
    strategy_html = db.Column(db.String, nullable=False)

class Weakness(db.Model):
    __tablename__ = 'weaknesses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String, nullable=False)
    
class UserHiddenTask(db.Model):
    __tablename__ = 'user_hidden_tasks'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    task_id = db.Column(db.String, primary_key=True)
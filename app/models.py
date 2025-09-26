from datetime import datetime
from .extensions import db
from flask_login import UserMixin

# ユーザーと科目を繋ぐための中間テーブル（多対多リレーションシップ用）
user_subjects_table = db.Table('user_subjects',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    grade = db.Column(db.String, nullable=False)
    school = db.Column(db.String, nullable=False)
    faculty = db.Column(db.String, nullable=False)
    plan_type = db.Column(db.String, nullable=False)
    course_type = db.Column(db.String)
    prefecture = db.Column(db.String)
    target_exam_date = db.Column(db.Date)
    learning_style = db.Column(db.String)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
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
    description = db.Column(db.String)
    youtube_query = db.Column(db.String)
    duration_weeks = db.Column(db.Integer, default=1)
    task_type = db.Column(db.String, nullable=False, default='sequential')
    url = db.Column(db.String(255), nullable=True)

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

class Progress(db.Model):
    __tablename__ = 'progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
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
    comment = db.Column(db.Text, nullable=True)
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
    
class MockExam(db.Model):
    __tablename__ = 'mock_exams'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_name = db.Column(db.String, nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    provider = db.Column(db.String) # ▼▼▼ 予備校名（河合、駿台など）を追加 ▼▼▼
    
    # ▼▼▼ この模試に紐づく、科目ごとの結果リストを定義 ▼▼▼
    results = db.relationship('MockExamResult', backref='mock_exam', cascade="all, delete-orphan")

# ▼▼▼▼▼ この新しいモデルをファイルの一番下などに追加 ▼▼▼▼▼
class MockExamResult(db.Model):
    __tablename__ = 'mock_exam_results'
    id = db.Column(db.Integer, primary_key=True)
    mock_exam_id = db.Column(db.Integer, db.ForeignKey('mock_exams.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    score = db.Column(db.Integer)       # 点数
    max_score = db.Column(db.Integer)   # 満点
    deviation = db.Column(db.Float)     # 偏差値
    ranking = db.Column(db.String)      # 判定 (A, B, Cなど)

    # どの科目の結果かを簡単に取得できるようにする
    subject = db.relationship('Subject')
    
class OfficialMockExam(db.Model):
    __tablename__ = 'official_mock_exam'
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    app_start_date = db.Column(db.Date, nullable=True) 
    app_end_date = db.Column(db.Date, nullable=True)
    url = db.Column(db.String(255), nullable=False)
    target_grade = db.Column(db.String(50), nullable=True)
    
# お問い合わせを保存するためのモデル
class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # ▼▼▼ 追加 ▼▼▼
    name = db.Column(db.String(100), nullable=True) # ▼▼▼ nullable=True に変更 ▼▼▼
    email = db.Column(db.String(100), nullable=True) # ▼▼▼ nullable=True に変更 ▼▼▼
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)
    faq_id = db.Column(db.Integer, db.ForeignKey('faqs.id'), nullable=True)

    def __repr__(self):
        return f'<Inquiry {self.id}>'
    
class Reply(db.Model):
    __tablename__ = 'replies'
    id = db.Column(db.Integer, primary_key=True)
    inquiry_id = db.Column(db.Integer, db.ForeignKey('inquiries.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # 関連するInquiryやUserオブジェクトを簡単に取得できるようにする
    inquiry = db.relationship('Inquiry', backref=db.backref('replies', lazy=True))
    admin = db.relationship('User')    
    
class FAQ(db.Model):
    __tablename__ = 'faqs'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    sort_order = db.Column(db.Integer, default=0) 
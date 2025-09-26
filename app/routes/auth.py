# app/routes/auth.py
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.datastructures import MultiDict
from flask_login import login_user, logout_user
from .. import db
from ..models import User, Subject 

# 'auth'という名前のブループリントを作成
auth_bp = Blueprint('auth', __name__)

# ここに、register, login, logout関数を移動してきます

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None
    form_data = MultiDict()
    
    if request.method == 'POST':
        form_data = request.form
        username = form_data.get('username')
        password = form_data.get('password')
        password_confirm = form_data.get('password_confirm')
        grade = form_data.get('grade')
        course_type = form_data.get('course_type')
        school = form_data.get('school')
        faculty = form_data.get('faculty')
        
        if not all([username, password, password_confirm, grade, course_type, school, faculty]):
            error_message = "全ての必須項目を入力してください。"
        elif password != password_confirm:
            error_message = "パスワードが一致しません。"
        # ▼▼▼ Model.query -> db.session.query(Model) に変更 ▼▼▼
        elif db.session.query(User).filter_by(username=username).first():
            error_message = "そのユーザー名は既に使用されています。"
        
        if not error_message:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            target_exam_date_str = form_data.get('target_exam_date')
            target_exam_date = date.fromisoformat(target_exam_date_str) if target_exam_date_str else None
        
            new_user = User(
                username=username, password_hash=password_hash, grade=grade,
                course_type=course_type, school=school, faculty=faculty,
                plan_type='standard', prefecture=form_data.get('prefecture'),
                target_exam_date=target_exam_date
            )
            db.session.add(new_user)
            db.session.commit()

            subject_ids = form_data.getlist('subjects')
            for subject_id_str in subject_ids:
                subject = db.session.query(Subject).get(int(subject_id_str))
                if subject:
                    new_user.subjects.append(subject)
            
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('main.dashboard', user_id=new_user.id))

    subjects = db.session.query(Subject).order_by(Subject.id).all()
    return render_template('register.html', subjects=subjects, error=error_message, form_data=form_data)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.session.query(User).filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # ▼▼▼ 2. sessionの操作を login_user(user) に置き換える ▼▼▼
            login_user(user) 
            
            # ログイン後にリダイレクトすべきページがあれば、そちらにリダイレクト
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard', user_id=user.id))
        else:
            error_message = "ユーザー名またはパスワードが正しくありません。"
    return render_template('login.html', error=error_message)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
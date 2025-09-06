import calendar
from datetime import date, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, jsonify, session
)
from collections import defaultdict
from werkzeug.security import generate_password_hash, check_password_hash

# データベースモデルを全てインポートします
from .models import db, User, Subject, University, Faculty, Book, Route, RouteStep, Progress, UserSubjectLevel, UserContinuousTaskSelection, UserSequentialTaskSelection, StudyLog, SubjectStrategy, Weakness, UserHiddenTask

bp = Blueprint('main', __name__)

# --- 認証 & 基本ページ ---

@bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard', user_id=session['user_id']))
    return render_template('index.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        grade = request.form.get('grade')
        course_type = request.form.get('course_type')
        school = request.form.get('school')
        faculty = request.form.get('faculty')
        prefecture = request.form.get('prefecture')
        target_exam_date_str = request.form.get('target_exam_date')
        starting_level = request.form.get('starting_level')
        error_message = None

        if not all([username, password, password_confirm, grade, course_type, school, faculty, starting_level]):
            error_message = "全ての必須項目を入力してください。"
        elif password != password_confirm:
            error_message = "パスワードが一致しません。"
        elif User.query.filter_by(username=username).first():
            error_message = "そのユーザー名は既に使用されています。"
        
        if error_message:
            subjects = Subject.query.order_by(Subject.id).all()
            return render_template('register.html', subjects=subjects, error=error_message)

        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        target_exam_date = date.fromisoformat(target_exam_date_str) if target_exam_date_str else None
        
        new_user = User(
            username=username, password_hash=password_hash, grade=grade,
            course_type=course_type, school=school, faculty=faculty,
            plan_type='standard', prefecture=prefecture,
            target_exam_date=target_exam_date, starting_level=int(starting_level)
        )
        db.session.add(new_user)
        db.session.commit()

        subject_ids = request.form.getlist('subjects')
        for subject_id_str in subject_ids:
            subject_id = int(subject_id_str)
            subject = Subject.query.get(subject_id)
            if subject:
                new_user.subjects.append(subject)
            
            start_level_for_subject = request.form.get(f'start_level_{subject_id}', starting_level)
            user_subject_level = UserSubjectLevel(
                user_id=new_user.id, subject_id=subject_id,
                start_level=int(start_level_for_subject)
            )
            if not UserSubjectLevel.query.filter_by(user_id=new_user.id, subject_id=subject_id).first():
                db.session.add(user_subject_level)
        
        db.session.commit()
        session['user_id'] = new_user.id
        return redirect(url_for('main.dashboard', user_id=new_user.id))

    subjects = Subject.query.order_by(Subject.id).all()
    return render_template('register.html', subjects=subjects)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('main.dashboard', user_id=user.id))
        else:
            error_message = "ユーザー名またはパスワードが正しくありません。"
    return render_template('login.html', error=error_message)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@bp.route('/plan/<int:user_id>')
def show_plan(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)
    if not user:
        return "ユーザーが見つかりません", 404

    # --- 1. 必要なデータをまとめて取得 ---
    target_school = University.query.filter_by(name=user.school).first()
    target_level_name = target_school.level if target_school else None
    level_hierarchy = { '基礎徹底レベル': 0, '高校入門レベル': 0, '日東駒専レベル': 1, '産近甲龍': 1, 'MARCHレベル': 2, '関関同立': 2, '早慶レベル': 3, '早稲田レベル': 3, '難関国公立・東大・早慶レベル': 3, '特殊形式': 98 }
    target_level_value = level_hierarchy.get(target_level_name, 99)
    
    start_levels_map = {usl.subject_id: usl.start_level for usl in UserSubjectLevel.query.filter_by(user_id=user_id).all()}
    user_subject_ids = [s.id for s in user.subjects]
    subjects_map = {s.id: s.name for s in Subject.query.all()}
    subject_ids_map = {v: k for k, v in subjects_map.items()}
    
    cont_selections_rows = UserContinuousTaskSelection.query.filter_by(user_id=user_id).all()
    user_selections = {(row.subject_id, row.level, row.category): row.selected_task_id for row in cont_selections_rows}
    
    seq_selections_rows = UserSequentialTaskSelection.query.filter_by(user_id=user_id).all()
    sequential_selections = {row.group_id: row.selected_task_id for row in seq_selections_rows}
    
    completed_tasks_set = {p.task_id for p in Progress.query.filter_by(user_id=user_id, is_completed=1).all()}
    strategies = {s.subject_id: s.strategy_html for s in SubjectStrategy.query.all()}
    
    # --- 2. 表示データを科目ごとに生成 ---
    plan_by_subject_level = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    continuous_tasks_by_subject_level_category = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for subject_id in user_subject_ids:
        subject_name = subjects_map.get(subject_id)
        
        query_builder = db.session.query(
            Subject.name.label('subject_name'), Book.task_id, Book.title.label('book'),
            Book.description, Book.youtube_query, Book.task_type, RouteStep.level,
            RouteStep.category, RouteStep.is_main, Book.duration_weeks
        ).select_from(Route).join(RouteStep, Route.id == RouteStep.route_id)\
         .join(Book, RouteStep.book_id == Book.id)\
         .join(Subject, Route.subject_id == Subject.id)


        if subject_name == '数学':
            route_name = 'math_rikei_standard' if user.course_type == 'science' else 'math_bunkei_standard'
            subject_plan_rows = query_builder.filter(Route.name == route_name).order_by(RouteStep.step_order).all()
        else:
            subject_plan_rows = query_builder.filter(Route.plan_type == 'standard', Route.subject_id == subject_id).order_by(RouteStep.step_order).all()
        
        subject_plan = [dict(row._mapping) for row in subject_plan_rows]
        
        # Pythonでレベルの難易度順に並べ替え
        subject_plan.sort(key=lambda task: level_hierarchy.get(task['level'], 99))

        if subject_plan:
            starting_level_value = start_levels_map.get(subject_id, 0)
            filtered_plan = [task for task in subject_plan if starting_level_value <= level_hierarchy.get(task['level'], 0) <= target_level_value]
            
            sequential_tasks = [task for task in filtered_plan if task['task_type'] == 'sequential']
            continuous_tasks = [task for task in filtered_plan if task['task_type'] == 'continuous']
            
            if continuous_tasks:
                for task in continuous_tasks:
                    continuous_tasks_by_subject_level_category[subject_name][task['level']][task['category']].append(task)
            
            if sequential_tasks:
                today = date.today()
                exam_date = user.target_exam_date if user.target_exam_date else date(today.year + 1, 2, 25)
                task_groups, temp_group = [], []
                for task in sequential_tasks:
                    if task['is_main'] == 1 and temp_group:
                        task_groups.append(temp_group); temp_group = []
                    temp_group.append(task)
                if temp_group: task_groups.append(temp_group)

                main_tasks_in_groups = [sequential_selections.get(next((t['task_id'] for t in g if t['is_main']), g[0]['task_id']), next((t['task_id'] for t in g if t['is_main']), g[0]['task_id'])) for g in task_groups]
                main_tasks_details = [task for task in sequential_tasks if task['task_id'] in main_tasks_in_groups]
                total_duration = sum(task['duration_weeks'] for task in main_tasks_details)
                weeks_until_exam = max(1, (exam_date - today).days / 7)
                pace_factor = weeks_until_exam / total_duration if total_duration > 0 else 1
                current_deadline = exam_date
                deadlines = {}
                for task in reversed(main_tasks_details):
                    adjusted_duration = task['duration_weeks'] * pace_factor
                    days_to_subtract = max(7, round(adjusted_duration * 7))
                    current_deadline -= timedelta(days=days_to_subtract)
                    deadlines[task['task_id']] = current_deadline.strftime('%Y-%m-%d')
                for group in task_groups:
                    main_task_id = next((t['task_id'] for t in group if t['is_main']), group[0]['task_id'])
                    deadline_for_group = deadlines.get(main_task_id, exam_date.strftime('%Y-%m-%d'))
                    for task in group:
                        task['deadline'] = deadline_for_group
                    plan_by_subject_level[subject_name][group[0]['level']][group[0]['category']].append(group)
    
    return render_template(
        'plan.html', user=user, plan_data=plan_by_subject_level, 
        continuous_tasks_data=continuous_tasks_by_subject_level_category,
        user_selections=user_selections, sequential_selections=sequential_selections,
        title="学習マップ", completed_tasks=completed_tasks_set,
        strategies=strategies, subject_ids_map=subject_ids_map
    )

@bp.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)
    if not user:
        return "ユーザーが見つかりません", 404

    university = University.query.filter_by(name=user.school).first()
    days_until_exam = "未設定"
    if user.target_exam_date:
        days_until_exam = (user.target_exam_date - date.today()).days

    subjects_map = {s.id: s.name for s in Subject.query.all()}
    user_subject_ids = [s.id for s in user.subjects]
    completed_tasks_set = {p.task_id for p in Progress.query.filter_by(user_id=user_id, is_completed=1).all()}
    
    cont_selections = db.session.query(
        UserContinuousTaskSelection.subject_id,
        UserContinuousTaskSelection.level,
        UserContinuousTaskSelection.category,
        UserContinuousTaskSelection.selected_task_id,
        Book.title
    ).join(Book, UserContinuousTaskSelection.selected_task_id == Book.task_id)\
     .filter(UserContinuousTaskSelection.user_id == user_id).all()
     
    seq_selections = {row.group_id: row.selected_task_id for row in UserSequentialTaskSelection.query.filter_by(user_id=user_id).all()}

    dashboard_data = []
    for subject_id in user_subject_ids:
        subject_name = subjects_map.get(subject_id)
        subject_info = {'name': subject_name, 'next_task': None, 'continuous_tasks': [], 'progress': 0, 'last_completed_task': None, 'pending_selections': []}
        
        base_query = db.session.query(
            Book.task_id, Book.title, Book.youtube_query, Book.task_type, 
            RouteStep.level, RouteStep.category, RouteStep.is_main
        ).join(RouteStep, Book.id == RouteStep.book_id)\
         .join(Route, RouteStep.route_id == Route.id)

        if subject_name == '数学':
            route_name = 'math_rikei_standard' if user.course_type == 'science' else 'math_bunkei_standard'
            full_plan_rows = base_query.filter(Route.name == route_name).order_by(RouteStep.step_order).all()
        else:
            full_plan_rows = base_query.filter(Route.plan_type == 'standard', Route.subject_id == subject_id).order_by(RouteStep.step_order).all()
        
        full_plan = [dict(row._mapping) for row in full_plan_rows]
        
        current_level = None
        if full_plan:
            sequential_plan = [task for task in full_plan if task['task_type'] == 'sequential']
            if sequential_plan:
                task_groups = []
                temp_group = []
                for task in sequential_plan:
                    if task['is_main'] == 1 and temp_group:
                        task_groups.append(temp_group)
                        temp_group = []
                    temp_group.append(task)
                if temp_group: task_groups.append(temp_group)

                for group in task_groups:
                    group_id = next((t['task_id'] for t in group if t['is_main']), group[0]['task_id'])
                    actual_task_id = seq_selections.get(group_id, group_id)
                    if actual_task_id not in completed_tasks_set:
                        if len(group) > 1 and group_id not in seq_selections:
                            subject_info['next_task'] = {'is_choice_pending': True, 'title': f"『{group[0]['category']}』の参考書を選択してください", 'subject_name': subject_name}
                        else:
                            subject_info['next_task'] = next((t for t in group if t['task_id'] == actual_task_id), group[0])
                        break
                
                plan_task_ids_in_groups = [seq_selections.get(next((t['task_id'] for t in g if t['is_main']), g[0]['task_id']), g[0]['task_id']) for g in task_groups]
                completed_in_plan = [task_id for task_id in plan_task_ids_in_groups if task_id in completed_tasks_set]
                if completed_in_plan:
                    last_completed_id = completed_in_plan[-1]
                    subject_info['last_completed_task'] = Book.query.filter_by(task_id=last_completed_id).first()
                
                if subject_info['next_task'] and not isinstance(subject_info['next_task'], dict):
                    current_level = subject_info['next_task']['level']
                elif completed_in_plan:
                    last_task_in_plan = next((t for t in sequential_plan if t['task_id'] == completed_in_plan[-1]), None)
                    current_level = last_task_in_plan['level'] if last_task_in_plan else None
                else:
                    current_level = sequential_plan[0]['level'] if sequential_plan else None
                
                subject_info['progress'] = int((len(completed_in_plan) / len(task_groups)) * 100) if task_groups else 0

            continuous_tasks_in_plan = [task for task in full_plan if task['task_type'] == 'continuous' and task['category'] != '補助教材']
            tasks_to_display = []
            tasks_by_category = defaultdict(list)
            for task in continuous_tasks_in_plan:
                tasks_by_category[task['category']].append(task)

            for category, tasks in tasks_by_category.items():
                if category == '漢字':
                    if tasks: tasks_to_display.append({'title': tasks[0]['title']}); continue
                if not current_level: continue
                tasks_in_current_level = [t for t in tasks if t['level'] == current_level]
                if not tasks_in_current_level: continue
                
                user_selection = next((s for s in cont_selections if s.subject_id == subject_id and s.level == current_level and s.category == category), None)

                if len(tasks_in_current_level) > 1:
                    if user_selection:
                        tasks_to_display.append({'title': user_selection.title})
                    else:
                        subject_info['pending_selections'].append(f"{current_level}の{category}")
                else:
                    tasks_to_display.append({'title': tasks_in_current_level[0]['title']})

            subject_info['continuous_tasks'] = tasks_to_display
        dashboard_data.append(subject_info)

    return render_template('dashboard.html', user=user, university=university, days_until_exam=days_until_exam, dashboard_data=dashboard_data)


@bp.route('/support/<int:user_id>')
def support(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('main.login'))
    
    user = User.query.get(user_id)
    if not user:
        return "ユーザーが見つかりません", 404

    # ここに、支援制度のデータを定義します
    support_data = {
        "東京都": [
            {"name": "受験生チャレンジ支援貸付事業", "description": "塾代や受験費用を無利子で借りられ、入学すれば返済が免除される場合があります。"},
        ],
        "大阪府": [
            {"name": "塾代助成事業", "description": "所得制限等に応じて、塾代に利用できるクーポンが支給されます。"},
        ]
        # 他の都道府県のデータも追加可能
    }
    
    user_support = support_data.get(user.prefecture, [])
    
    return render_template('support.html', user=user, support_list=user_support)

@bp.route('/stats/<int:user_id>')
def stats(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)
    if not user:
        return "ユーザーが見つかりません", 404
    
    try:
        year = int(request.args.get('year', date.today().year))
        month = int(request.args.get('month', date.today().month))
    except (TypeError, ValueError):
        today = date.today(); year, month = today.year, today.month
        
    current_month_date = date(year, month, 1)
    prev_month_date = current_month_date - timedelta(days=1)
    next_month_date = (current_month_date + timedelta(days=32)).replace(day=1)
    prev_month = {'year': prev_month_date.year, 'month': prev_month_date.month}
    next_month = {'year': next_month_date.year, 'month': next_month_date.month}
    is_future = (year > date.today().year) or (year == date.today().year and month >= date.today().month)
    
    # グラフ用データ
    total_by_subject = db.session.query(Subject.name, db.func.sum(StudyLog.duration_minutes).label('total')).join(Subject, StudyLog.subject_id == Subject.id).filter(StudyLog.user_id == user_id).group_by(Subject.name).all()
    last_7_days = db.session.query(StudyLog.date, db.func.sum(StudyLog.duration_minutes).label('total')).filter(StudyLog.user_id == user_id, StudyLog.date >= date.today() - timedelta(days=7)).group_by(StudyLog.date).order_by(StudyLog.date).all()
    
    # カレンダー用データ
    if user.grade == 'ronin': thresholds = {5: 600, 4: 480, 3: 300, 2: 180, 1: 1}
    else: thresholds = {5: 300, 4: 180, 3: 120, 2: 60, 1: 1}
    
    all_logs_rows = db.session.query(StudyLog.date, db.func.sum(StudyLog.duration_minutes).label('total')).filter(StudyLog.user_id == user_id).group_by(StudyLog.date).all()
    study_data = {row.date.isoformat(): row.total for row in all_logs_rows}
    cal = calendar.Calendar()
    month_days = cal.monthdatescalendar(year, month)
    calendar_data = []
    for week in month_days:
        week_data = []
        for day in week:
            total_minutes = study_data.get(day.isoformat(), 0)
            color_level = 0
            for level, minute_req in sorted(thresholds.items(), reverse=True):
                if total_minutes >= minute_req:
                    color_level = level; break
            week_data.append({'date': day, 'total_minutes': total_minutes, 'color_level': color_level})
        calendar_data.append(week_data)
        
    user_subjects_list = [{'id': s.id, 'name': s.name} for s in user.subjects]    
        
    # 最近の記録リストとモーダル用データ
    recent_logs = db.session.query(StudyLog.id, StudyLog.date, Subject.name, StudyLog.duration_minutes).join(Subject).filter(StudyLog.user_id == user_id).order_by(StudyLog.date.desc(), StudyLog.id.desc()).limit(10).all()
    user_subjects = user.subjects
    all_logs_details_rows = StudyLog.query.filter_by(user_id=user_id).all()
    logs_by_date = defaultdict(dict)
    for row in all_logs_details_rows: logs_by_date[row.date.isoformat()][row.subject_id] = row.duration_minutes
    
    return render_template(
        'stats.html', user=user,
        subject_labels=[r.name for r in total_by_subject], subject_data=[r.total for r in total_by_subject],
        date_labels=[r.date.isoformat() for r in last_7_days], date_data=[r.total for r in last_7_days],
        calendar_data=calendar_data, month=month, year=year,
        recent_logs=recent_logs, user_subjects=user_subjects_list,
        logs_by_date=logs_by_date, prev_month=prev_month, next_month=next_month, is_future=is_future
    )

@bp.route('/settings/<int:user_id>', methods=['GET', 'POST'])
def settings(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('main.login'))
    
    user = User.query.get(user_id)
    message, error = None, None

    if request.method == 'POST':
        username = request.form.get('username')
        grade = request.form.get('grade')
        school = request.form.get('school')
        faculty = request.form.get('faculty')
        target_exam_date = request.form.get('target_exam_date')
        
        if not all([username, grade, school, faculty]):
            error = "ユーザー名、学年、志望校、志望学部は必須項目です。"
        else:
            user.username = username
            user.grade = grade
            user.school = school
            user.faculty = faculty
            user.target_exam_date = date.fromisoformat(target_exam_date) if target_exam_date else None
            
            new_subject_ids = {int(sid) for sid in request.form.getlist('subjects')}
            
            # ユーザーの科目を更新
            user.subjects = [subject for subject in Subject.query.all() if subject.id in new_subject_ids]
            
            # 科目ごとのレベルを更新
            UserSubjectLevel.query.filter_by(user_id=user_id).delete()
            for subject_id in new_subject_ids:
                start_level = request.form.get(f'start_level_{subject_id}', 1)
                level_entry = UserSubjectLevel(user_id=user_id, subject_id=subject_id, start_level=int(start_level))
                db.session.add(level_entry)
            
            db.session.commit()
            message = "設定を保存しました。"

    all_subjects = Subject.query.order_by(Subject.id).all()
    user_subject_ids = {s.id for s in user.subjects}
    user_start_levels = {usl.subject_id: usl.start_level for usl in UserSubjectLevel.query.filter_by(user_id=user_id).all()}
    level_options = {0: '中学レベルから', 1: '日東駒専レベルから', 2: 'MARCHレベルから'}

    return render_template(
        'settings.html', user=user, message=message, error=error,
        all_subjects=all_subjects, user_subject_ids=user_subject_ids,
        user_start_levels=user_start_levels, level_options=level_options
    )
    
@bp.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
def change_password(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)
    error, message = None, None

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(user.password_hash, current_password):
            error = "現在のパスワードが正しくありません。"
        elif new_password != confirm_password:
            error = "新しいパスワードが一致しません。"
        elif not new_password:
            error = "新しいパスワードを入力してください。"
        else:
            user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.commit()
            message = "パスワードが正常に変更されました。"
            
    return render_template('change_password.html', user=user, error=error, message=message)

# --- ここから下はAPIエンドポイント ---

@bp.route('/api/universities')
def get_universities():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    search_term = f"{query}%"
    universities = University.query.filter(db.or_(University.name.like(search_term), University.kana_name.like(search_term))).limit(5).all()
    return jsonify([uni.name for uni in universities])

@bp.route('/api/faculties')
def get_faculties():
    university_name = request.args.get('univ', '')
    if not university_name:
        return jsonify([])
    university = University.query.filter_by(name=university_name).first()
    if not university:
        return jsonify([])
    faculties = Faculty.query.filter_by(university_id=university.id).all()
    return jsonify([fac.name for fac in faculties])

@bp.route('/api/update_progress', methods=['POST'])
def update_progress():
    user_id = session.get('user_id')
    if not user_id: return jsonify({'success': False, 'error': 'Not logged in'}), 401
    data = request.get_json()
    task_id = data.get('task_id'); is_completed = data.get('is_completed')
    if task_id is None or is_completed is None:
        return jsonify({'success': False, 'error': 'Missing data'}), 400
    
    progress = Progress.query.filter_by(user_id=user_id, task_id=task_id).first()
    if progress:
        progress.is_completed = 1 if is_completed else 0
    else:
        new_progress = Progress(user_id=user_id, task_id=task_id, is_completed=1 if is_completed else 0)
        db.session.add(new_progress)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/select_continuous_task', methods=['POST'])
def select_continuous_task():
    user_id = session.get('user_id')
    if not user_id: return jsonify({'success': False}), 401
    data = request.get_json()
    subject_id = data.get('subject_id'); level = data.get('level'); category = data.get('category'); task_id = data.get('task_id')
    if not all([subject_id, level, category, task_id]): return jsonify({'success': False}), 400
    
    selection = UserContinuousTaskSelection.query.get((user_id, subject_id, level, category))
    if selection:
        selection.selected_task_id = task_id
    else:
        new_selection = UserContinuousTaskSelection(user_id=user_id, subject_id=subject_id, level=level, category=category, selected_task_id=task_id)
        db.session.add(new_selection)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/select_sequential_task', methods=['POST'])
def select_sequential_task():
    user_id = session.get('user_id')
    if not user_id: return jsonify({'success': False}), 401
    data = request.get_json()
    group_id = data.get('group_id'); task_id = data.get('task_id')
    if not all([group_id, task_id]): return jsonify({'success': False}), 400
    
    selection = UserSequentialTaskSelection.query.get((user_id, group_id))
    if selection:
        selection.selected_task_id = task_id
    else:
        new_selection = UserSequentialTaskSelection(user_id=user_id, group_id=group_id, selected_task_id=task_id)
        db.session.add(new_selection)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/log_study_for_date/<int:user_id>', methods=['POST'])
def log_study_for_date(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    data = request.get_json()
    date_str = data.get('date'); logs = data.get('logs')
    if not date_str or logs is None: return jsonify({'success': False}), 400
    
    for log_item in logs:
        subject_id = log_item.get('subject_id')
        hours = log_item.get('hours') or '0'; minutes = log_item.get('minutes') or '0'
        try:
            total_minutes = int(hours) * 60 + int(minutes)
        except (ValueError, TypeError): total_minutes = 0
        
        existing_log = StudyLog.query.filter_by(user_id=user_id, subject_id=subject_id, date=date.fromisoformat(date_str)).first()
        
        if total_minutes > 0:
            if existing_log:
                existing_log.duration_minutes = total_minutes
            else:
                new_log = StudyLog(user_id=user_id, subject_id=subject_id, date=date.fromisoformat(date_str), duration_minutes=total_minutes)
                db.session.add(new_log)
        elif existing_log:
            db.session.delete(existing_log)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/log/<int:log_id>/delete', methods=['POST'])
def delete_log(log_id):
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('main.login'))
    
    log = StudyLog.query.get(log_id)
    if log and log.user_id == user_id:
        db.session.delete(log)
        db.session.commit()
    return redirect(url_for('main.stats', user_id=user_id))
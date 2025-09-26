# app/routes/main.py
import calendar 
from datetime import date, datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash, abort
from flask_login import login_required, current_user
# ... 他に必要なものをインポート ...
from ..extensions import db
from ..models import (User, Subject, University, Faculty, Book, Route, RouteStep, 
                       Progress, UserContinuousTaskSelection, UserSequentialTaskSelection, 
                       StudyLog, Reply, Inquiry, MockExam, OfficialMockExam, FAQ, MockExamResult)

main_bp = Blueprint('main', __name__)

results_data = {
    'A': {
        'description': 'あなたは、目で見た情報を処理するのが得意なタイプです。図やグラフ、イラスト、色分けされた情報、映像などを通して物事を理解し、記憶することに長けています。',
        'advice': [
            '<strong>参考書選び:</strong> 解説文だけでなく、図やイラスト、写真が豊富な参考書を選びましょう。特に地理や歴史、理科の資料集はあなたの強力な武器になります。',
            '<strong>映像授業の活用:</strong> 文字を読むだけでなく、講師の動きや板書を視覚的に捉えられる映像授業は非常に効果的です。',
            '<strong>ノート術:</strong> 重要なポイントを色分けしたり、情報の関係性を矢印や図でまとめたりすると、記憶に定着しやすくなります。',
            '<strong>暗記の工夫:</strong> 英単語はイラスト付きの単語帳を使ったり、歴史上の人物は肖肖像画とセットで覚えたりするなど、常にビジュアルと結びつけることを意識しましょう。'
        ]
    },
    'B': {
        'description': 'あなたは、耳から入ってくる情報を処理するのが得意なタイプです。講義を聞いたり、ディスカッションをしたり、音読をしたりすることで学習内容が頭に入りやすい傾向があります。',
        'advice': [
            '<strong>音読の徹底:</strong> 英語や古文の文章、覚えたい用語などを積極的に声に出して読みましょう。リズムに乗って覚えるのも効果的です。',
            '<strong>音声教材の活用:</strong> 英単語帳に付属している音声や、講義系の音声コンテンツなどを通学中などのスキマ時間に活用しましょう。',
            '<strong>セルフレクチャー:</strong> 学習した内容を、まるで先生になったかのように自分自身に声に出して説明してみましょう。理解が整理され、記憶が強固になります。',
            '<strong>議論・質問:</strong> 友達と問題を出し合ったり、先生に質問に行ったりして、対話の中で理解を深めるのも得意なはずです。'
        ]
    },
    'C': {
        'description': 'あなたは、文字情報を読んだり書いたりして、論理的に物事を理解・整理するのが得意なタイプです。教科書や参考書の文章をじっくり読み解き、要点をまとめ、自分の言葉で再構築することで知識を定着させます。',
        'advice': [
            '<strong>精読と要約:</strong> 教科書や参考書の解説を丁寧に読み込み、段落ごとや章ごとに内容を要約する習慣をつけましょう。',
            '<strong>ノート作成:</strong> 学習した内容を自分なりにノートにまとめることで、知識が体系的に整理されます。単に書き写すのではなく、情報の構造を意識して整理するのがポイントです。',
            '<strong>問題演習と解説の熟読:</strong> 多くの問題を解き、なぜその答えになるのかを解説でしっかり確認する、というオーソドックスな学習法が最も効果的です。',
            '<strong>反復筆記:</strong> なかなか覚えられない用語や公式は、何度も繰り返し書くことで記憶に定着しやすくなります。'
        ]
    }
}

# --- 認証 & 基本ページ ---

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('.dashboard', user_id=session['user_id']))
    return render_template('index.html')

@main_bp.route('/more/<int:user_id>')
@login_required
def more(user_id):
    if user_id != current_user.id:
        abort(404)
    return render_template('more.html', user=current_user)



@main_bp.route('/plan/<int:user_id>')
@login_required
def show_plan(user_id):
    if user_id != current_user.id:
        abort(404)
    return render_template('plan.html', user=current_user)


# app/routes.py の get_plan_data 関数

@main_bp.route('/api/plan_data/<int:user_id>/<subject_name>')
@login_required
def get_plan_data(user_id, subject_name):
    if user_id != current_user.id: abort(403)
    
    subject = db.session.query(Subject).filter_by(name=subject_name).first()
    if not subject: return jsonify({})

    route = db.session.query(Route).filter_by(subject_id=subject.id, plan_type='standard').first()
    if not route: return jsonify({})

    # --- 1. 必要なデータを全て取得 ---
    all_steps_raw = db.session.query(RouteStep, Book).join(Book, RouteStep.book_id == Book.id).filter(RouteStep.route_id == route.id).order_by(RouteStep.step_order).all()
    
    # ユーザーの全ての選択状況を取得
    seq_selections = {sel.group_id: sel.selected_task_id for sel in db.session.query(UserSequentialTaskSelection).filter_by(user_id=user_id).all()}
    cont_selections_raw = db.session.query(UserContinuousTaskSelection).filter_by(user_id=user_id, subject_id=subject.id).all()
    
    completed_tasks_set = {p.task_id for p in db.session.query(Progress).filter_by(user_id=user_id, is_completed=1).all()}

    # --- 2. ルートタスク(sequential)を処理し、表示するノードを決定 ---
    nodes_to_render, sequential_links_base = [], []
    
    sequential_steps_raw = [(s, b) for s, b in all_steps_raw if b.task_type == 'sequential']
    
    # is_mainフラグでタスクをグループ化
    task_groups = []
    if sequential_steps_raw:
        temp_group = []
        for step, book in sequential_steps_raw:
            if step.is_main == 1 and temp_group:
                task_groups.append(temp_group)
                temp_group = []
            temp_group.append((step, book))
        if temp_group: task_groups.append(temp_group)

    # 各グループを処理して表示ノードを決定
    for group in task_groups:
        group_id = next((b.task_id for s, b in group if s.is_main == 1), group[0][1].task_id)
        user_selected_task_id = seq_selections.get(group_id)

        node_to_add = None
        if user_selected_task_id:
            step, book = next(((s, b) for s, b in group if b.task_id == user_selected_task_id), (None, None))
            if book:
                node_to_add = {"id": book.task_id, "title": book.title, "description": book.description, "youtube_query": book.youtube_query, "level": step.level, "category": step.category, "completed": book.task_id in completed_tasks_set, "is_placeholder": False}
        elif len(group) == 1:
            step, book = group[0]
            node_to_add = {"id": book.task_id, "title": book.title, "description": book.description, "youtube_query": book.youtube_query, "level": step.level, "category": step.category, "completed": book.task_id in completed_tasks_set, "is_placeholder": False}
        else:
            step, _ = group[0]
            node_to_add = {
                "id": f"placeholder_seq_{group_id}", "title": f"【{step.category}】を選択", "description": "クリックして使用する参考書を選択してください。",
                "level": step.level, "category": step.category, "completed": False, 
                "is_placeholder": True, "placeholder_type": "sequential",
                "group_id": group_id,
                "choices": [{"id": b.task_id, "title": b.title} for s, b in group]
            }
        
        if node_to_add:
            nodes_to_render.append(node_to_add)
            if not node_to_add["is_placeholder"]:
                sequential_links_base.append(node_to_add)
    
    graph_links = [{"source": sequential_links_base[i]['id'], "target": sequential_links_base[i+1]['id']} for i in range(len(sequential_links_base) - 1)]

    # --- 3. 継続タスク(continuous)の情報を整形 ---
    current_level = None
    next_node = next((node for node in nodes_to_render if not node['completed']), None)
    if next_node:
        current_level = next_node['level']
    elif nodes_to_render:
        current_level = nodes_to_render[-1]['level']

    continuous_steps = [(s, b) for s, b in all_steps_raw if b.task_type == 'continuous']
    available_choices = defaultdict(list)
    for step, book in continuous_steps:
        if step.level == current_level:
            available_choices[step.category].append({"id": book.task_id, "title": book.title})
            
    return jsonify({
        "graph_data": {"nodes": nodes_to_render, "links": graph_links},
        "continuous_data": {
            "current_level": current_level,
            "current_selections": {sel.category: sel.selected_task_id for sel in cont_selections_raw if sel.level == current_level},
            "available_choices": dict(available_choices)
        }
    })
    
# app/routes.py

# 学年と志望校レベルに応じた、中間目標の基準日（月-日）
BENCHMARK_SCHEDULES = {
    # 高校3年生向けのスケジュール
    'high3': {
        '早慶': {
            '日東駒専': '07-31', # 7月末
            'MARCH': '10-31',   # 10月末
        },
        'MARCH': {
            '日東駒専': '09-30', # 9月末
        }
    },
    # 浪人生向けの、より前倒しのスケジュール
    'ronin': {
        '早慶': {
            '日東駒専': '06-30', # 6月末
            'MARCH': '09-30',   # 9月末
        },
        'MARCH': {
            '日東駒専': '08-31', # 8月末
        }
    }
}    
    
@main_bp.route('/dashboard/<int:user_id>')
@login_required
def dashboard(user_id):
    if user_id != current_user.id:
        abort(404)
    user = current_user

    # --- 1. 基本情報をDBから取得 ---
    university = db.session.query(University).filter_by(name=user.school).first()
    target_level_name = university.level if university else None
    
    completed_tasks_set = {p.task_id for p in db.session.query(Progress).filter_by(user_id=user_id, is_completed=1).all()}
    seq_selections = {row.group_id: row.selected_task_id for row in db.session.query(UserSequentialTaskSelection).filter_by(user_id=user_id).all()}
    cont_selections_rows = db.session.query(UserContinuousTaskSelection).filter(UserContinuousTaskSelection.user_id == user_id).all()
    cont_selections = {(s.subject_id, s.level, s.category): s.selected_task_id for s in cont_selections_rows}
    
    unread_replies = db.session.query(Reply).join(Inquiry).filter(Inquiry.user_id == user_id, Reply.is_read == False).order_by(Reply.created_at.desc()).all()
    upcoming_exams = db.session.query(OfficialMockExam).filter(OfficialMockExam.exam_date >= date.today()).order_by(OfficialMockExam.exam_date.asc()).limit(5).all()

    days_until_exam = (user.target_exam_date - date.today()).days if user.target_exam_date else "未設定"
    level_hierarchy = { '基礎徹底レベル': 0, '高校入門レベル': 0, '日東駒専レベル': 1, '産近甲龍': 1, 'MARCHレベル': 2, '関関同立': 2, '早慶レベル': 3, '早稲田レベル': 3, '難関国公立・東大・早慶レベル': 3, '特殊形式': 98 }
    target_level_value = level_hierarchy.get(target_level_name, 99)

    # --- 2. 各科目のダッシュボード用データを作成 ---
    dashboard_data = []
    for subject in user.subjects:
        # --- 2a. 科目ごとの基本情報を初期化 ---
        subject.next_task = None
        subject.continuous_tasks = []
        subject.progress = 0
        subject.last_completed_task = None
        subject.pending_selections = []
        subject.benchmark = None
        
        # ▼▼▼▼▼ このデバッグブロックを追加 ▼▼▼▼▼
        print(f"\n--- 🕵️‍♂️ デバッグ開始: 科目「{subject.name}」---")
        print(f"1. ユーザーの学年 (user.grade): '{user.grade}'")
        print(f"2. 志望校レベル (target_level_name): '{target_level_name}'")
        print(f"3. ルールブックに学年 '{user.grade}' は存在しますか？ -> {user.grade in BENCHMARK_SCHEDULES}")
        if user.grade in BENCHMARK_SCHEDULES:
            print(f"4. 学年ルールブックにレベル '{target_level_name}' は存在しますか？ -> {target_level_name in BENCHMARK_SCHEDULES.get(user.grade, {})}")
        else:
            print(f"4. 学年ルールブックが存在しないため、レベルをチェックできません。")
        print(f"--- デバッグ終了 ---\n")
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
        
        # --- 2b. 科目ごとのルート計画を取得 ---
        base_query = db.session.query(Book, RouteStep).join(RouteStep, Book.id == RouteStep.book_id).join(Route, RouteStep.route_id == Route.id)
        route_name_map = {'数学': 'math_rikei_standard' if user.course_type == 'science' else 'math_bunkei_standard'}
        route_name = route_name_map.get(subject.name)
        if route_name:
            full_plan_rows = base_query.filter(Route.name == route_name).order_by(RouteStep.step_order).all()
        else:
            full_plan_rows = base_query.filter(Route.plan_type == 'standard', Route.subject_id == subject.id).order_by(RouteStep.step_order).all()

        full_plan = [{'book': b, 'step': s} for b, s in full_plan_rows]
        
        sequential_plan = sorted([task for task in full_plan if task['book'].task_type == 'sequential'], key=lambda x: x['step'].step_order)
        
        task_groups = []
        if sequential_plan:
            temp_group = []
            for task in sequential_plan:
                if task['step'].is_main == 1 and temp_group:
                    task_groups.append(temp_group)
                    temp_group = []
                temp_group.append(task)
            if temp_group: task_groups.append(temp_group)

        # --- 2c. 「次のタスク」と「最後に完了したタスク」を決定 ---
        completed_task_ids_in_plan = []
        uncompleted_groups = []
        for group in task_groups:
            group_id = next((t['book'].task_id for t in group if t['step'].is_main), group[0]['book'].task_id)
            actual_task_id = seq_selections.get(group_id, group_id)
            if actual_task_id in completed_tasks_set:
                completed_task_ids_in_plan.append(actual_task_id)
            else:
                uncompleted_groups.append(group)

        if uncompleted_groups:
            # --- 未完了タスクがある場合の処理 ---
            next_group = uncompleted_groups[0]
            group_id = next((t['book'].task_id for t in next_group if t['step'].is_main), next_group[0]['book'].task_id)
            
            if len(next_group) > 1 and group_id not in seq_selections:
                subject.next_task = {'is_choice_pending': True, 'title': f"『{next_group[0]['step'].category}』を選択", 'subject_name': subject.name, 'level': next_group[0]['step'].level}
            else:
                selected_task_id = seq_selections.get(group_id, group_id)
                subject.next_task = db.session.query(Book).filter_by(task_id=selected_task_id).first()

            user_schedule = BENCHMARK_SCHEDULES.get(user.grade, {}).get(target_level_name, {})
            if user_schedule:
                next_benchmark_level = None
                # uncompleted_groups[0] (つまり next_group) を使う
                for task in next_group:
                    level_from_db = task['step'].level
                    lookup_key = level_from_db.replace('レベル', '')
                    if lookup_key in user_schedule:
                        next_benchmark_level = level_from_db
                        break
                
                if next_benchmark_level:
                    lookup_key = next_benchmark_level.replace('レベル', '')
                    deadline_str = user_schedule[lookup_key]
                    deadline_date = datetime.strptime(f"{date.today().year}-{deadline_str}", "%Y-%m-%d").date()
                    subject.benchmark = {'level_name': next_benchmark_level, 'deadline': deadline_date.strftime('%-m月%-d日'), 'days_remaining': (deadline_date - date.today()).days}

        if completed_task_ids_in_plan:
            subject.last_completed_task = db.session.query(Book).filter_by(task_id=completed_task_ids_in_plan[-1]).first()


        # --- 2e. 「継続タスク」と「現在のレベル」と「進捗率」を決定 ---
        current_level = None
        if subject.next_task and isinstance(subject.next_task, Book):
            task_info = next((t for t in sequential_plan if t['book'].task_id == subject.next_task.task_id), None)
            if task_info: current_level = task_info['step'].level
        elif subject.last_completed_task:
            task_info = next((t for t in sequential_plan if t['book'].task_id == subject.last_completed_task.task_id), None)
            if task_info: current_level = task_info['step'].level
        elif sequential_plan:
            current_level = sequential_plan[0]['step'].level

        if current_level:
            continuous_tasks_in_plan = [task for task in full_plan if task['book'].task_type == 'continuous']
            tasks_by_category = defaultdict(list)
            for task in continuous_tasks_in_plan: tasks_by_category[task['step'].category].append(task)

            tasks_to_display = []
            for category, tasks in tasks_by_category.items():
                tasks_in_current_level = [t for t in tasks if t['step'].level == current_level]
                if not tasks_in_current_level: continue
                
                user_selection_id = cont_selections.get((subject.id, current_level, category))
                if len(tasks_in_current_level) > 1 and not user_selection_id:
                     subject.pending_selections.append(f"{current_level}の{category}")
                else:
                    task_to_add_id = user_selection_id or tasks_in_current_level[0]['book'].task_id
                    book = db.session.query(Book).filter_by(task_id=task_to_add_id).first()
                    if book: tasks_to_display.append(book)
            subject.continuous_tasks = tasks_to_display

        if task_groups:
            subject.progress = int((len(completed_task_ids_in_plan) / len(task_groups)) * 100)

        dashboard_data.append(subject)

    return render_template('dashboard.html', user=user, university=university, 
                           days_until_exam=days_until_exam, dashboard_data=dashboard_data,
                           upcoming_exams=upcoming_exams, unread_replies=unread_replies, today=date.today())
    
    
@main_bp.route('/support/<int:user_id>')
@login_required
def support(user_id):
    user = db.session.query(User).get(user_id)
    if not user or user.id != current_user.id: abort(404)
    support_data = {
        "東京都": [{"name": "受験生チャレンジ支援貸付事業", "description": "塾代や受験費用を無利子で借りられ、入学すれば返済が免除される場合があります。"}],
        "大阪府": [{"name": "塾代助成事業", "description": "所得制限等に応じて、塾代に利用できるクーポンが支給されます。"}]}
    user_support = support_data.get(user.prefecture, [])
    return render_template('support.html', user=user, support_list=user_support)

@main_bp.route('/stats/<int:user_id>')
@login_required
def stats(user_id):
    user = db.session.query(User).get(user_id)
    if not user or user.id != current_user.id: abort(404)
    
    try:
        year = int(request.args.get('year', date.today().year))
        month = int(request.args.get('month', date.today().month))
    except (TypeError, ValueError):
        today = date.today(); year, month = today.year, today.month
        
    current_month_date = date(year, month, 1)
    prev_month_date = current_month_date - timedelta(days=1); next_month_date = (current_month_date + timedelta(days=32)).replace(day=1)
    prev_month = {'year': prev_month_date.year, 'month': prev_month_date.month}; next_month = {'year': next_month_date.year, 'month': next_month_date.month}
    is_future = (year > date.today().year) or (year == date.today().year and month >= date.today().month)
    
    total_by_subject = db.session.query(Subject.name, db.func.sum(StudyLog.duration_minutes).label('total')).join(Subject, StudyLog.subject_id == Subject.id).filter(StudyLog.user_id == user_id).group_by(Subject.name).all()
    last_7_days = db.session.query(StudyLog.date, db.func.sum(StudyLog.duration_minutes).label('total')).filter(StudyLog.user_id == user_id, StudyLog.date >= date.today() - timedelta(days=7)).group_by(StudyLog.date).order_by(StudyLog.date).all()
    
    thresholds = {5: 600, 4: 480, 3: 300, 2: 180, 1: 1} if user.grade == 'ronin' else {5: 300, 4: 180, 3: 120, 2: 60, 1: 1}
    all_logs_rows = db.session.query(StudyLog.date, db.func.sum(StudyLog.duration_minutes).label('total')).filter(StudyLog.user_id == user_id).group_by(StudyLog.date).all()
    heatmap_data = [{"date": row.date.isoformat(), "value": row.total} for row in all_logs_rows]
    study_data = {row.date.isoformat(): row.total for row in all_logs_rows}
    cal = calendar.Calendar(); month_days = cal.monthdatescalendar(year, month)
    calendar_data = []
    for week in month_days:
        week_data = []
        for day in week:
            total_minutes = study_data.get(day.isoformat(), 0); color_level = 0
            for level, minute_req in sorted(thresholds.items(), reverse=True):
                if total_minutes >= minute_req:
                    color_level = level; break
            week_data.append({'date': day, 'total_minutes': total_minutes, 'color_level': color_level})
        calendar_data.append(week_data)
        
    user_subjects_list = [{'id': s.id, 'name': s.name} for s in user.subjects]    
    # app/routes.py の stats 関数内
    # ▼▼▼ 新しいロジック：日毎のログをグループ化する ▼▼▼
    all_logs_details = db.session.query(StudyLog, Subject.name.label('subject_name'))\
        .join(Subject, StudyLog.subject_id == Subject.id)\
        .filter(StudyLog.user_id == user_id)\
        .order_by(StudyLog.date.desc()).all()
    
    logs_by_date = defaultdict(lambda: {'date': None, 'comment': None, 'logs': []})
    for log, subject_name in all_logs_details:
        day_key = log.date.isoformat()
        logs_by_date[day_key]['date'] = log.date
        logs_by_date[day_key]['comment'] = log.comment
        logs_by_date[day_key]['logs'].append({'subject_name': subject_name, 'duration': log.duration_minutes})
    
    # 最近のコメント付きログ10件を抽出
    recent_logs_grouped = [log_group for log_group in logs_by_date.values() if log_group['comment']][:10]

    heatmap_data = [{"date": row.date.isoformat(), "value": row.total} for row in all_logs_rows]


    return render_template(
        'stats.html', user=user,
        subject_labels=[r.name for r in total_by_subject], 
        subject_data=[round(r.total / 60, 1) for r in total_by_subject],
        date_labels=[r.date.isoformat() for r in last_7_days], 
        date_data=[round(r.total / 60, 1) for r in last_7_days],
        calendar_data=calendar_data, month=month, year=year,
        recent_logs_grouped=recent_logs_grouped, user_subjects=user_subjects_list,
        logs_by_date=logs_by_date, prev_month=prev_month, next_month=next_month, is_future=is_future, heatmap_data=heatmap_data
    )

@main_bp.route('/settings/<int:user_id>', methods=['GET', 'POST'])
@login_required
def settings(user_id):
    user = db.session.query(User).get(user_id)
    if not user or user.id != current_user.id: abort(404)
    message, error = None, None

    if request.method == 'POST':
        new_username = request.form.get('username')
        existing_user = db.session.query(User).filter(User.id != user_id, User.username == new_username).first()
        if existing_user:
            error = "そのユーザー名は既に使用されています。"
        else:
            user.username = new_username
            user.grade = request.form.get('grade')
            user.course_type = request.form.get('course_type')
            user.school = request.form.get('school')
            user.faculty = request.form.get('faculty')
            target_exam_date_str = request.form.get('target_exam_date')
            user.target_exam_date = date.fromisoformat(target_exam_date_str) if target_exam_date_str else None
            
            old_subject_ids = {s.id for s in user.subjects}
            new_subject_ids = {int(sid) for sid in request.form.getlist('subjects')}
            subjects_to_remove = old_subject_ids - new_subject_ids
            
            if subjects_to_remove:
                db.session.query(Progress).filter(Progress.user_id == user_id, Progress.subject_id.in_(subjects_to_remove)).delete(synchronize_session=False)
                db.session.query(UserContinuousTaskSelection).filter(UserContinuousTaskSelection.user_id == user_id, UserContinuousTaskSelection.subject_id.in_(subjects_to_remove)).delete(synchronize_session=False)

            user.subjects = [subject for subject in db.session.query(Subject).all() if subject.id in new_subject_ids]
            db.session.commit()
            message = "設定を保存しました。"

    all_subjects = db.session.query(Subject).order_by(Subject.id).all()
    user_subject_ids = {s.id for s in user.subjects}
    return render_template('settings.html', user=user, message=message, error=error, all_subjects=all_subjects, user_subject_ids=user_subject_ids)
    
@main_bp.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    user = db.session.query(User).get(user_id)
    if not user or user.id != current_user.id: abort(404)
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

# --- APIエンドポイント ---
@main_bp.route('/api/universities')
def get_universities():
    query = request.args.get('q', '')
    if not query: return jsonify([])
    search_term = f"{query}%"
    universities = db.session.query(University).filter(db.or_(University.name.like(search_term), University.kana_name.like(search_term))).limit(5).all()
    return jsonify([uni.name for uni in universities])

@main_bp.route('/api/faculties')
def get_faculties():
    university_name = request.args.get('univ', '')
    if not university_name: return jsonify([])
    university = db.session.query(University).filter_by(name=university_name).first()
    if not university: return jsonify([])
    faculties = db.session.query(Faculty).filter_by(university_id=university.id).all()
    return jsonify([fac.name for fac in faculties])

@main_bp.route('/api/update_progress', methods=['POST'])
@login_required
def update_progress():
    data = request.get_json()
    task_id = data.get('task_id'); is_completed = data.get('is_completed'); subject_id_from_request = data.get('subject_id')
    if task_id is None or is_completed is None: return jsonify({'success': False, 'error': 'Missing data'}), 400
    try:
        subject_id = int(subject_id_from_request)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid or missing subject_id'}), 400
    
    progress = db.session.query(Progress).filter_by(user_id=current_user.id, task_id=task_id).first()
    if progress:
        progress.is_completed = 1 if is_completed else 0
    else:
        new_progress = Progress(user_id=current_user.id, task_id=task_id, subject_id=subject_id, is_completed=1 if is_completed else 0)
        db.session.add(new_progress)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/api/select_continuous_task', methods=['POST'])
@login_required
def select_continuous_task():
    data = request.get_json()
    subject_id = data.get('subject_id'); level = data.get('level'); category = data.get('category'); task_id = data.get('task_id')
    if not all([subject_id, level, category, task_id]): return jsonify({'success': False}), 400
    
    selection = db.session.query(UserContinuousTaskSelection).get((current_user.id, subject_id, level, category))
    if selection:
        selection.selected_task_id = task_id
    else:
        new_selection = UserContinuousTaskSelection(user_id=current_user.id, subject_id=subject_id, level=level, category=category, selected_task_id=task_id)
        db.session.add(new_selection)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/api/select_sequential_task', methods=['POST'])
@login_required
def select_sequential_task():
    data = request.get_json()
    group_id = data.get('group_id'); task_id = data.get('task_id')
    if not all([group_id, task_id]): return jsonify({'success': False}), 400
    
    selection = db.session.query(UserSequentialTaskSelection).get((current_user.id, group_id))
    if selection:
        selection.selected_task_id = task_id
    else:
        new_selection = UserSequentialTaskSelection(user_id=current_user.id, group_id=group_id, selected_task_id=task_id)
        db.session.add(new_selection)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/api/log_study_for_date/<int:user_id>', methods=['POST'])
@login_required
def log_study_for_date(user_id):
    if user_id != current_user.id: return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    data = request.get_json()
    date_str = data.get('date'); logs = data.get('logs')
    comment = data.get('comment')
    if not date_str or logs is None: return jsonify({'success': False}), 400
    
    for log_item in logs:
        subject_id = log_item.get('subject_id')
        total_minutes = int(log_item.get('hours', 0)) * 60 + int(log_item.get('minutes', 0))
        if total_minutes > 0:
         new_log = StudyLog(
            user_id=user_id, 
            subject_id=subject_id, 
            date=date.fromisoformat(date_str), 
            duration_minutes=total_minutes,
            comment=comment # ▼▼▼ 全てのログに同じコメントを紐付け ▼▼▼
         )
         db.session.add(new_log)

    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/log/<int:log_id>/delete', methods=['POST'])
@login_required
def delete_log(log_id):
    log = db.session.query(StudyLog).get(log_id)
    if log and log.user_id == current_user.id:
        db.session.delete(log)
        db.session.commit()
    return redirect(url_for('.stats', user_id=current_user.id))

@main_bp.route('/quiz/<int:user_id>')
@login_required
def quiz(user_id):
    if user_id != current_user.id: abort(404)
    return render_template('quiz.html', user=current_user)

@main_bp.route('/quiz/<int:user_id>/submit', methods=['POST'])
@login_required
def submit_quiz(user_id):
    if user_id != current_user.id: abort(404)
    answers = request.form; scores = {'A': 0, 'B': 0, 'C': 0}
    for i in range(1, 11):
        answer = answers.get(f'q{i}')
        if answer in scores: scores[answer] += 1
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_score = sorted_scores[0][1]
    top_types = [k for k, v in scores.items() if v == top_score]
    type_map = {'A': '視覚優位', 'B': '聴覚優位', 'C': '言語感覚優位'}
    if len(top_types) > 1:
        result_type_name = "・".join([type_map[t] for t in top_types]) + "の複合タイプ"
    else: result_type_name = type_map[top_types[0]] + "タイプ"
    current_user.learning_style = result_type_name
    db.session.commit()
    return redirect(url_for('.quiz_results'))

@main_bp.route('/quiz_results')
def quiz_results():
    if not current_user.is_authenticated or not current_user.learning_style:
        return redirect(url_for('.quiz', user_id=current_user.id))
    top_types = []
    result_type_name = current_user.learning_style
    if '視覚' in result_type_name: top_types.append('A')
    if '聴覚' in result_type_name: top_types.append('B')
    if '言語' in result_type_name or '読み書き' in result_type_name: top_types.append('C')
    final_advice, unique_descriptions = [], []
    for type_code in top_types:
        if type_code in results_data:
            if results_data[type_code]['description'] not in unique_descriptions:
                unique_descriptions.append(results_data[type_code]['description'])
            final_advice.extend(results_data[type_code]['advice'])
    final_description = "<br><br>".join(unique_descriptions)
    return render_template('quiz_results.html', user=current_user, result_type=result_type_name, description=final_description, advice=final_advice)
    
@main_bp.route('/quiz/public')
def quiz_public():
    return render_template('quiz.html', is_public=True)

@main_bp.route('/quiz/public/submit', methods=['POST'])
def submit_quiz_public():
    answers = request.form; scores = {'A': 0, 'B': 0, 'C': 0}
    for i in range(1, 11):
        answer = answers.get(f'q{i}')
        if answer in scores: scores[answer] += 1
    top_score = sorted(scores.values(), reverse=True)[0]
    top_types = [k for k, v in scores.items() if v == top_score]
    session['quiz_result_top_types'] = top_types
    return redirect(url_for('.quiz_public_results'))

@main_bp.route('/quiz/public_results')
def quiz_public_results():
    top_types = session.get('quiz_result_top_types', [])
    if not top_types: return redirect(url_for('.quiz_public'))
    type_map = {'A': '視覚優位', 'B': '聴覚優位', 'C': '言語感覚優位'}
    if len(top_types) > 1:
        result_type_name = "・".join([type_map[t] for t in top_types]) + "の複合タイプ"
    else: result_type_name = type_map[top_types[0]] + "タイプ"
    final_advice, unique_descriptions = [], []
    for type_code in top_types:
        if type_code in results_data:
            if results_data[type_code]['description'] not in unique_descriptions:
                unique_descriptions.append(results_data[type_code]['description'])
            final_advice.extend(results_data[type_code]['advice'])
    final_description = "<br><br>".join(unique_descriptions)
    return render_template('quiz_results_public.html', result_type=result_type_name, description=final_description, advice=final_advice)

@main_bp.route('/exams/<int:user_id>', methods=['GET', 'POST'])
@login_required
def mock_exams(user_id):
    if user_id != current_user.id: abort(404)
    if request.method == 'POST':
        exam_name = request.form.get('exam_name'); exam_date_str = request.form.get('exam_date')
        if exam_name and exam_date_str:
            exam_date = date.fromisoformat(exam_date_str)
            new_exam = MockExam(user_id=current_user.id, exam_name=exam_name, exam_date=exam_date)
            db.session.add(new_exam)
            db.session.commit()
            return redirect(url_for('.mock_exams', user_id=current_user.id))
    exams = db.session.query(MockExam).filter_by(user_id=current_user.id).order_by(MockExam.exam_date.asc()).all()
    return render_template('mock_exams.html', user=current_user, exams=exams)

@main_bp.route('/exams/delete/<int:exam_id>', methods=['POST'])
@login_required
def delete_mock_exam(exam_id):
    exam = db.session.query(MockExam).get(exam_id)
    if exam and exam.user_id == current_user.id:
        db.session.delete(exam)
        db.session.commit()
    return redirect(url_for('.mock_exams', user_id=current_user.id))



# ... (既存のimport文) ...
import requests
from bs4 import BeautifulSoup
import os
import google.generativeai as genai
import json
import re
from datetime import date, datetime
from urllib.parse import urljoin
import ssl
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
from urllib3.util.ssl_ import create_urllib3_context

# --- 共通ヘルパー (変更なし) ---
class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
        self.poolmanager = PoolManager(
            ssl_context=ssl_context, num_pools=connections, maxsize=maxsize,
            block=block, **pool_kwargs)

def _get_legacy_session():
    """古いSSLリネゴシエーションを許可するrequests.Sessionオブジェクトを作成する"""
    session = requests.Session()
    session.mount("https://", LegacySSLAdapter())
    return session
# --- AIの役割定義 (思考ルーチンを強化) ---

def _is_link_a_mock_exam(link_text: str, link_url: str) -> bool:
    """【鑑定士AI - 強化版】与えられたリンクが模試詳細ページらしいか、より厳しく判定する"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        以下のHTMLリンクは、特定の大学受験模試（例：「第1回全統共通テスト模試」）の詳細・申込ページへのリンクですか？
        一般的な案内ページ（例：「模試一覧」「お申し込み方法」）や、模試と無関係なページは「いいえ」と判断してください。
        「はい」か「いいえ」だけで答えてください。
        リンクテキスト: "{link_text}"
        リンクURL: "{link_url}"
        """
        response = model.generate_content(prompt, request_options={'timeout': 20})
        return "はい" in response.text
    except Exception:
        return False

def _extract_exam_details_with_ai(url: str, provider: str):
    """【書記AI - 強化版】詳細ページから文脈を読んで模試の情報をJSONで抽出する"""
    session = requests.Session()
    session.mount("https://", LegacySSLAdapter())
    response = session.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    page_text = ' '.join(soup.get_text().split())[:8000]

    model = genai.GenerativeModel('gemini-1.5-flash')
    today = date.today().isoformat()
    prompt = f"""
    あなたはWebページから日本の大学受験模試の情報を抽出するエキスパートです。今日の日付は{today}です。
    以下のテキストから、以下の項目を抽出してください。
    - name: 模試の正式名称。「{provider}」という単語は含めないでください。
    - target_grade: 対象学年（例：「高3・卒」）。
    - exam_date: 実施日。
    - app_start_date: 申込開始日。
    - app_end_date: 申込締切日。
    
    重要：
    - 日付は必ず「YYYY-MM-DD」形式にしてください。
    - 実施日は、今日以降の最も可能性の高い日付を選んでください。
    - 申込開始日と締切日は、「申込期間」などのキーワードの近くにある日付を優先してください。
    - 情報が見つからない項目はnullにしてください。
    - 結果は必ずJSON形式 {{"name": ..., "exam_date": ...}} で返してください。

    テキスト：
    {page_text}
    """
    
    ai_response = model.generate_content(prompt, request_options={'timeout': 40})
    json_text_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response.text, re.DOTALL)
    if not json_text_match:
        raise ValueError("AI did not return a valid JSON block.")
    return json.loads(json_text_match.group(1))



@main_bp.route('/api/update_continuous_tasks/<int:user_id>', methods=['POST'])
@login_required
def update_continuous_tasks(user_id):
    if user_id != current_user.id:
        abort(403)
    
    data = request.get_json()
    level = data.get('level')
    selections = data.get('selections') # { "英単語": "task_id_1", "英文法": "task_id_2" }

    if not level or selections is None:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    # このレベル・カテゴリの古い選択を一度削除
    categories_to_update = list(selections.keys())
    db.session.query(UserContinuousTaskSelection).filter(
        UserContinuousTaskSelection.user_id == user_id,
        UserContinuousTaskSelection.level == level,
        UserContinuousTaskSelection.category.in_(categories_to_update)
    ).delete(synchronize_session=False)

    # 新しい選択を追加
    subject_ids = {s.id for s in current_user.subjects} # ユーザーの科目IDを取得
    for category, task_id in selections.items():
        if task_id: # 選択がある場合のみ
             # subject_idを見つけるロジック(簡易版、要改善の可能性あり)
            book = db.session.query(Book).filter_by(task_id=task_id).first()
            route_step = db.session.query(RouteStep).filter_by(book_id=book.id).first()
            route = db.session.query(Route).get(route_step.route_id)
            subject_id = route.subject_id
            
            if subject_id in subject_ids:
                new_selection = UserContinuousTaskSelection(
                    user_id=user_id, 
                    subject_id=subject_id, 
                    level=level, 
                    category=category, 
                    selected_task_id=task_id
                )
                db.session.add(new_selection)
    
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        # AJAXリクエストの処理
        data = request.get_json()
        message = data.get('message')

        if not message:
            return jsonify({'success': False, 'error': 'お問い合わせ内容を入力してください。'}), 400
        
        new_inquiry = Inquiry(
            user_id=current_user.id,
            name=current_user.username,
            email=f"user_id:{current_user.id}",
            message=message
        )
        db.session.add(new_inquiry)
        db.session.commit()
        return jsonify({'success': True, 'message': 'お問い合わせいただき、ありがとうございます！'})
            
    # GETリクエスト（通常のページ表示）
    return render_template('contact.html', user=current_user)


@main_bp.route('/faq')
def faq_list():
    faqs = db.session.query(FAQ).order_by(FAQ.sort_order).all()
    return render_template('faq.html', faqs=faqs, user=current_user)



@main_bp.route('/inbox')
@login_required
def inbox():
    # ユーザーに関連する全てのお問い合わせと、それに対する返信を取得
    inquiries = db.session.query(Inquiry).filter_by(user_id=current_user.id).order_by(Inquiry.created_at.desc()).all()
    return render_template('inbox.html', inquiries=inquiries, user=current_user)

@main_bp.route('/api/reply/<int:reply_id>/read', methods=['POST'])
@login_required
def mark_reply_as_read(reply_id):
    reply = db.session.query(Reply).join(Inquiry).filter(
        Reply.id == reply_id,
        Inquiry.user_id == current_user.id
    ).first_or_404()
    
    reply.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/exams/<int:exam_id>/results', methods=['GET', 'POST'])
@login_required
def edit_exam_results(exam_id):
    exam = db.session.query(MockExam).filter_by(id=exam_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        for subject in current_user.subjects:
            result = db.session.query(MockExamResult).filter_by(
                mock_exam_id=exam_id, 
                subject_id=subject.id
            ).first()

            # フォームからデータが送られてきていれば、新しい結果として作成または更新
            if f'score_{subject.id}' in request.form:
                if not result:
                    result = MockExamResult(mock_exam_id=exam_id, subject_id=subject.id)
                    db.session.add(result)
                
                result.score = int(request.form[f'score_{subject.id}']) if request.form[f'score_{subject.id}'] else None
                result.max_score = int(request.form[f'max_score_{subject.id}']) if request.form[f'max_score_{subject.id}'] else None
                result.deviation = float(request.form[f'deviation_{subject.id}']) if request.form[f'deviation_{subject.id}'] else None
                result.ranking = request.form[f'ranking_{subject.id}'] if request.form[f'ranking_{subject.id}'] else None

        db.session.commit()
        flash('模試の結果を保存しました。')
        return redirect(url_for('.mock_exams', user_id=current_user.id))

    # 既存の結果を辞書としてテンプレートに渡す
    existing_results = {res.subject_id: res for res in exam.results}
    return render_template('exam_results_form.html', user=current_user, exam=exam, results=existing_results)

@main_bp.route('/privacy')
def privacy_policy():
    return render_template('privacy.html', user=current_user)

@main_bp.route('/terms')
def terms_of_service():
    return render_template('terms.html', user=current_user)

@main_bp.route('/about')
def about():
    return render_template('about.html', user=current_user)

# app/routes/main.py の一番下に追加

@main_bp.route('/exams/<int:exam_id>/results', methods=['GET', 'POST'])
@login_required
def edit_exam_results(exam_id):
    exam = db.session.query(MockExam).filter_by(id=exam_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        # フォームから送信された科目ごとの結果を処理
        for subject in current_user.subjects:
            result = db.session.query(MockExamResult).filter_by(
                mock_exam_id=exam_id, 
                subject_id=subject.id
            ).first()

            # フォームからデータが送られてきていれば、新しい結果として作成または更新
            if f'score_{subject.id}' in request.form:
                if not result:
                    result = MockExamResult(mock_exam_id=exam_id, subject_id=subject.id)
                    db.session.add(result)
                
                # 空欄の場合はNone(NULL)を、そうでなければ数値に変換して保存
                result.score = int(request.form[f'score_{subject.id}']) if request.form[f'score_{subject.id}'] else None
                result.max_score = int(request.form[f'max_score_{subject.id}']) if request.form[f'max_score_{subject.id}'] else None
                result.deviation = float(request.form[f'deviation_{subject.id}']) if request.form[f'deviation_{subject.id}'] else None
                result.ranking = request.form[f'ranking_{subject.id}'] if request.form[f'ranking_{subject.id}'] else None

        db.session.commit()
        flash('模試の結果を保存しました。')
        return redirect(url_for('.mock_exams', user_id=current_user.id))

    # GETリクエストの場合：既存の結果を辞書としてテンプレートに渡す
    existing_results = {res.subject_id: res for res in exam.results}
    return render_template('exam_results_form.html', user=current_user, exam=exam, results=existing_results)
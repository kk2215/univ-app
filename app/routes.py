import sqlite3
import calendar
from datetime import date, datetime, timedelta # 変更済みのimport

from flask import (
    Blueprint, render_template, request, redirect, url_for, jsonify, session, current_app
)
from collections import defaultdict
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User # <- 関数の先頭でUserモデルをインポート

bp = Blueprint('main', __name__)

# 結果とアドバイスのテキスト
results_data = {
        'A': {
            'description': 'あなたは、目で見た情報を処理するのが得意なタイプです。図やグラフ、イラスト、色分けされた情報、映像などを通して物事を理解し、記憶することに長けています。',
            'advice': [
                '<strong>参考書選び:</strong> 解説文だけでなく、図やイラスト、写真が豊富な参考書を選びましょう。特に地理や歴史、理科の資料集はあなたの強力な武器になります。',
                '<strong>映像授業の活用:</strong> 文字を読むだけでなく、講師の動きや板書を視覚的に捉えられる映像授業は非常に効果的です。',
                '<strong>ノート術:</strong> 重要なポイントを色分けしたり、情報の関係性を矢印や図でまとめたりすると、記憶に定着しやすくなります。',
                '<strong>暗記の工夫:</strong> 英単語はイラスト付きの単語帳を使ったり、歴史上の人物は肖像画とセットで覚えたりするなど、常にビジュアルと結びつけることを意識しましょう。'
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

def get_db_connection():
    connection = sqlite3.connect(current_app.config['DATABASE'])
    connection.row_factory = sqlite3.Row
    return connection

@bp.route('/')
def index():
    return render_template('index.html')

# app/routes.py の register 関数をこちらに置き換えてください

@bp.route('/register', methods=['GET', 'POST'])
def register():
    connection = get_db_connection()
    cursor = connection.cursor()
    error_message = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        grade = request.form.get('grade')
        course_type = request.form.get('course_type')
        school = request.form.get('school')
        faculty = request.form.get('faculty')
        prefecture = request.form.get('prefecture')
        target_exam_date = request.form.get('target_exam_date')
        
        # starting_level をフォームから取得
        starting_level = request.form.get('starting_level')

        user_exists = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

        if not all([username, password, password_confirm, grade, course_type, school, faculty, starting_level]):
            error_message = "全ての必須項目を入力してください。"
        elif password != password_confirm:
            error_message = "パスワードが一致しません。"
        elif user_exists:
            error_message = "そのユーザー名は既に使用されています。"
        
        if error_message is None:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            plan_type = 'standard'
            
            # ▼▼▼ [修正点] INSERT文に starting_level を追加 ▼▼▼
            cursor.execute(
                'INSERT INTO users (username, password_hash, grade, course_type, school, faculty, plan_type, prefecture, target_exam_date, starting_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (username, password_hash, grade, course_type, school, faculty, plan_type, prefecture, target_exam_date, starting_level)
            )
            user_id = cursor.lastrowid

            subject_ids = request.form.getlist('subjects')
            for subject_id in subject_ids:
                cursor.execute('INSERT INTO user_subjects (user_id, subject_id) VALUES (?, ?)', (user_id, subject_id))
                # 科目ごとの開始レベルを登録 (この部分は元から正しく動いているはずです)
                start_level = request.form.get(f'start_level_{subject_id}', starting_level) # デフォルト値を全体の開始レベルにする
                cursor.execute('INSERT INTO user_subject_levels (user_id, subject_id, start_level) VALUES (?, ?, ?)', (user_id, subject_id, start_level))
            
            connection.commit()
            session['user_id'] = user_id
            connection.close()
            return redirect(url_for('main.dashboard', user_id=user_id))

    subjects = cursor.execute('SELECT * FROM subjects ORDER BY id').fetchall()
    connection.close()
    return render_template('register.html', subjects=subjects, error=error_message)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        connection = get_db_connection()
        user = connection.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        connection.close()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('main.dashboard', user_id=user['id']))
        else:
            error_message = "ユーザー名またはパスワードが正しくありません。"
    
    return render_template('login.html', error=error_message)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@bp.route('/plan/<int:user_id>')
def show_plan(user_id):
    connection = get_db_connection()
    user = User.query.get(user_id)
    if not user:
        connection.close(); return "ユーザーが見つかりません", 404

    target_school_level_row = connection.execute('SELECT level FROM universities WHERE name = ?', (user['school'],)).fetchone()
    target_level_name = target_school_level_row['level'] if target_school_level_row else None
    level_hierarchy = { '基礎徹底レベル': 0, '高校入門レベル': 0, '日東駒専レベル': 1, '産近甲龍': 1, 'MARCHレベル': 2, '関関同立': 2, '早慶レベル': 3, '早稲田レベル': 3, '難関国公立・東大・早慶レベル': 3, '特殊形式': 98 }
    target_level_value = level_hierarchy.get(target_level_name, 99)
    
    start_level_rows = connection.execute('SELECT subject_id, start_level FROM user_subject_levels WHERE user_id = ?', (user_id,)).fetchall()
    start_levels_map = {row['subject_id']: row['start_level'] for row in start_level_rows}
    user_subject_ids = [row['subject_id'] for row in connection.execute('SELECT subject_id FROM user_subjects WHERE user_id = ?', (user_id,)).fetchall()]
    subjects_map = {row['id']: row['name'] for row in connection.execute('SELECT id, name FROM subjects').fetchall()}
    subject_ids_map = {v: k for k, v in subjects_map.items()}
    
    cont_selections_rows = connection.execute('SELECT subject_id, level, category, selected_task_id FROM user_continuous_task_selections WHERE user_id = ?', (user_id,)).fetchall()
    user_selections = {(row['subject_id'], row['level'], row['category']): row['selected_task_id'] for row in cont_selections_rows}
    
    seq_selections_rows = connection.execute('SELECT group_id, selected_task_id FROM user_sequential_task_selections WHERE user_id = ?', (user_id,)).fetchall()
    sequential_selections = {row['group_id']: row['selected_task_id'] for row in seq_selections_rows}
    
    completed_tasks_set = {row['task_id'] for row in connection.execute('SELECT task_id FROM progress WHERE user_id = ? AND is_completed = 1', (user_id,)).fetchall()}
    strategies = {row['subject_id']: row['strategy_html'] for row in connection.execute('SELECT subject_id, strategy_html FROM subject_strategies').fetchall()}
    
    plan_by_subject_level = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    continuous_tasks_by_subject_level_category = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for subject_id in user_subject_ids:
        subject_name = subjects_map.get(subject_id)
        
        # ▼▼▼ [修正点] SQLのORDER BY句で、レベルの難易度順に並べ替える ▼▼▼
        order_by_clause = """
        ORDER BY
            CASE rs.level
                WHEN '基礎徹底レベル' THEN 1
                WHEN '高校入門レベル' THEN 2
                WHEN '日東駒専レベル' THEN 3
                WHEN '産近甲龍' THEN 3
                WHEN 'MARCHレベル' THEN 4
                WHEN '関関同立' THEN 4
                WHEN '早慶レベル' THEN 5
                WHEN '早稲田レベル' THEN 5
                WHEN '難関国公立・東大・早慶レベル' THEN 5
                WHEN '特殊形式' THEN 98
                ELSE 99
            END,
            rs.step_order
        """
        
        base_query = "SELECT s.name AS subject_name, b.task_id, b.title AS book, b.description, b.youtube_query, b.task_type, rs.level, rs.category, rs.is_main, b.duration_weeks FROM routes r JOIN route_steps rs ON r.id = rs.route_id JOIN books b ON rs.book_id = b.id JOIN subjects s ON r.subject_id = s.id"
        if subject_name == '数学':
            route_name = 'math_rikei_standard' if user['course_type'] == 'science' else 'math_bunkei_standard'
            query = f"{base_query} WHERE r.name = ? {order_by_clause};"
            params = (route_name,)
        else:
            query = f"{base_query} WHERE r.plan_type = 'standard' AND r.subject_id = ? {order_by_clause};"
            params = (subject_id,)
        
        subject_plan = [dict(row) for row in connection.execute(query, params).fetchall()]

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
                exam_date = date.fromisoformat(user['target_exam_date']) if user['target_exam_date'] else date(today.year + 1, 2, 25)
                
                task_groups = []
                temp_group = []
                for task in sequential_tasks:
                    if task['is_main'] == 1 and temp_group:
                        task_groups.append(temp_group)
                        temp_group = []
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
    
    connection.close()
    
    return render_template(
        'plan.html', 
        user=user, 
        plan_data=plan_by_subject_level, 
        continuous_tasks_data=continuous_tasks_by_subject_level_category,
        user_selections=user_selections,
        sequential_selections=sequential_selections,
        title="学習マップ", 
        completed_tasks=completed_tasks_set,
        strategies=strategies,
        subject_ids_map=subject_ids_map
    )

@bp.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    connection = get_db_connection()
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        connection.close()
        return "ユーザーが見つかりません", 404

    # --- 1. 必要なデータをまとめて取得 ---
    university = connection.execute('SELECT * FROM universities WHERE name = ?', (user['school'],)).fetchone()
    days_until_exam = "未設定"
    if user['target_exam_date']:
        exam_date = date.fromisoformat(user['target_exam_date'])
        today = date.today()
        days_until_exam = (exam_date - today).days

    subjects_map = {row['id']: row['name'] for row in connection.execute('SELECT id, name FROM subjects').fetchall()}
    user_subject_ids = [row['subject_id'] for row in connection.execute('SELECT subject_id FROM user_subjects WHERE user_id = ?', (user_id,)).fetchall()]
    completed_tasks_set = {row['task_id'] for row in connection.execute('SELECT task_id FROM progress WHERE user_id = ? AND is_completed = 1', (user_id,)).fetchall()}
    
    cont_selections_rows = connection.execute('''
        SELECT sel.subject_id, sel.level, sel.category, sel.selected_task_id, b.title
        FROM user_continuous_task_selections sel JOIN books b ON sel.selected_task_id = b.task_id
        WHERE sel.user_id = ?
    ''', (user_id,)).fetchall()
    cont_selections = [dict(row) for row in cont_selections_rows]

    seq_selections_rows = connection.execute('SELECT group_id, selected_task_id FROM user_sequential_task_selections WHERE user_id = ?', (user_id,)).fetchall()
    seq_selections = {row['group_id']: row['selected_task_id'] for row in seq_selections_rows}

    # --- 2. 科目ごとにループし、表示データを生成 ---
    dashboard_data = []
    for subject_id in user_subject_ids:
        subject_name = subjects_map.get(subject_id)
        subject_info = {'name': subject_name, 'next_task': None, 'continuous_tasks': [], 'progress': 0, 'last_completed_task': None, 'pending_selections': []}
        
        base_query = "SELECT b.task_id, b.title, b.youtube_query, b.task_type, rs.level, rs.category, rs.is_main FROM routes r JOIN route_steps rs ON r.id = rs.route_id JOIN books b ON rs.book_id = b.id JOIN subjects s ON r.subject_id = s.id"
        if subject_name == '数学':
            route_name = 'math_rikei_standard' if user['course_type'] == 'science' else 'math_bunkei_standard'
            query = f"{base_query} WHERE r.name = ? ORDER BY rs.step_order;"
            params = (route_name,)
        else:
            query = f"{base_query} WHERE r.plan_type = 'standard' AND r.subject_id = ? ORDER BY rs.step_order;"
            params = (subject_id,)
        full_plan = [dict(row) for row in connection.execute(query, params).fetchall()]
        
        current_level = None
        if full_plan:
            # a) Sequentialタスクの処理
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

                # 「次のタスク」を決定
                for group in task_groups:
                    group_id = next((t['task_id'] for t in group if t['is_main']), group[0]['task_id'])
                    actual_task_id = seq_selections.get(group_id, group_id)
                    if actual_task_id not in completed_tasks_set:
                        if len(group) > 1 and group_id not in seq_selections:
                            subject_info['next_task'] = {'is_choice_pending': True, 'title': f"『{group[0]['category']}』の参考書を選択してください", 'subject_name': subject_name}
                        else:
                            subject_info['next_task'] = next((t for t in group if t['task_id'] == actual_task_id), group[0])
                        break
                
                # 「現在のレベル」を決定
                if subject_info['next_task']:
                    if isinstance(subject_info['next_task'], dict) and subject_info['next_task'].get('is_choice_pending'):
                        # 選択待ちの場合、最後に完了したタスクのレベルを現在レベルと見なす
                        plan_task_ids_in_groups_for_level = [seq_selections.get(next((t['task_id'] for t in g if t['is_main']), g[0]['task_id']), g[0]['task_id']) for g in task_groups]
                        completed_in_plan_for_level = [task_id for task_id in plan_task_ids_in_groups_for_level if task_id in completed_tasks_set]
                        if completed_in_plan_for_level:
                            last_completed_id = completed_in_plan_for_level[-1]
                            last_task_in_plan = next((t for t in sequential_plan if t['task_id'] == last_completed_id), None)
                            current_level = last_task_in_plan['level'] if last_task_in_plan else None
                        else:
                            current_level = sequential_plan[0]['level'] if sequential_plan else None
                    else:
                        current_level = subject_info['next_task']['level']
                
                # 進捗と直前タスクを計算
                plan_task_ids_in_groups = [seq_selections.get(next((t['task_id'] for t in g if t['is_main']), g[0]['task_id']), g[0]['task_id']) for g in task_groups]
                completed_in_plan = [task_id for task_id in plan_task_ids_in_groups if task_id in completed_tasks_set]
                if completed_in_plan:
                    last_completed_id = completed_in_plan[-1]
                    subject_info['last_completed_task'] = connection.execute('SELECT * FROM books WHERE task_id = ?', (last_completed_id,)).fetchone()
                subject_info['progress'] = int((len(completed_in_plan) / len(task_groups)) * 100) if task_groups else 0

            # b) Continuousタスクの処理
            continuous_tasks_in_plan = [task for task in full_plan if task['task_type'] == 'continuous' and task['category'] != '補助教材']
            tasks_to_display = []
            
            tasks_by_category = defaultdict(list)
            for task in continuous_tasks_in_plan:
                tasks_by_category[task['category']].append(task)
            
            for category, tasks in tasks_by_category.items():
                if category == '漢字':
                    if tasks: tasks_to_display.append({'title': tasks[0]['title']})
                    continue

                if not current_level: continue

                tasks_in_current_level = [t for t in tasks if t['level'] == current_level]
                if not tasks_in_current_level: continue

                user_selection = next((s for s in cont_selections if s['subject_id'] == subject_id and s['level'] == current_level and s['category'] == category), None)

                if len(tasks_in_current_level) > 1: # 選択肢あり
                    if user_selection:
                        tasks_to_display.append({'title': user_selection['title']})
                    else:
                        subject_info['pending_selections'].append(f"{current_level}の{category}")
                else: # 選択肢なし
                    tasks_to_display.append({'title': tasks_in_current_level[0]['title']})

            subject_info['continuous_tasks'] = tasks_to_display
        dashboard_data.append(subject_info)

    connection.close()
    return render_template('dashboard.html', user=user, university=university, days_until_exam=days_until_exam, dashboard_data=dashboard_data)


@bp.route('/support/<int:user_id>')
def support(user_id):
    connection = get_db_connection()
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    connection.close()

    if not user:
        return "ユーザーが見つかりません", 404

    support_data = {
        "東京都": [
            {"name": "受験生チャレンジ支援貸付事業", "description": "塾代や受験費用を無利子で借りられ、入学すれば返済が免除される場合があります。"},
            {"name": "東京都育英資金", "description": "高校・大学等の学費を無利子で借りられる奨学金制度です。"}
        ],
        "大阪府": [
            {"name": "塾代助成事業", "description": "所得制限等に応じて、塾代に利用できるクーポンが支給されます。"},
            {"name": "大阪府育英会奨学金", "description": "高校・大学等の学費を無利子で借りられる奨学金制度です。"}
        ]
    }
    
    user_support = support_data.get(user['prefecture'], [])
    return render_template('support.html', user=user, support_list=user_support)

@bp.route('/weakness/add/<int:user_id>', methods=['GET', 'POST'])
def add_weakness(user_id):
    connection = get_db_connection()
    if request.method == 'POST':
        topic = request.form['topic']
        exists = connection.execute('SELECT id FROM weaknesses WHERE user_id = ? AND topic = ?', (user_id, topic)).fetchone()
        if not exists:
            connection.execute('INSERT INTO weaknesses (user_id, topic) VALUES (?, ?)', (user_id, topic))
            connection.commit()
        connection.close()
        return redirect(url_for('main.show_plan', user_id=user_id))
    
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    connection.close()
    return render_template('add_weakness.html', user=user)


@bp.route('/update_progress', methods=['POST'])
def update_progress():
    # ユーザーがログインしているか確認
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    task_id = data.get('task_id')
    is_completed = data.get('is_completed')

    if task_id is None or is_completed is None:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    connection = get_db_connection()
    exists = connection.execute('SELECT id FROM progress WHERE user_id = ? AND task_id = ?', (user_id, task_id)).fetchone()
    
    if exists:
        connection.execute('UPDATE progress SET is_completed = ? WHERE user_id = ? AND task_id = ?', (1 if is_completed else 0, user_id, task_id))
    else:
        connection.execute('INSERT INTO progress (user_id, task_id, is_completed) VALUES (?, ?, ?)', (user_id, task_id, 1 if is_completed else 0))

    connection.commit()
    connection.close()
    
    # redirectではなく、JSON形式で成功を返す
    return jsonify({'success': True})

# app/routes.py の get_universities 関数をこちらに置き換えてください

@bp.route('/api/universities')
def get_universities():
    # ユーザーが入力した検索キーワードを取得します (例: 'あ', 'わせだ')
    query = request.args.get('q', '')
    
    # 検索キーワードが空の場合は、空のリストを返します
    if not query:
        return jsonify([])

    # データベースに接続します
    connection = get_db_connection()
    
    # SQLのLIKE検索で使うために、キーワードの後ろに「%」を付けます
    # これで「前方一致検索」(例: 'あ'で始まる大学名) が可能になります
    search_term = f"{query}%"
    
    # データベースに直接、前方一致する大学を問い合わせます
    # name (漢字名) と kana_name (ふりがな) の両方を検索対象にします
    # LIMIT 5 で、候補を最大5件に絞り込みます
    universities = connection.execute(
        'SELECT name FROM universities WHERE name LIKE ? OR kana_name LIKE ? LIMIT 5',
        (search_term, search_term)
    ).fetchall()
    
    connection.close()
    
    # 結果をJSON形式でフロントエンド（ブラウザ）に返します
    # [row['name'] for row in universities] は、取得したデータから大学名だけを抜き出してリストを作成する処理です
    return jsonify([row['name'] for row in universities])

@bp.route('/api/faculties')
def get_faculties():
    university_name = request.args.get('univ', '')
    if not university_name:
        return jsonify([])

    connection = get_db_connection()
    faculties = connection.execute('''
        SELECT f.name FROM faculties f
        JOIN universities u ON f.university_id = u.id
        WHERE u.name = ?
    ''', (university_name,)).fetchall()
    connection.close()
    return jsonify([row['name'] for row in faculties])

# app/routes.py の末尾に追記

@bp.route('/quiz/<int:user_id>')
def quiz(user_id):
    connection = get_db_connection()
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    connection.close()
    return render_template('quiz.html', user=user)

@bp.route('/quiz/<int:user_id>/submit', methods=['POST'])
def submit_quiz(user_id):
    answers = request.form
    scores = {'A': 0, 'B': 0, 'C': 0}
    for i in range(10):
        answer = answers.get(f'q{i}')
        if answer in scores:
            scores[answer] += 1

    # スコアを降順にソート
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    
    top_score = sorted_scores[0][1]
    second_score = sorted_scores[1][1]
    
    # 最もスコアが高いタイプを全て取得
    top_types = [k for k, v in scores.items() if v == top_score]
    
    result_type_name = ""
    type_map = {'A': '視覚', 'B': '聴覚', 'C': '言語'}

    if len(top_types) > 1:
        # 同点の場合 (複合タイプ)
        result_type_name = "・".join([type_map[t] for t in top_types]) + "優位の複合タイプ"
    elif top_score - second_score >= 3:
        # 圧勝の場合 (単独優位タイプ)
        result_type_name = type_map[top_types[0]] + "優位タイプ"
    else:
        # 僅差の場合 (バランスタイプ)
        result_type_name = f"バランスタイプ（{type_map[top_types[0]]}優位）"
    
    # 結果とアドバイスのテキスト
    results_data = {
        'A': {
            'description': 'あなたは、目で見た情報を処理するのが得意なタイプです。図やグラフ、イラスト、色分けされた情報、映像などを通して物事を理解し、記憶することに長けています。',
            'advice': [
                '<strong>参考書選び:</strong> 解説文だけでなく、図やイラスト、写真が豊富な参考書を選びましょう。特に地理や歴史、理科の資料集はあなたの強力な武器になります。',
                '<strong>映像授業の活用:</strong> 文字を読むだけでなく、講師の動きや板書を視覚的に捉えられる映像授業は非常に効果的です。',
                '<strong>ノート術:</strong> 重要なポイントを色分けしたり、情報の関係性を矢印や図でまとめたりすると、記憶に定着しやすくなります。',
                '<strong>暗記の工夫:</strong> 英単語はイラスト付きの単語帳を使ったり、歴史上の人物は肖像画とセットで覚えたりするなど、常にビジュアルと結びつけることを意識しましょう。'
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
    
    # 診断結果をDBに保存
    connection = get_db_connection()
    connection.execute('UPDATE users SET learning_style = ? WHERE id = ?', (result_type_name, user_id))
    connection.commit()
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    connection.close()

    # 複合タイプの場合は、該当するアドバイスをすべて表示
    final_advice = []
    final_description = ""
    for type_code in top_types:
        final_description += results_data[type_code]['description'] + "<br><br>"
        final_advice.extend(results_data[type_code]['advice'])

    return render_template('quiz_results.html', user=user, result_type=result_type_name, description=final_description, advice=final_advice)

# app/routes.py の末尾に追記

@bp.route('/quiz_results/<int:user_id>')
def quiz_results(user_id):
    connection = get_db_connection()
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    connection.close()

    if not user or not user['learning_style']:
        return redirect(url_for('main.quiz', user_id=user_id))

    result_type_name = user['learning_style']
    
   # 保存された結果の文字列から、該当するタイプを全て抽出する
    top_types = []
    if '視覚' in result_type_name:
        top_types.append('A')
    if '聴覚' in result_type_name:
        top_types.append('B')
    if '言語' in result_type_name or '読み書き' in result_type_name:
        top_types.append('C')

    final_advice = []
    final_description = ""
    unique_descriptions = []
    
    for type_code in top_types:
        if type_code in results_data:
            # 同じ説明文が重複しないように追加
            if results_data[type_code]['description'] not in unique_descriptions:
                unique_descriptions.append(results_data[type_code]['description'])
                final_description += results_data[type_code]['description'] + "<br><br>"
            final_advice.extend(results_data[type_code]['advice'])
            
    return render_template('quiz_results.html', user=user, result_type=result_type_name, description=final_description, advice=final_advice)

@bp.route('/api/hide_task', methods=['POST'])
def hide_task():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    task_id = request.json.get('task_id')
    if not task_id:
        return jsonify({'success': False, 'error': 'Task ID is missing'}), 400

    connection = get_db_connection()
    connection.execute('INSERT OR IGNORE INTO user_hidden_tasks (user_id, task_id) VALUES (?, ?)', (user_id, task_id))
    connection.commit()
    connection.close()
    return jsonify({'success': True})

# app/routes.py の settings 関数を置き換え
@bp.route('/settings/<int:user_id>', methods=['GET', 'POST'])
def settings(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('main.login'))

    connection = get_db_connection()
    message = None
    error = None

    if request.method == 'POST':
        # フォームから送信されたデータを取得して更新する
        username = request.form.get('username')
        grade = request.form.get('grade')
        school = request.form.get('school')
        faculty = request.form.get('faculty')
        target_exam_date = request.form.get('target_exam_date')
        
        # 必須項目が空でないかチェック
        if not all([username, grade, school, faculty]):
            error = "ユーザー名、学年、志望校、志望学部は必須項目です。"
            # エラー発生時でもページを再表示するために必要なデータを全て取得する
            user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            all_subjects = connection.execute('SELECT * FROM subjects ORDER BY id').fetchall()
            user_subjects_rows = connection.execute('SELECT subject_id FROM user_subjects WHERE user_id = ?', (user_id,)).fetchall()
            user_subject_ids = {row['subject_id'] for row in user_subjects_rows}
            start_level_rows = connection.execute('SELECT subject_id, start_level FROM user_subject_levels WHERE user_id = ?', (user_id,)).fetchall()
            user_start_levels = {row['subject_id']: row['start_level'] for row in start_level_rows}
            level_options = {0: '中学レベルから', 1: '日東駒専レベルから', 2: 'MARCHレベルから'}
            connection.close()
            
            return render_template(
                'settings.html', user=user, error=error, all_subjects=all_subjects, 
                user_subject_ids=user_subject_ids, user_start_levels=user_start_levels, 
                level_options=level_options
            )
            
        connection.execute(
            'UPDATE users SET username = ?, grade = ?, school = ?, faculty = ?, target_exam_date = ? WHERE id = ?',
            (username, grade, school, faculty, target_exam_date, user_id)
        )
        
        new_subject_ids = request.form.getlist('subjects')
        connection.execute('DELETE FROM user_subjects WHERE user_id = ?', (user_id,))
        connection.execute('DELETE FROM user_subject_levels WHERE user_id = ?', (user_id,))
        for subject_id in new_subject_ids:
            connection.execute('INSERT INTO user_subjects (user_id, subject_id) VALUES (?, ?)', (user_id, int(subject_id)))
            start_level = request.form.get(f'start_level_{subject_id}', 1)
            connection.execute('INSERT INTO user_subject_levels (user_id, subject_id, start_level) VALUES (?, ?, ?)', (user_id, int(subject_id), int(start_level)))
        
        connection.commit()
        message = "設定を保存しました。"

    # ページを表示するために必要なデータを取得する
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    all_subjects = connection.execute('SELECT * FROM subjects ORDER BY id').fetchall()
    user_subjects_rows = connection.execute('SELECT subject_id FROM user_subjects WHERE user_id = ?', (user_id,)).fetchall()
    user_subject_ids = {row['subject_id'] for row in user_subjects_rows}
    start_level_rows = connection.execute('SELECT subject_id, start_level FROM user_subject_levels WHERE user_id = ?', (user_id,)).fetchall()
    user_start_levels = {row['subject_id']: row['start_level'] for row in start_level_rows}
    
    level_options = {0: '中学レベルから', 1: '日東駒専レベルから', 2: 'MARCHレベルから'}

    connection.close()

    return render_template(
        'settings.html', 
        user=user, 
        message=message, 
        error=error,
        all_subjects=all_subjects, 
        user_subject_ids=user_subject_ids,
        user_start_levels=user_start_levels,
        level_options=level_options
    )
    
@bp.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
def change_password(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('main.login'))

    connection = get_db_connection()
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    error = None
    message = None

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(user['password_hash'], current_password):
            error = "現在のパスワードが正しくありません。"
        elif new_password != confirm_password:
            error = "新しいパスワードが一致しません。"
        elif not new_password:
            error = "新しいパスワードを入力してください。"
        else:
            password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            connection.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
            connection.commit()
            message = "パスワードが正常に変更されました。"

    connection.close()
    return render_template('change_password.html', user=user, error=error, message=message)

# app/routes.py の select_continuous_task 関数をこちらに置き換え

@bp.route('/api/select_continuous_task', methods=['POST'])
def select_continuous_task():
    user_id = session.get('user_id')
    if not user_id: return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    subject_id = data.get('subject_id')
    level = data.get('level')
    category = data.get('category')
    task_id = data.get('task_id')

    if not all([subject_id, level, category, task_id]):
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    connection = get_db_connection()
    connection.execute('''
        INSERT INTO user_continuous_task_selections (user_id, subject_id, level, category, selected_task_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, subject_id, level, category) DO UPDATE SET
        selected_task_id = excluded.selected_task_id;
    ''', (user_id, subject_id, level, category, task_id))
    connection.commit()
    connection.close()
    
    return jsonify({'success': True})

@bp.route('/stats/<int:user_id>')
def stats(user_id):
    connection = get_db_connection()
    user = connection.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    try:
        year = int(request.args.get('year', date.today().year))
        month = int(request.args.get('month', date.today().month))
    except (TypeError, ValueError):
        today = date.today()
        year, month = today.year, today.month

    current_month_date = date(year, month, 1)
    prev_month_date = current_month_date - timedelta(days=1)
    next_month_date = (current_month_date + timedelta(days=32)).replace(day=1)
    
    prev_month = {'year': prev_month_date.year, 'month': prev_month_date.month}
    next_month = {'year': next_month_date.year, 'month': next_month_date.month}
    is_future = (year > date.today().year) or (year == date.today().year and month >= date.today().month)

    # --- データを取得 ---
    total_by_subject_rows = connection.execute('SELECT s.name, SUM(sl.duration_minutes) as total FROM study_logs sl JOIN subjects s ON sl.subject_id = s.id WHERE sl.user_id = ? GROUP BY s.name', (user_id,)).fetchall()
    last_7_days_rows = connection.execute("SELECT date, SUM(duration_minutes) as total FROM study_logs WHERE user_id = ? AND date >= date('now', '-7 days') GROUP BY date ORDER BY date", (user_id,)).fetchall()
    recent_logs_rows = connection.execute('SELECT sl.id, sl.date, s.name, sl.duration_minutes FROM study_logs sl JOIN subjects s ON sl.subject_id = s.id WHERE sl.user_id = ? ORDER BY sl.date DESC, sl.id DESC LIMIT 10', (user_id,)).fetchall()
    user_subjects_rows = connection.execute('SELECT s.id, s.name FROM subjects s JOIN user_subjects us ON s.id = us.subject_id WHERE us.user_id = ?', (user_id,)).fetchall()
    
    # --- カレンダー用のデータを計算 ---
    if user['grade'] == 'ronin': thresholds = {5: 600, 4: 480, 3: 300, 2: 180, 1: 1}
    else: thresholds = {5: 300, 4: 180, 3: 120, 2: 60, 1: 1}
    
    all_logs_rows = connection.execute("SELECT date, SUM(duration_minutes) as total FROM study_logs WHERE user_id = ? GROUP BY date", (user_id,)).fetchall()
    study_data = {row['date']: row['total'] for row in all_logs_rows}
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
        
    # --- 編集モーダル用の詳細データを計算 ---
    all_logs_details_rows = connection.execute('SELECT date, subject_id, duration_minutes FROM study_logs WHERE user_id = ?', (user_id,)).fetchall()
    logs_by_date = defaultdict(dict)
    for row in all_logs_details_rows: logs_by_date[row['date']][row['subject_id']] = row['duration_minutes']
    
    connection.close()
    
    # --- データを辞書リストに変換 ---
    total_by_subject = [dict(row) for row in total_by_subject_rows]
    last_7_days = [dict(row) for row in last_7_days_rows]
    recent_logs = [dict(row) for row in recent_logs_rows]
    user_subjects = [dict(row) for row in user_subjects_rows]

    return render_template(
        'stats.html', user=user,
        subject_labels=[r['name'] for r in total_by_subject], subject_data=[r['total'] for r in total_by_subject],
        date_labels=[r['date'] for r in last_7_days], date_data=[r['total'] for r in last_7_days],
        calendar_data=calendar_data, month=month, year=year,
        recent_logs=recent_logs, user_subjects=user_subjects,
        logs_by_date=logs_by_date, prev_month=prev_month, next_month=next_month, is_future=is_future
    )

# 記録を受け取るための専用API
# app/routes.py の log_study_for_date 関数をこちらに置き換え

@bp.route('/api/log_study_for_date/<int:user_id>', methods=['POST'])
def log_study_for_date(user_id):
    connection = get_db_connection()
    data = request.get_json()
    date = data.get('date')
    logs = data.get('logs')

    if not date or logs is None:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    for log in logs:
        subject_id = log.get('subject_id')
        
        # ▼▼▼ [修正点] 空の文字列を'0'として扱うように修正 ▼▼▼
        hours_str = log.get('hours') or '0'
        minutes_str = log.get('minutes') or '0'
        
        # 空白や不正な値が入っていてもエラーにならないように、安全に整数に変換
        try:
            total_minutes = int(hours_str) * 60 + int(minutes_str)
        except (ValueError, TypeError):
            total_minutes = 0 # 変換に失敗したら0分とする
        
        existing_log = connection.execute('SELECT id FROM study_logs WHERE user_id = ? AND subject_id = ? AND date = ?',
                                          (user_id, subject_id, date)).fetchone()
        
        if total_minutes > 0:
            if existing_log:
                connection.execute('UPDATE study_logs SET duration_minutes = ? WHERE id = ?', (total_minutes, existing_log['id']))
            else:
                connection.execute('INSERT INTO study_logs (user_id, subject_id, date, duration_minutes) VALUES (?, ?, ?, ?)',
                                   (user_id, subject_id, date, total_minutes))
        elif existing_log:
            connection.execute('DELETE FROM study_logs WHERE id = ?', (existing_log['id'],))

    connection.commit()
    connection.close()
    return jsonify({'success': True})

@bp.route('/log/<int:log_id>/delete', methods=['POST'])
def delete_log(log_id):
    connection = get_db_connection()
    # 削除後に正しいユーザーのページに戻るため、先にuser_idを取得
    log = connection.execute('SELECT user_id FROM study_logs WHERE id = ?', (log_id,)).fetchone()
    if log:
        user_id = log['user_id']
        connection.execute('DELETE FROM study_logs WHERE id = ?', (log_id,))
        connection.commit()
        connection.close()
        return redirect(url_for('main.stats', user_id=user_id))
    
    # もしログが見つからなかった場合（念のため）
    connection.close()
    # ログイン中のユーザーのstatsページにリダイレクトするなどの代替案
    return redirect(url_for('main.stats', user_id=session.get('user_id')))

@bp.route('/api/select_sequential_task', methods=['POST'])
def select_sequential_task():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    group_id = data.get('group_id')
    task_id = data.get('task_id')

    if not all([group_id, task_id]):
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    connection = get_db_connection()
    connection.execute(
        'INSERT OR REPLACE INTO user_sequential_task_selections (user_id, group_id, selected_task_id) VALUES (?, ?, ?)',
        (user_id, group_id, task_id)
    )
    connection.commit()
    connection.close()
    
    return jsonify({'success': True})
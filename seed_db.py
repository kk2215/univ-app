# seed_db.py

from app.models import Subject, University, Faculty, Book, Route, RouteStep, SubjectStrategy
from seed_data.universities import universities_to_seed
from seed_data.books import books_to_seed
from seed_data.routes import routes_to_seed, route_steps_human_readable
from seed_data.faculties import faculties_to_seed
from seed_data.strategies import strategy_data

def seed_database(db):
    """データベースに初期データを投入する関数"""
    print("Seeding database...")

    # --- 1. 科目マスターデータ ---
    subjects_list = [
        '英語', '数学', '現代文', '古文', '漢文', '世界史', '日本史', 
        '地理', '政治・経済', '倫理', '物理', '化学', '生物', '地学', '小論文'
    ]
    for subject_name in subjects_list:
        # ▼▼▼ Model.query -> db.session.query(Model) に変更 ▼▼▼
        if not db.session.query(Subject).filter_by(name=subject_name).first():
            db.session.add(Subject(name=subject_name))
    db.session.commit()
    print("科目を登録しました。")

    # --- 2. 大学マスターデータ ---
    for name, kana, level, url in universities_to_seed:
        if not db.session.query(University).filter_by(name=name).first():
            db.session.add(University(name=name, kana_name=kana, level=level, info_url=url))
    db.session.commit()
    print("大学データを登録しました。")

    # --- 3. 学部マスターデータの登録 ---
    university_id_map = {u.name: u.id for u in db.session.query(University).all()}
    for uni_name, fac_name in faculties_to_seed:
        if uni_name in university_id_map:
            uni_id = university_id_map[uni_name]
            if not db.session.query(Faculty).filter_by(university_id=uni_id, name=fac_name).first():
                db.session.add(Faculty(university_id=uni_id, name=fac_name))
    db.session.commit()
    print("学部データを登録しました。")

    # --- 4. 参考書マスターデータ ---
    for task_id, title, desc, yt, weeks, type in books_to_seed:
        if not db.session.query(Book).filter_by(task_id=task_id).first():
            db.session.add(Book(task_id=task_id, title=title, description=desc, youtube_query=yt, duration_weeks=weeks, task_type=type))
    db.session.commit()
    print("参考書を登録しました。")

    # --- 5. ルート定義 ---
    subject_id_map = {s.name: s.id for s in db.session.query(Subject).all()}
    for name, p_type, s_id_or_name in routes_to_seed:
        subject_id = subject_id_map.get(s_id_or_name) if isinstance(s_id_or_name, str) else s_id_or_name
        if not db.session.query(Route).filter_by(name=name).first():
            db.session.add(Route(name=name, plan_type=p_type, subject_id=subject_id))
    db.session.commit()
    print("各科目のルートを定義しました。")
    
    # --- 6. ルートステップ登録 ---
    book_id_map = {b.task_id: b.id for b in db.session.query(Book).all()}
    route_id_map = {r.name: r.id for r in db.session.query(Route).all()}
    for route_name, task_id, step, level, cat, is_main in route_steps_human_readable:
        if route_name in route_id_map and task_id in book_id_map:
            route_id = route_id_map[route_name]
            book_id = book_id_map[task_id]
            if not db.session.query(RouteStep).filter_by(route_id=route_id, book_id=book_id, step_order=step).first():
                db.session.add(RouteStep(route_id=route_id, book_id=book_id, step_order=step, level=level, category=cat, is_main=is_main))
    db.session.commit()
    print("全科目のルートステップを登録しました。")
    
    # --- 7. 学習戦略データ ---
    for subject_name, strategy_html in strategy_data.items():
        if subject_name in subject_id_map:
            subject_id = subject_id_map[subject_name]
            if not db.session.query(SubjectStrategy).filter_by(subject_id=subject_id).first():
                db.session.add(SubjectStrategy(subject_id=subject_id, strategy_html=strategy_html))
    db.session.commit()
    print("学習戦略データを登録しました。")

    print("データベースに全ての初期データを投入しました。")
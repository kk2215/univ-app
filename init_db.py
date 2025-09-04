import sqlite3

def main():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # usersテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE, -- ユーザー名を追加（重複不可）
            password_hash TEXT NOT NULL,   -- 暗号化パスワードを追加
            grade TEXT NOT NULL,
            school TEXT NOT NULL,
            faculty TEXT NOT NULL,
            plan_type TEXT NOT NULL,
            course_type TEXT,
            prefecture TEXT,
            target_exam_date DATE,
            starting_level INTEGER NOT NULL,
            learning_style TEXT
        )
    ''')

    # usersテーブルにtarget_exam_dateを追加
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
            grade TEXT NOT NULL, school TEXT NOT NULL, faculty TEXT NOT NULL,
            plan_type TEXT NOT NULL, course_type TEXT, prefecture TEXT,
            target_exam_date DATE
        )
    ''')


    # subjectsテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # user_subjectsテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subjects (
            user_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, subject_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
    ''')

    # universitiesテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS universities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            kana_name TEXT NOT NULL,
            level TEXT NOT NULL,
            info_url TEXT 
        )
    ''')

    # booksテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
            description TEXT NOT NULL, youtube_query TEXT,
            duration_weeks INTEGER NOT NULL DEFAULT 1,
            task_type TEXT NOT NULL DEFAULT 'sequential'
        )
    ''')

    # routesテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            plan_type TEXT NOT NULL,
            subject_id INTEGER,
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
    ''')

    # route_stepsテーブル

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS route_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        step_order INTEGER NOT NULL,
        level TEXT NOT NULL,
        category TEXT NOT NULL,
        is_main INTEGER NOT NULL DEFAULT 1, -- この行が重要です
        FOREIGN KEY (route_id) REFERENCES routes (id),
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
''')

    # progressテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            is_completed INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # weaknessesテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weaknesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # init_db.py の末尾に追記

# 学部マスターテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            university_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (university_id) REFERENCES universities (id)
    )
''')

# 学部と必須科目を紐付けるテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculty_subjects (
             faculty_id INTEGER NOT NULL,
             subject_id INTEGER NOT NULL,
             PRIMARY KEY (faculty_id, subject_id),
             FOREIGN KEY (faculty_id) REFERENCES faculties (id),
             FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
''')

    # init_db.py の末尾に追記
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_hidden_tasks (
        user_id INTEGER NOT NULL,
        task_id TEXT NOT NULL,
        PRIMARY KEY (user_id, task_id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
    
    # init_db.py の末尾に追記
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subject_strategies (
        subject_id INTEGER PRIMARY KEY,
        strategy_html TEXT NOT NULL,
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
''')

    # init_db.py の末尾に追記
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_subject_levels (
        user_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        start_level INTEGER NOT NULL,
        PRIMARY KEY (user_id, subject_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
''')

# init_db.py の user_continuous_task_selections の CREATE TABLE 文をこちらに置き換え

    cursor.execute('''
CREATE TABLE IF NOT EXISTS user_continuous_task_selections (
    user_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    level TEXT NOT NULL,
    category TEXT NOT NULL,
    selected_task_id TEXT NOT NULL,
    PRIMARY KEY (user_id, subject_id, level, category),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (subject_id) REFERENCES subjects (id)
)
''')

    # init_db.py の一番下に追加

    cursor.execute('''
CREATE TABLE IF NOT EXISTS study_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    date DATE NOT NULL,
    duration_minutes INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (subject_id) REFERENCES subjects (id)
)
''')
    
    # init_db.py の一番下に追加

    cursor.execute('''
CREATE TABLE IF NOT EXISTS user_sequential_task_selections (
    user_id INTEGER NOT NULL,
    group_id TEXT NOT NULL, 
    selected_task_id TEXT NOT NULL,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

    connection.commit()
    connection.close()
    print("マルチ科目対応の新しいデータベース構造が準備できました。")

if __name__ == '__main__':
    main()
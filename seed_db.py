import sqlite3
from seed_data.universities import universities_to_seed
from seed_data.books import books_to_seed
from seed_data.routes import routes_to_seed, route_steps_human_readable
from seed_data.faculties import faculties_to_seed # <-- この行を追加

def seed_database():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # --- 1. 科目マスターデータ ---
    subjects_to_seed = [
    ('英語',), ('数学',), ('現代文',), ('古文',), ('漢文',),
    ('世界史',), ('日本史',), ('地理',), ('政治・経済',), ('倫理',),
    ('物理',), ('化学',), ('生物',), ('地学',), ('小論文',)
]
    
    cursor.executemany('INSERT OR IGNORE INTO subjects (name) VALUES (?)', subjects_to_seed)
    print("科目を登録しました。")

    # --- 2. 大学マスターデータ ---
    cursor.executemany('INSERT OR IGNORE INTO universities (name, kana_name, level, info_url) VALUES (?, ?, ?, ?)', universities_to_seed)
    print("大学データを登録しました。")

    # --- 3. 学部マスターデータの登録 ---
    print("学部データの登録を開始します...")
    university_id_map = {row[1]: row[0] for row in cursor.execute('SELECT id, name FROM universities').fetchall()}
    
    faculties_with_ids = []
    for uni_name, fac_name in faculties_to_seed:
        if uni_name in university_id_map:
            faculties_with_ids.append((university_id_map[uni_name], fac_name))
    
    cursor.executemany('INSERT OR IGNORE INTO faculties (university_id, name) VALUES (?, ?)', faculties_with_ids)
    print(f"{len(faculties_with_ids)}件の学部データを登録しました。")

    # --- 4. 参考書マスターデータ ---
    # seed_db.py の該当行を修正
    cursor.executemany('INSERT OR IGNORE INTO books (task_id, title, description, youtube_query, duration_weeks, task_type) VALUES (?, ?, ?, ?, ?, ?)', books_to_seed)
    print(f"{len(books_to_seed)}件の参考書を登録しました。")

    # --- 5. ルート定義 ---
    cursor.executemany('INSERT OR IGNORE INTO routes (name, plan_type, subject_id) VALUES (?, ?, ?)', routes_to_seed)
    print("各科目のルートを定義しました。")
    
    # --- 6. ルートステップ登録 ---
    print("ルートステップの登録を開始します...")
    book_id_map = {row[1]: row[0] for row in cursor.execute('SELECT id, task_id FROM books').fetchall()}
    route_id_map = {row[1]: row[0] for row in cursor.execute('SELECT id, name FROM routes').fetchall()}

    final_route_steps = []
    for route_name, task_id, step, level, cat, is_main in route_steps_human_readable:
        if route_name in route_id_map and task_id in book_id_map:
            final_route_steps.append((
                route_id_map[route_name], book_id_map[task_id],
                step, level, cat, is_main
            ))
        else:
            print(f"警告: 見つからないIDです - Route: {route_name}, Task: {task_id}")

    cursor.executemany('INSERT OR IGNORE INTO route_steps (route_id, book_id, step_order, level, category, is_main) VALUES (?, ?, ?, ?, ?, ?)', final_route_steps)
    print("全科目のルートステップを登録しました。")
    
    # seed_db.py の末尾に追記
    print("学習戦略データの登録を開始します...")
    strategy_data = {
        '英語': """
            <h4>揺るぎない「学習順序」を守り抜く</h4>
            <p>英語学習には<b>「単語・熟語 → 文法 → 英文解釈 → 長文読解」</b>という、決して崩してはならない普遍的な順序が存在します。単語と文法という土台なくして長文は読めません。</p>
            <ul>
                <li><b>単語・熟語：</b> 『システム英単語』のように短いフレーズの中で使い方と一緒に覚える方法と、『ターゲット』シリーズのように一語一義でスピーディーに覚える方法があります。自分に合った一冊を選び、毎日触れることを徹底しましょう。</li>
                <li><b>長文読解：</b> 精読で構造を理解した後は、必ず音読を繰り返してください。これにより、英語を頭から理解する回路が作られ、速読力とリスニング力の向上に直結します。</li>
            </ul>
        """,
        '数学': """
            <h4>解法の「型」を体に叩き込む</h4>
            <p>大学入試数学の問題は、その9割が基礎的な問題の組み合わせで構成されています。したがって、典型問題の「解法パターン」を瞬時に引き出せるようにすることが最重要課題です。</p>
            <ul>
                <li><b>問題集の反復：</b> 『基礎問題精講』のような厳選された問題集を使い、問題文を見た瞬間に解法の方針が立てられるレベルまで、何度も繰り返しましょう。</li>
                <li><b>「わかったつもり」の撲滅：</b> 解説を読んで理解した問題は、必ず解説を閉じて、自分の力だけで再現できるかを確認する作業を徹底してください。これを怠ると、いつまでも「見たことはあるのに解けない」状態から抜け出せません。</li>
            </ul>
        """,
        '現代文': """
            <h4>感覚を排し、「論理」で読み解く</h4>
            <p>筆者の主張を客観的に捉える「論理的な読解法」を身につけることが全てです。文章全体の構造（対比、因果関係など）を意識し、各段落の要旨をまとめる訓練は、記述力だけでなく選択肢問題の精度も飛躍的に向上させます。</p>
        """,
        '古文': """
            <h4>まずは外国語として捉える</h4>
            <p>古文は外国語です。まずは<b>単語と文法</b>の暗記が絶対的な基礎となります。これらをマスターして初めて、正確な読解が可能になります。</p>
        """,
        '漢文': """
            <h4>短期集中で得点源に</h4>
            <p>漢文は覚える範囲が限定的（主に句法）で得点源にしやすい科目です。短期間で集中してマスターするのがおすすめです。</p>
        """,
        '日本史': """
            <h4>「流れ」と「用語」を有機的に結びつける</h4>
            <p>まず講義本で歴史の大きな<b>「流れ（ストーリー）」を物語として理解します。その上で、一問一答などで個別の「用語」</b>を暗記し、再度講義本に戻って「あの流れの中の、この用語か」と確認する。この反復学習が最も効率的です。</p>
        """,
        '世界史': """
            <h4>「流れ」と「用語」を有機的に結びつける</h4>
            <p>まず講義本で歴史の大きな<b>「流れ（ストーリー）」を物語として理解します。その上で、一問一答などで個別の「用語」</b>を暗記し、再度講義本に戻って「あの流れの中の、この用語か」と確認する。この反復学習が最も効率的です。</p>
        """,
        '地理': """
            <h4>「なぜ？」を常に意識する</h4>
            <p>「なぜこの地域でこの産業が発達するのか」「なぜこの気候が生まれるのか」といった因果関係を理解することで、単なる暗記を超えた思考力が身につきます。資料集の活用も不可欠です。</p>
        """,
        '政治・経済': """
            <h4>「なぜ？」を常に意識する</h4>
            <p>「なぜこの制度が必要なのか」「なぜこの経済現象が起きるのか」といった因果関係を理解することが、単なる暗記を超えた思考力に繋がります。</p>
        """,
        '倫理': """
            <h4>思想家の対話として理解する</h4>
            <p>各思想家が、前の時代の誰の考えに影響を受け、誰を批判したのか、という「思想の系譜」を意識すると、知識が繋がりやすくなります。</p>
        """,
        '物理': """
            <h4>「なぜ？」の理解が応用力を生む</h4>
            <p>公式の丸暗記は最も危険です。必ず講義系の参考書で、その公式が成り立つ理由や、現象の背景にあるメカニズムを深く理解することから始めましょう。<b>理解と演習の往復</b>が鍵です。</p>
        """,
        '化学': """
            <h4>「なぜ？」の理解が応用力を生む</h4>
            <p>公式や用語の丸暗記ではなく、まず講義系の参考書で、化学反応の背景にあるメカニズムを深く理解することから始めましょう。<b>理解と演習の往復</b>が鍵です。</p>
        """,
        '生物': """
            <h4>「なぜ？」の理解が応用力を生む</h4>
            <p>生命現象の背景にあるメカニズムを深く理解することから始めましょう。<b>資料集を常に横に置き</b>、文字情報とビジュアル情報を結びつけながら学習すると記憶に定着しやすくなります。</p>
        """,
        '地学': """
            <h4>資料集こそが最高の参考書</h4>
            <p>図やデータが豊富な<b>『地学図録』</b>のような資料集は、他のどの科目よりも重要性が高く、常に参照するべき必須アイテムです。過去問演習が学習の主体となります。</p>
        """
    }
    subject_id_map = {row[1]: row[0] for row in cursor.execute('SELECT id, name FROM subjects').fetchall()}
    for subject_name, strategy_html in strategy_data.items():
        if subject_name in subject_id_map:
            subject_id = subject_id_map[subject_name]
            cursor.execute('INSERT OR REPLACE INTO subject_strategies (subject_id, strategy_html) VALUES (?, ?)', (subject_id, strategy_html))
    print("学習戦略データを登録しました。")

    connection.commit()
    connection.close()
    print("データベースに全ての初期データを投入しました。")

if __name__ == '__main__':
    seed_database()
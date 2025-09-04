import sqlite3

def inspect_database():
    db_path = 'database.db'
    print(f"--- '{db_path}' の内部調査を開始します ---")
    
    try:
        connection = sqlite3.connect(db_path)
        # ▼▼▼【重要】この一行を追加して、列名でアクセスできるようにします ▼▼▼
        connection.row_factory = sqlite3.Row
        
        cursor = connection.cursor()

        # 問題が報告された科目名
        subjects_to_check = ['物理', '数学', '政治・経済', '倫理']

        for subject in subjects_to_check:
            print(f"\n▼▼▼ 科目'{subject}'のルート内容 ▼▼▼")
            
            # 特定の科目に紐づくルートと、そのステップに含まれる参考書をすべて取得する
            query = """
                SELECT
                    r.name AS route_name,
                    rs.step_order,
                    b.task_id AS book_task_id,
                    b.title AS book_title
                FROM route_steps rs
                JOIN routes r ON rs.route_id = r.id
                JOIN books b ON rs.book_id = b.id
                JOIN subjects s ON r.subject_id = s.id
                WHERE s.name = ?
                ORDER BY rs.step_order;
            """
            
            results = cursor.execute(query, (subject,)).fetchall()

            if not results:
                print("この科目のルートは登録されていません。")
            else:
                for row in results:
                    print(f"ルート名: {row['route_name']}, ステップ: {row['step_order']}, 参考書ID: {row['book_task_id']}, 参考書名: {row['book_title']}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if 'connection' in locals():
            connection.close()
        print("\n--- 調査を終了します ---")

if __name__ == '__main__':
    inspect_database()
# run.py

from app import create_app, db # dbもインポート
from seed_db import seed_database 

app = create_app()

@app.cli.command('seed-db')
def seed_db_command():
    """データベースに初期データを投入します。"""
    # ▼▼▼ ここで準備済みのdbオブジェクトを渡す ▼▼▼
    seed_database(db)
    print('データベースの初期化が完了しました。')

if __name__ == '__main__':
    app.run()
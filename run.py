# run.py

from app import create_app
from seed_db import seed_database # seed_db.py から関数をインポート

# create_app() から Flaskアプリのインスタンスを作成
app = create_app()

# 'seed-db' という名前で新しい flask コマンドを登録
@app.cli.command('seed-db')
def seed_db_command():
    """データベースに初期データを投入します。"""
    seed_database()
    print('データベースの初期化が完了しました。')

# このファイルは、`flask run` を実行したときにも使われます
if __name__ == '__main__':
    app.run()
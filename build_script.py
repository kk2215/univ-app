from app import create_app, db
from flask_migrate import upgrade
from seed_db import seed_database

print("--- Build script started ---")

# 1. アプリケーションを一度だけ作成
app = create_app()

# 2. 作成したアプリのコンテキスト内で、全てのDB操作を実行
with app.app_context():
    print("--- Running database upgrade... ---")
    # テーブル作成・更新を実行
    upgrade()
    print("--- Database upgrade finished. ---")

    print("--- Seeding database... ---")
    # データ投入を実行
    seed_database(db)
    print("--- Database seeding finished. ---")

print("--- Build script finished successfully! ---")
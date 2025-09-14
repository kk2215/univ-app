# run.py

from app import create_app

print("--- A. run.py がインポートされました ---")
app = create_app()
print("--- B. create_app() の呼び出しが完了しました ---")


if __name__ == '__main__':
    app.run()
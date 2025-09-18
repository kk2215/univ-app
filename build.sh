#!/usr/bin/env bash
# exit on error
set -e

pip install -r requirements.txt

# ▼▼▼ この一行を追加 ▼▼▼
# FLASK_APP環境変数を、このスクリプト内で明確に設定する
export FLASK_APP=app:create_app

# これで、以下のflaskコマンドは必ずアプリを見つけられる
flask setup-db
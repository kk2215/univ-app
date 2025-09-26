#!/usr/bin/env bash
# exit on error
set -o errexit

# 必要なライブラリをインストール
pip install -r requirements.txt

# データベースのマイグレーションを実行
flask db upgrade
#!/usr/bin/env bash
# exit on error
set -e

pip install -r requirements.txt

export FLASK_APP=app:create_app
flask setup-db
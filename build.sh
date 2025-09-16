#!/usr/bin/env bash
# exit on error
set -e

pip install -r requirements.txt

flask db upgrade

flask seed-db
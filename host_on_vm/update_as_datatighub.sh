#!/bin/bash

set -e

cd
export $(grep -v '^#' env_vars | xargs)
cd datatighub
git pull
source .ve/bin/activate
pip install -r requirements.txt
cd datatighub/
python manage.py migrate
python manage.py collectstatic --noinput

#!/bin/bash

set -e

cd
export $(grep -v '^#' env_vars | xargs)
cd datatighub/
source .ve/bin/activate
cd datatighub/
python manage.py $*


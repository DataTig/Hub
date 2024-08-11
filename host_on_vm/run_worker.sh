#!/bin/bash

set -e

cd
export $(grep -v '^#' env_vars | xargs)
cd datatighub
source .ve/bin/activate
cd datatighub/
celery -A datatighubcore worker --without-heartbeat --without-gossip --without-mingle -l info -Q important,celery

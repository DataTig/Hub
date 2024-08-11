#!/bin/bash

set -e

systemctl stop datatighubworker.service
systemctl stop datatighubworkerimportant.service

systemctl stop uwsgi.service
killall -9 uwsgi

# This currently fails, so always pass it so next statement runs
systemctl start uwsgi.service || true

systemctl start datatighubworker.service
systemctl start datatighubworkerimportant.service

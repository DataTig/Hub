#!/bin/bash

set -e

current_date=$(date +"%d")

pg_dump --host=localhost --username=datatighub --no-password -f /home/datatighub/backups/database-$current_date.sql datatighub

zip -q -r /home/datatighub/backups/backup-$current_date.zip  /home/datatighub/backups/database-$current_date.sql  /home/datatighub/data

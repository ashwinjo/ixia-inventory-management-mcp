#!/bin/bash

set -e

exec python3 init_db_new.py
exec python3 data_poller.py --category=chassis --interval=60 &
exec python3 data_poller.py --category=cards --interval=60 &
exec python3 data_poller.py --category=ports --interval=60 &
exec python3 data_poller.py --category=sensors --interval=60 &
exec python3 data_poller.py --category=perf --interval=60 &
exec python3 data_poller.py --category=licensing --interval=900 &
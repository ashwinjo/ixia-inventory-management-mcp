python3 init_db_new.py
python3 data_poller.py --category=chassis --interval=60 &
python3 data_poller.py --category=cards --interval=60 &
python3 data_poller.py --category=ports --interval=60 &
python3 data_poller.py --category=sensors --interval=60 &
python3 data_poller.py --category=perf --interval=60 &
python3 data_poller.py --category=licensing --interval=900 &
flask --app /python-docker/myapp.py --debug run --host=0.0.0.0 -p 3000
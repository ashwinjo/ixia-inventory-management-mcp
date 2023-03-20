python3 init_db.py
python3 data_poller.py --category=chassis --interval=60 &
sleep 15
python3 data_poller.py --category=cards --interval=60 &
python3 data_poller.py --category=ports --interval=60 &
python3 data_poller.py --category=sensors --interval=60 &
python3 data_poller.py --category=perf --interval=60 &
python3 data_poller.py --category=licensing --interval=120 &
flask --app /python-docker/myapp.py --debug run --host=0.0.0.0 -p 3000

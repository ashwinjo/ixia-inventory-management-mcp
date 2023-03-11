python3 data_poller.py --category=chassis --interval=15 &
python3 data_poller.py --category=cards --interval=30 &
python3 data_poller.py --category=ports --interval=30 &
python3 data_poller.py --category=sensors --interval=30 &
python3 data_poller.py --category=licensing --interval=900 &
# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
EXPOSE 3000

# Create Barebones Databases
CMD ["python3", "init_db.py"]

# Start web app
CMD ["flask", "--app","/python-docker/myapp.py", "--debug", "run", "--host=0.0.0.0", "-p", "3000"]

# Start pollers
CMD ["sh", "start_pollers.sh"]


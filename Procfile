release: cd ./news && orator migrate -f && cd ..
web: newrelic-admin run-program gunicorn -b "0.0.0.0:$PORT" -w 3 news:app
worker: rq worker
clock: python scheduler.py
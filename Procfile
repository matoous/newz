release: cd ./news && orator migrate -f && cd ..
web: newrelic-admin run-program gunicorn -b "0.0.0.0:$PORT" -w 3 hello:app
worker: rq worker
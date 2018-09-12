release: cd ./news && orator migrate -f && cd ..
web: gunicorn news:app
worker: rq worker
import json
import os

DATABASES = json.loads(os.getenv('DATABASES')) if os.getenv('DATABASES') else {"default": "postgres", "postgres": {"driver": "postgres", "host": "localhost", "database": "newsfeed", "user": "postgres", "password": "postgres", "prefix": ""}}

if os.getenv('DATABASE_URL') is not None:
    url = os.getenv('DATABASE_URL')
    f, s = url[11:].split('@')
    name, password = f.split(':')
    host, db = s.split('/')
    DATABASES['postgres'] = {
        'driver': 'postgres',
        'host': host.split(':')[0],
        'database': db,
        'user': name,
        'password': password,
        'prefix': '',
    }
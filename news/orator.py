import json
import os

DATABASES = json.loads(os.getenv('DATABASES')) if os.getenv('DATABASES') else {
    'default': 'postgres',
    'postgres': {
        'driver': 'postgres',
        'host': 'news.c4ioot2pm9qy.eu-central-1.rds.amazonaws.com',
        'database': 'news',
        'user': 'newsadmin',
        'password': 'Zub5t5SeBl2z2#yolo!',
        'prefix': '',
    },
}

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
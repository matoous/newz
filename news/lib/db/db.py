# apps.members.models
from flask_orator import Orator
from orator import Schema, DatabaseManager

db = Orator()
manager = DatabaseManager({
    'default': 'postgres',
    'postgres': {
        'driver': 'postgres',
        'host': 'localhost',
        'database': 'newsfeed',
        'user': 'postgres',
        'password': '',
        'prefix': ''
    },
})
schema = Schema(manager)


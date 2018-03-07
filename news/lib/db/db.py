# apps.members.models
from flask_orator import Orator
from orator import Schema, DatabaseManager

db = Orator()
manager = DatabaseManager({'development': {
            'driver': 'sqlite',
            'database': '/tmp/test.db'
        }})
schema = Schema(manager)


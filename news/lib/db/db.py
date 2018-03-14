from orator import Schema, DatabaseManager, Model

db = DatabaseManager({
    'default': 'postgres',
    'postgres': {
        'driver': 'postgres',
        'host': 'localhost',
        'database': 'newsfeed',
        'user': 'postgres',
        'password': '',
        'prefix': '',
    },
})
schema = Schema(db)
Model.set_connection_resolver(db)
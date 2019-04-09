import json
import os

DATABASES = (
    json.loads(os.getenv("DATABASES"))
    if os.getenv("DATABASES")
    else {
        "default": "postgres",
        "postgres": {
            "driver": "postgres",
            "host": "localhost",
            "port": 5432,
            "database": "news",
            "user": "postgres",
            "password": "postgres",
        },
    }
)

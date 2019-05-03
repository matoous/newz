import json
import os

if os.getenv("DATABASE_URL") is not None:
        url = os.getenv("DATABASE_URL")
        f, s = url[11:].split("@")
        name, password = f.split(":")
        host, db = s.split("/")
        config = {
                "default": "postgres",
                "postgres": {
                    "driver": "postgres",
                    "host": host.split(":")[0],
                    "database": db,
                    "user": name,
                    "password": password,
                    "prefix": "",
                    },
                }
else:
        config = {
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
DATABASES = config


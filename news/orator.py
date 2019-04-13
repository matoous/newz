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

url = os.getenv("DATABASE_URL")
f, s = url[11:].split("@")
name, password = f.split(":")
host, db = s.split("/")
DATABASES = ({
            "driver": "postgres",
            "host": host.split(":")[0],
            "database": db,
            "user": name,
            "password": password,
            "prefix": "",
})

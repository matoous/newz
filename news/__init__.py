from pathlib import Path

from prometheus_client import start_http_server, MetricsHandler

from news.config.app import make_app
from dotenv import load_dotenv

load_dotenv()
app = make_app()
from pathlib import Path

from news.config.app import make_app
from dotenv import load_dotenv

env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)
app = make_app()

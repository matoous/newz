from news.config.app import make_app
from dotenv import load_dotenv

load_dotenv("/etc/opt/news")
app = make_app()

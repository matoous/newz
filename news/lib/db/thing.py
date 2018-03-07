from datetime import datetime

from sqlalchemy import Column, Date


class Thing:
    added = Column(Date, default=datetime.utcnow)

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    niche = Column(String, nullable=False)
    location = Column(String, nullable=False)
    total_scraped = Column(Integer, default=0)
    total_qualified = Column(Integer, default=0)
    total_emailed = Column(Integer, default=0)
    total_replied = Column(Integer, default=0)
    total_closed = Column(Integer, default=0)
    status = Column(String, default="active")  # active | paused | completed
    created_at = Column(DateTime, default=datetime.utcnow)

    leads = relationship("Lead", backref="campaign", lazy="dynamic")

    def __repr__(self):
        return f"<Campaign {self.id}: {self.name} ({self.status})>"

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)

    # Business info (from Outscraper)
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    address = Column(String, default="")
    city = Column(String, default="")
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    google_maps_url = Column(String, default="")
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=True)

    # Analysis (from Claude API)
    screenshot_url = Column(String, nullable=True)
    site_score = Column(Integer, nullable=True)
    site_issues = Column(Text, nullable=True)  # JSON string
    analysis_summary = Column(Text, nullable=True)

    # Preview (from Lovable API)
    preview_url = Column(String, nullable=True)
    preview_prompt = Column(Text, nullable=True)
    preview_status = Column(String, default="pending")  # pending | generating | ready | failed

    # Outreach (from Instantly.ai)
    email_subject = Column(String, nullable=True)
    email_body = Column(Text, nullable=True)
    email_status = Column(String, default="draft")  # draft | sent | opened | clicked | replied | bounced
    email_sent_at = Column(DateTime, nullable=True)

    # Pipeline status
    status = Column(String, default="scraped")  # scraped | analyzed | preview_ready | email_drafted | sent | responded | closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Lead {self.id}: {self.business_name} ({self.status})>"

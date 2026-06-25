from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class PropertyBase(BaseModel):
    title: Optional[str] = "Unknown Property"
    bank_name: Optional[str] = "N/A"
    reserve_price: Optional[float] = None
    emd: Optional[float] = None
    area_sqft: Optional[float] = None
    rate_sqft: Optional[float] = None
    city: Optional[str] = "N/A"
    area_locality: Optional[str] = "N/A"
    state: Optional[str] = "N/A"
    auction_start_date: Optional[str] = "N/A"
    auction_end_time: Optional[str] = "N/A"
    borrower_name: Optional[str] = "N/A"
    notice_image_url: Optional[str] = "N/A"
    source_url: str
    description: Optional[str] = "N/A"
    listing_summary: Optional[str] = "N/A"
    auction_id: Optional[str] = "N/A"
    contact_details: Optional[str] = "N/A"
    branch_name: Optional[str] = "N/A"
    service_provider: Optional[str] = "N/A"
    asset_category: Optional[str] = "N/A"
    auction_type: Optional[str] = "N/A"
    application_submission_date: Optional[str] = "N/A"
    possession_status: Optional[str] = "Unknown" # NEW: Physical/Symbolic/Unknown

class PropertyEnrichment(BaseModel):
    area_sqft: Optional[float] = None
    market_rate_sqft: Optional[float] = None
    village: Optional[str] = None
    property_type: Optional[str] = None
    floor: Optional[str] = None
    society_name: Optional[str] = None
    discount_rate_percent: Optional[float] = None
    investment_score: Optional[int] = None # NEW: 0-100
    risk_rating: Optional[str] = None # NEW: Low/Medium/High

class Property(PropertyBase, PropertyEnrichment):
    id: Optional[int] = None
    crawled_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True, extra="ignore")

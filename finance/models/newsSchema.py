from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NewsItemResponse(BaseModel):
    id: int
    source: str
    title: str
    link: Optional[str] = None
    published_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True
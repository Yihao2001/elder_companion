from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List, Dict, Any



class LTMCategories(str, Enum):
    """Categories for long-term memory storage"""
    personal = "personal"
    family = "family"
    education = "education"
    career = "career"
    lifestyle = "lifestyle"
    finance = "finance"
    legal = "legal"

class InsertLongTermSchema(BaseModel):
    """Schema for long-term memory insertion"""
    category: LTMCategories = Field(
        ...,
        description="Category of long-term memory. Use for stable traits & preferences that rarely change - generally fixed profile information. Must follow one of the following categories ['personal','family','education','career','lifestyle','finance','legal']"
    )
    key: str = Field(
        ...,
        description="Key or label for the memory fact. Should be a clear, descriptive subcategory for the category for this piece of long-term information"
    )
    value: str = Field(
        ...,
        description="The fact/value to store. The actual free form user information long-term memory item. This should be stable information that rarely changes."
    )
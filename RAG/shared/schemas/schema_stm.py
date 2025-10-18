from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class InsertShortTermSchema(BaseModel):
    """Schema for short-term memory insertion"""
    content: str = Field(
        ...,
        description="Short-term conversational detail to store. Use for temporary information that's useful in the near future but doesn't belong in long-term or healthcare storage. Examples: reminders, temporary preferences, upcoming appointments, casual mentions."
    )
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class HealthRecordTypes(str, Enum):
    """Types of healthcare records"""
    condition = "condition"
    procedure = "procedure"
    appointment = "appointment"
    medication = "medication"

class InsertHealthSchema(BaseModel):
    """Schema for healthcare record insertion"""
    record_type: HealthRecordTypes = Field(
        ...,
        description="Type of healthcare record. Use for official physical/mental health information explicitly shared for future care. Must follow one of the following categories ['condition','procedure','appointment','medication']"
    )
    description: str = Field(
        ...,
        description="The details of the healthcare record. The actual free form and complete description of the medical information being stored. Should include specific details relevant to the record type."
    )
    diagnosis_date: Optional[str] = Field(
        None,
        description="Date in YYYY-MM-DD format (optional). When the healthcare event occurred, was diagnosed, or is scheduled. Leave empty if no specific date was mentioned. Examples: '2023-12-15', '2024-03-20', null."
    )
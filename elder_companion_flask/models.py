import enum
import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy import Table, Column, String, Date, Enum, ForeignKey, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from sqlalchemy.orm import relationship
from .db import Base

# ENUM types
class RoleEnum(enum.Enum):
    super_admin = "super_admin"
    caregiver = "caregiver"

class GenderEnum(enum.Enum):
    Male = "Male"
    Female = "Female"
    Other = "Other"

class MaritalEnum(enum.Enum):
    Single = "Single"
    Married = "Married"
    Widowed = "Widowed"
    Divorced = "Divorced"

class LTMCategoryEnum(enum.Enum):
    personal = "personal"
    family = "family"
    education = "education"
    career = "career"
    lifestyle = "lifestyle"
    finance = "finance"
    legal = "legal"

class RecordTypeEnum(enum.Enum):
    condition = "condition"
    procedure = "procedure"
    appointment = "appointment"
    medication = "medication"

# Tables
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Enum(RoleEnum))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    elderly = relationship("ElderlyProfile", secondary="user_elderly", back_populates="caregivers")

# This table join user to elderly 
user_elderly = Table(
    "user_elderly",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("elderly_id", UUID(as_uuid=True), ForeignKey("elderly_profile.id", ondelete="CASCADE"), primary_key=True)
)

class ElderlyProfile(Base):
    __tablename__ = "elderly_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(BYTEA)
    date_of_birth = Column(BYTEA)
    gender = Column(Enum(GenderEnum))
    nationality = Column(BYTEA)
    dialect_group = Column(BYTEA)
    marital_status = Column(Enum(MaritalEnum))
    address = Column(BYTEA)

    stm = relationship("ShortTermMemory", back_populates="elderly", cascade="all, delete-orphan")
    ltm = relationship("LongTermMemory", back_populates="elderly", cascade="all, delete-orphan")
    healthcare = relationship("HealthcareRecord", back_populates="elderly", cascade="all, delete-orphan")
    caregivers = relationship("User", secondary="user_elderly",back_populates="elderly")

class ShortTermMemory(Base):
    __tablename__ = "short_term_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    elderly_id = Column(UUID(as_uuid=True), ForeignKey("elderly_profile.id"))
    content = Column(String, nullable=False)
    embedding = Column(Vector(768))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    elderly = relationship("ElderlyProfile", back_populates="stm")

class LongTermMemory(Base):
    __tablename__ = "long_term_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    elderly_id = Column(UUID(as_uuid=True), ForeignKey("elderly_profile.id"))
    category = Column(Enum(LTMCategoryEnum))
    key = Column(String)
    value = Column(String)
    embedding = Column(Vector(768))
    last_updated = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    elderly = relationship("ElderlyProfile", back_populates="ltm")

class HealthcareRecord(Base):
    __tablename__ = "healthcare_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    elderly_id = Column(UUID(as_uuid=True), ForeignKey("elderly_profile.id"))
    record_type = Column(Enum(RecordTypeEnum))
    description = Column(String)
    diagnosis_date = Column(Date)
    embedding = Column(Vector(768))
    last_updated = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    elderly = relationship("ElderlyProfile", back_populates="healthcare")

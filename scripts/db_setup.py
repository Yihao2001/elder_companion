# scripts/db_setup.py
from elder_companion_flask.db import engine, Base, get_db

# Import all models so SQLAlchemy knows about them
from elder_companion_flask.models import (
    ElderlyProfile,
    ShortTermMemory,
    LongTermMemory,
    HealthcareRecord,
    User,
    user_elderly,
)

def create_tables():
    """
    Function to create tables defined in models.py if it does not already exists.
    However, this does not add new column to existing table.
    """
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()

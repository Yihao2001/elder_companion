"""
ElderComp Caregiver Interface Backend
FastAPI application for caregiver authentication and database operations
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add database config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'database'))
from config.database import DatabaseManager, DatabaseConfig

# Initialize FastAPI app
app = FastAPI(
    title="ElderComp Caregiver Interface API",
    description="Backend API for caregiver authentication and elderly data management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "eldercomp_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database manager
db_manager = DatabaseManager()

# Pydantic models
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: str
    username: str
    full_name: str
    role: str

class ElderlyProfile(BaseModel):
    id: str
    first_name: str
    last_name: str
    preferred_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None

class PersonalPreference(BaseModel):
    id: str
    elderly_id: str
    category: str
    preference_name: str
    preference_value: Optional[str] = None
    importance_level: int = 5
    notes: Optional[str] = None

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # For simplicity, we'll use hardcoded users
    # In production, this would query a users table
    if username == "caregiver1":
        return User(
            id="1",
            username="caregiver1",
            full_name="Dr. Sarah Johnson",
            role="primary_caregiver"
        )
    elif username == "admin":
        return User(
            id="2",
            username="admin",
            full_name="System Administrator",
            role="admin"
        )
    
    raise credentials_exception

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await db_manager.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await db_manager.close()

# Authentication endpoints
@app.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Authenticate user and return JWT token"""
    # Hardcoded users for demo (in production, query from database)
    users_db = {
        "caregiver1": {
            "username": "caregiver1",
            "hashed_password": get_password_hash("password123"),
            "full_name": "Dr. Sarah Johnson",
            "role": "primary_caregiver"
        },
        "admin": {
            "username": "admin",
            "hashed_password": get_password_hash("admin123"),
            "full_name": "System Administrator",
            "role": "admin"
        }
    }
    
    user = users_db.get(user_login.username)
    if not user or not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_health = await db_manager.health_check()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_health
    }

# Elderly profiles endpoints
@app.get("/elderly", response_model=List[ElderlyProfile])
async def get_elderly_profiles(current_user: User = Depends(get_current_user)):
    """Get all elderly profiles"""
    try:
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT id, first_name, last_name, preferred_name, date_of_birth,
                       gender, phone_number, emergency_contact_name, 
                       emergency_contact_phone, address
                FROM eldercomp.elderly_profiles
                ORDER BY first_name, last_name
            """)
            
            profiles = []
            for row in rows:
                profile = ElderlyProfile(
                    id=str(row['id']),
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    preferred_name=row['preferred_name'],
                    date_of_birth=row['date_of_birth'].isoformat() if row['date_of_birth'] else None,
                    gender=row['gender'],
                    phone_number=row['phone_number'],
                    emergency_contact_name=row['emergency_contact_name'],
                    emergency_contact_phone=row['emergency_contact_phone'],
                    address=row['address']
                )
                profiles.append(profile)
            
            return profiles
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/elderly/{elderly_id}", response_model=ElderlyProfile)
async def get_elderly_profile(elderly_id: str, current_user: User = Depends(get_current_user)):
    """Get specific elderly profile by ID"""
    try:
        async with db_manager.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT id, first_name, last_name, preferred_name, date_of_birth,
                       gender, phone_number, emergency_contact_name, 
                       emergency_contact_phone, address
                FROM eldercomp.elderly_profiles
                WHERE id = $1
            """, elderly_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Elderly profile not found")
            
            return ElderlyProfile(
                id=str(row['id']),
                first_name=row['first_name'],
                last_name=row['last_name'],
                preferred_name=row['preferred_name'],
                date_of_birth=row['date_of_birth'].isoformat() if row['date_of_birth'] else None,
                gender=row['gender'],
                phone_number=row['phone_number'],
                emergency_contact_name=row['emergency_contact_name'],
                emergency_contact_phone=row['emergency_contact_phone'],
                address=row['address']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/elderly/{elderly_id}/preferences", response_model=List[PersonalPreference])
async def get_elderly_preferences(elderly_id: str, current_user: User = Depends(get_current_user)):
    """Get personal preferences for an elderly person"""
    try:
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT id, elderly_id, category, preference_name, preference_value,
                       importance_level, notes
                FROM eldercomp.personal_preferences
                WHERE elderly_id = $1
                ORDER BY category, preference_name
            """, elderly_id)
            
            preferences = []
            for row in rows:
                preference = PersonalPreference(
                    id=str(row['id']),
                    elderly_id=str(row['elderly_id']),
                    category=row['category'],
                    preference_name=row['preference_name'],
                    preference_value=row['preference_value'],
                    importance_level=row['importance_level'],
                    notes=row['notes']
                )
                preferences.append(preference)
            
            return preferences
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/elderly/{elderly_id}/preferences", response_model=PersonalPreference)
async def create_elderly_preference(
    elderly_id: str, 
    preference: PersonalPreference, 
    current_user: User = Depends(get_current_user)
):
    """Create a new personal preference for an elderly person"""
    try:
        async with db_manager.get_connection() as conn:
            # Verify elderly profile exists
            elderly_exists = await conn.fetchval("""
                SELECT EXISTS(SELECT 1 FROM eldercomp.elderly_profiles WHERE id = $1)
            """, elderly_id)
            
            if not elderly_exists:
                raise HTTPException(status_code=404, detail="Elderly profile not found")
            
            # Insert new preference
            row = await conn.fetchrow("""
                INSERT INTO eldercomp.personal_preferences 
                (elderly_id, category, preference_name, preference_value, importance_level, notes)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, elderly_id, category, preference_name, preference_value, importance_level, notes
            """, elderly_id, preference.category, preference.preference_name, 
                preference.preference_value, preference.importance_level, preference.notes)
            
            return PersonalPreference(
                id=str(row['id']),
                elderly_id=str(row['elderly_id']),
                category=row['category'],
                preference_name=row['preference_name'],
                preference_value=row['preference_value'],
                importance_level=row['importance_level'],
                notes=row['notes']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/elderly/{elderly_id}/medical-summary")
async def get_medical_summary(elderly_id: str, current_user: User = Depends(get_current_user)):
    """Get medical summary for an elderly person (non-encrypted data only)"""
    try:
        async with db_manager.get_connection() as conn:
            # Get basic medical record info (without encrypted content)
            medical_records = await conn.fetch("""
                SELECT record_type, record_title, record_date, healthcare_provider
                FROM eldercomp.medical_records
                WHERE elderly_id = $1 AND is_active = true
                ORDER BY record_date DESC
                LIMIT 10
            """, elderly_id)
            
            # Get active medications count
            medication_count = await conn.fetchval("""
                SELECT COUNT(*) FROM eldercomp.medications
                WHERE elderly_id = $1 AND is_active = true
            """, elderly_id)
            
            # Get active conditions count
            condition_count = await conn.fetchval("""
                SELECT COUNT(*) FROM eldercomp.medical_conditions
                WHERE elderly_id = $1 AND status = 'active'
            """, elderly_id)
            
            # Get allergies count
            allergy_count = await conn.fetchval("""
                SELECT COUNT(*) FROM eldercomp.allergies
                WHERE elderly_id = $1 AND is_active = true
            """, elderly_id)
            
            return {
                "elderly_id": elderly_id,
                "recent_records": [
                    {
                        "type": record['record_type'],
                        "title": record['record_title'],
                        "date": record['record_date'].isoformat(),
                        "provider": record['healthcare_provider']
                    } for record in medical_records
                ],
                "summary": {
                    "active_medications": medication_count,
                    "active_conditions": condition_count,
                    "known_allergies": allergy_count
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

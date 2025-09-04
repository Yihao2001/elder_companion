# ElderComp Database Setup

This directory contains the PostgreSQL database setup for the ElderComp system, specifically implementing the HCM (Healthcare Memory) and LTM (Long-Term Memory) modules.

## 🏗️ Database Architecture

The database is built on PostgreSQL with the pgvector extension for semantic search capabilities. It consists of two main memory modules:

### Long-Term Memory (LTM)
- **elderly_profiles**: Core elderly person information
- **personal_preferences**: Food, activity, music preferences
- **relationships**: Family and social connections
- **life_memories**: Important life events and memories
- **daily_routines**: Regular activities and schedules

### Healthcare Memory (HCM) - Encrypted
- **medical_records**: Encrypted medical history and diagnoses
- **medications**: Encrypted current and past medications
- **medical_conditions**: Encrypted health conditions
- **allergies**: Encrypted allergy information
- **healthcare_appointments**: Medical appointments and visits

### Shared Components
- **memory_contexts**: Links conversations to LTM/HCM data for RAG retrieval

## 📁 Directory Structure

```
database/
├── docker-compose.yml          # PostgreSQL + pgAdmin containers
├── init.sql                    # Database schema initialization
├── .env.example               # Environment variables template
├── config/
│   └── database.py            # Python database connection manager
├── schemas/                   # Additional schema files (if needed)
├── migrations/                # Database migration files
└── seeds/
    └── sample_data.sql        # Sample data for testing
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose (or Docker Desktop)
- Python 3.9+ (for database connection testing)

### Setup Instructions

1. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

2. **Start the database** (requires Docker)
   ```bash
   # Using Docker Compose V2 (newer)
   docker compose up -d
   
   # Or using Docker Compose V1 (older)
   docker-compose up -d
   ```

3. **Verify database is running**
   ```bash
   docker ps
   ```
   You should see containers named `eldercomp_postgres` and `eldercomp_pgadmin`

4. **Access pgAdmin** (optional)
   - URL: http://localhost:8080
   - Email: admin@eldercomp.com
   - Password: admin

### Alternative Setup (Without Docker)

If Docker is not available, you can set up PostgreSQL manually:

1. **Install PostgreSQL with pgvector extension**
2. **Create database**
   ```sql
   CREATE DATABASE eldercomp;
   ```
3. **Run initialization script**
   ```bash
   psql -U postgres -d eldercomp -f init.sql
   ```
4. **Load sample data** (optional)
   ```bash
   psql -U postgres -d eldercomp -f seeds/sample_data.sql
   ```

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database Connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=eldercomp
DB_USER=postgres
DB_PASSWORD=password

# Security
ENCRYPTION_KEY=your_secure_encryption_key_here
```

### Database Connection (Python)

```python
from database.config.database import init_database, health_check

# Initialize database connection
await init_database()

# Check database health
health = await health_check()
print(health)
```

## 🔒 Security Features

### Data Encryption

Healthcare data is encrypted using PostgreSQL's pgcrypto extension:

- **Encrypted Fields**: Medical records, medications, conditions, allergies
- **Encryption Functions**: `encrypt_sensitive_data()`, `decrypt_sensitive_data()`
- **Key Management**: Environment variable `ENCRYPTION_KEY`

### Example Usage

```sql
-- Encrypt data
INSERT INTO medications (medication_name_encrypted) 
VALUES (encrypt_sensitive_data('Aspirin'));

-- Decrypt data
SELECT decrypt_sensitive_data(medication_name_encrypted) 
FROM medications WHERE id = 'some-uuid';
```

## 🔍 Vector Search

The database supports semantic search using pgvector:

```sql
-- Find similar memories
SELECT *, (1 - (embedding <=> $1::vector)) as similarity_score
FROM life_memories 
WHERE (1 - (embedding <=> $1::vector)) > 0.7
ORDER BY embedding <=> $1::vector 
LIMIT 10;
```

## 📊 Database Schema

### Core Tables

| Table                   | Purpose                         | Encryption |
| ----------------------- | ------------------------------- | ---------- |
| elderly_profiles        | Basic elderly information       | No         |
| personal_preferences    | Preferences and characteristics | No         |
| relationships           | Family and social contacts      | No         |
| life_memories           | Important memories              | No         |
| daily_routines          | Regular activities              | No         |
| medical_records         | Medical history                 | Yes        |
| medications             | Current medications             | Yes        |
| medical_conditions      | Health conditions               | Yes        |
| allergies               | Allergy information             | Yes        |
| healthcare_appointments | Medical appointments            | Yes        |

### Key Features

- **UUID Primary Keys**: All tables use UUID for better security
- **Timestamps**: Automatic created_at and updated_at tracking
- **Vector Embeddings**: Support for semantic search
- **Referential Integrity**: Foreign key constraints
- **Indexes**: Optimized for common query patterns

## 🧪 Testing

### Sample Data

The database includes sample data for testing:

- 3 elderly profiles (Margaret Chen, Robert Lim, Siti Rahman)
- Personal preferences and relationships
- Encrypted medical records and medications
- Life memories and daily routines

### Health Check

```python
from database.config.database import health_check

# Check database status
result = await health_check()
# Returns: {"status": "healthy", "message": "Database is operational", ...}
```

### Connection Test

```bash
# Test database connection
cd database
python -c "
import asyncio
from config.database import init_database, health_check, close_database

async def test():
    await init_database()
    health = await health_check()
    print(f'Database health: {health}')
    await close_database()

asyncio.run(test())
"
```

## 🔧 Maintenance

### Backup

```bash
# Backup database
docker exec eldercomp_postgres pg_dump -U postgres eldercomp > backup.sql

# Restore database
docker exec -i eldercomp_postgres psql -U postgres eldercomp < backup.sql
```

### Monitoring

- **Health endpoint**: Use `health_check()` function
- **Logs**: `docker logs eldercomp_postgres`
- **Performance**: Monitor connection pool usage

## 🚨 Troubleshooting

### Common Issues

1. **Docker not installed**
   - Install Docker Desktop or Docker Engine
   - Verify with `docker --version`

2. **Port conflicts**
   - Change ports in docker-compose.yml if 5432 or 8080 are in use

3. **Permission errors**
   - Ensure Docker has proper permissions
   - On Linux: add user to docker group

4. **Connection failures**
   - Check if containers are running: `docker ps`
   - Verify environment variables in `.env`
   - Check firewall settings

### Logs

```bash
# View PostgreSQL logs
docker logs eldercomp_postgres

# View pgAdmin logs
docker logs eldercomp_pgadmin

# Follow logs in real-time
docker logs -f eldercomp_postgres
```

## 📈 Performance Optimization

### Indexes

The database includes optimized indexes for:
- Vector similarity search (ivfflat)
- Foreign key relationships
- Common query patterns
- Timestamp-based queries

### Connection Pooling

- Minimum connections: 5
- Maximum connections: 20
- Configurable via environment variables

## 🤝 Integration

This database is designed to integrate with:

- **RAG System**: Vector embeddings for semantic search
- **Memory Router**: Context classification and routing
- **Caregiver Interface**: CRUD operations and reporting
- **NLP Processor**: Entity extraction and storage

## 📝 Notes

- **Development Only**: Sample data contains mock medical information
- **Production**: Change default passwords and encryption keys
- **Compliance**: Ensure HIPAA/PDPA compliance for medical data
- **Backup**: Implement regular backup procedures for production

---

**ElderComp Database** - Secure, scalable memory storage for elderly care 🏥💾

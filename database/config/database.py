"""
Database configuration and connection management for ElderComp
Handles PostgreSQL connections with pgvector support for HCM and LTM modules
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncpg
import asyncio
from asyncpg import Pool, Connection
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'eldercomp')
    user: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', 'password')
    schema: str = os.getenv('DB_SCHEMA', 'eldercomp')
    min_connections: int = int(os.getenv('DB_MIN_CONNECTIONS', '5'))
    max_connections: int = int(os.getenv('DB_MAX_CONNECTIONS', '20'))
    encryption_key: str = os.getenv('ENCRYPTION_KEY', 'eldercomp_encryption_key_change_in_production')
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def connection_params(self) -> Dict[str, Any]:
        """Generate connection parameters for asyncpg"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'min_size': self.min_connections,
            'max_size': self.max_connections,
            'command_timeout': 60,
            'server_settings': {
                'search_path': f'{self.schema},public'
            }
        }

class DatabaseManager:
    """Manages database connections and operations for ElderComp"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pool: Optional[Pool] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connection pool"""
        if self._initialized:
            return
        
        try:
            logger.info(f"Initializing database connection pool to {self.config.host}:{self.config.port}")
            self.pool = await asyncpg.create_pool(**self.config.connection_params)
            
            # Test connection and verify extensions
            async with self.pool.acquire() as conn:
                await self._verify_database_setup(conn)
            
            self._initialized = True
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def _verify_database_setup(self, conn: Connection) -> None:
        """Verify that the database is properly set up with required extensions and schema"""
        try:
            # Check if required extensions are installed
            extensions = await conn.fetch("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('uuid-ossp', 'pgcrypto', 'vector')
            """)
            
            installed_extensions = {ext['extname'] for ext in extensions}
            required_extensions = {'uuid-ossp', 'pgcrypto', 'vector'}
            
            if not required_extensions.issubset(installed_extensions):
                missing = required_extensions - installed_extensions
                raise Exception(f"Missing required extensions: {missing}")
            
            # Check if eldercomp schema exists
            schema_exists = await conn.fetchval("""
                SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = $1)
            """, self.config.schema)
            
            if not schema_exists:
                raise Exception(f"Schema '{self.config.schema}' does not exist")
            
            # Check if core tables exist
            core_tables = [
                'elderly_profiles', 'personal_preferences', 'relationships', 
                'life_memories', 'daily_routines', 'medical_records', 
                'medications', 'medical_conditions', 'allergies', 
                'healthcare_appointments', 'memory_contexts'
            ]
            
            for table in core_tables:
                table_exists = await conn.fetchval(f"""
                    SELECT EXISTS(SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = $1 AND table_name = $2)
                """, self.config.schema, table)
                
                if not table_exists:
                    raise Exception(f"Core table '{table}' does not exist in schema '{self.config.schema}'")
            
            logger.info("Database setup verification completed successfully")
            
        except Exception as e:
            logger.error(f"Database setup verification failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            if not self._initialized:
                return {"status": "error", "message": "Database not initialized"}
            
            async with self.get_connection() as conn:
                # Test basic connectivity
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    return {"status": "error", "message": "Basic connectivity test failed"}
                
                # Check pool status
                pool_info = {
                    "size": self.pool.get_size(),
                    "min_size": self.pool.get_min_size(),
                    "max_size": self.pool.get_max_size(),
                    "idle_size": self.pool.get_idle_size()
                }
                
                # Test vector extension
                vector_test = await conn.fetchval("SELECT '[1,2,3]'::vector")
                
                return {
                    "status": "healthy",
                    "message": "Database is operational",
                    "pool_info": pool_info,
                    "extensions": ["uuid-ossp", "pgcrypto", "vector"],
                    "schema": self.config.schema
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query and return results"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_single(self, query: str, *args) -> Any:
        """Execute a query and return single result"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute_scalar(self, query: str, *args) -> Any:
        """Execute a query and return scalar value"""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_transaction(self, queries: list) -> None:
        """Execute multiple queries in a transaction"""
        async with self.get_connection() as conn:
            async with conn.transaction():
                for query, args in queries:
                    await conn.execute(query, *args)

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for common operations
async def get_db_connection():
    """Get database connection (convenience function)"""
    async with db_manager.get_connection() as conn:
        yield conn

async def init_database():
    """Initialize database (convenience function)"""
    await db_manager.initialize()

async def close_database():
    """Close database (convenience function)"""
    await db_manager.close()

async def health_check():
    """Database health check (convenience function)"""
    return await db_manager.health_check()

# Encryption helper functions
async def encrypt_data(data: str, key: Optional[str] = None) -> bytes:
    """Encrypt sensitive data using database function"""
    encryption_key = key or db_manager.config.encryption_key
    async with db_manager.get_connection() as conn:
        return await conn.fetchval(
            "SELECT encrypt_sensitive_data($1, $2)", 
            data, encryption_key
        )

async def decrypt_data(encrypted_data: bytes, key: Optional[str] = None) -> str:
    """Decrypt sensitive data using database function"""
    encryption_key = key or db_manager.config.encryption_key
    async with db_manager.get_connection() as conn:
        return await conn.fetchval(
            "SELECT decrypt_sensitive_data($1, $2)", 
            encrypted_data, encryption_key
        )

# Vector similarity search helper
async def vector_similarity_search(
    table: str, 
    embedding_column: str, 
    query_embedding: list, 
    limit: int = 10,
    similarity_threshold: float = 0.7,
    additional_filters: Optional[str] = None
) -> list:
    """Perform vector similarity search"""
    base_query = f"""
        SELECT *, (1 - ({embedding_column} <=> $1::vector)) as similarity_score
        FROM eldercomp.{table}
        WHERE (1 - ({embedding_column} <=> $1::vector)) > $2
    """
    
    if additional_filters:
        base_query += f" AND {additional_filters}"
    
    base_query += f" ORDER BY {embedding_column} <=> $1::vector LIMIT $3"
    
    async with db_manager.get_connection() as conn:
        return await conn.fetch(base_query, query_embedding, similarity_threshold, limit)

if __name__ == "__main__":
    # Test database connection
    async def test_connection():
        try:
            await init_database()
            health = await health_check()
            print(f"Database health check: {health}")
            await close_database()
        except Exception as e:
            print(f"Database test failed: {e}")
    
    asyncio.run(test_connection())

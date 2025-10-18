import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
from huggingface_hub import login

# -----------------------------------------------------------------------
# 1. Connect to Neon Postgres
# -----------------------------------------------------------------------
load_dotenv()
conn_string = os.getenv("DATABASE_URL")
conn = None

# -----------------------------------------------------------------------
# 2. Load Embedding Model
# -----------------------------------------------------------------------
# login to huggingface to access the model
login(os.getenv("HUGGINGFACE_TOKEN"))
model = SentenceTransformer("google/embeddinggemma-300m")

def embed(text):
    return model.encode(text).tolist()

try:
    with psycopg2.connect(conn_string) as conn:
        print("Connection established")
        with conn.cursor() as cur:

# -----------------------------------------------------------------------
# 3. Enable extensions
# -----------------------------------------------------------------------
            print("1. Enabling extensions.")
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

# -----------------------------------------------------------------------
# 4. Define ENUM Types
# -----------------------------------------------------------------------
            print("2. Defining ENUM types.")
            cur.execute("CREATE TYPE gender_enum AS ENUM ('Male','Female','Other');")
            cur.execute("CREATE TYPE marital_enum AS ENUM ('Single','Married','Widowed','Divorced');")
            cur.execute("CREATE TYPE ltm_category_enum AS ENUM ('personal','family','education','career','lifestyle','finance','legal');")
            cur.execute("CREATE TYPE record_type_enum AS ENUM ('condition','procedure','appointment','medication');")

# -----------------------------------------------------------------------
# 5. Create Tables with UUID & ENUM
# -----------------------------------------------------------------------
            print("3. Creating database schema.")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS elderly_profile (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name BYTEA,              
                date_of_birth BYTEA,     
                gender gender_enum,      
                nationality BYTEA,       
                dialect_group BYTEA,     
                marital_status marital_enum,
                address BYTEA            
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                elderly_id UUID REFERENCES elderly_profile(id),
                content TEXT NOT NULL,
                embedding VECTOR(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                elderly_id UUID REFERENCES elderly_profile(id),
                category ltm_category_enum,
                key TEXT,
                value TEXT,
                embedding VECTOR(768),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS healthcare_records (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                elderly_id UUID REFERENCES elderly_profile(id),
                record_type record_type_enum,
                description TEXT,
                diagnosis_date DATE,
                embedding VECTOR(768),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

# -----------------------------------------------------------------------
# 6. Create index for efficient retrieval
# -----------------------------------------------------------------------
            print("4. Creating index.")
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_stm_embedding
            ON short_term_memory
            USING hnsw (embedding vector_cosine_ops);

            CREATE INDEX IF NOT EXISTS idx_ltm_embedding
            ON long_term_memory
            USING hnsw (embedding vector_cosine_ops);

            CREATE INDEX IF NOT EXISTS idx_health_embedding
            ON healthcare_records
            USING hnsw (embedding vector_cosine_ops);
            """)

# -----------------------------------------------------------------------
# 7. Insert Sample Data
# -----------------------------------------------------------------------
            SECRET_KEY = os.getenv("DATABASE_ENCRYPTION_KEY")

            print("5. Inserting synthetic data.")
            # Elderly profile
            cur.execute(f"""
            INSERT INTO elderly_profile (name, date_of_birth, gender, nationality, dialect_group, marital_status, address)
            VALUES (
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                %s, -- ENUM value
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                %s, -- ENUM value
                pgp_sym_encrypt(%s, %s)
            )
            RETURNING id;
            """, (
                "Tan Ah Lek", SECRET_KEY,
                "1945-03-27", SECRET_KEY,
                "Male",  # ENUM gender_enum
                "Singaporean", SECRET_KEY,
                "Hokkien", SECRET_KEY,
                "Single",  # ENUM marital_enum
                "21 Hui Mui Keng Terrace, i3 Building, Singapore 119613", SECRET_KEY
            ))
            elderly_id = cur.fetchone()[0]

            # Long-term memory facts
            ltm_data = [
                ("career", "occupation", "Retired hawker"),
                ("family", "closest_kin", "Nephew Tan Ma Ne"),
                ("lifestyle", "likes", "Taiwanese soap operas, Channel 8 news, Radio FM 95.8"),
                ("lifestyle", "dislikes", "Computers, digital devices, hot weather"),
            ]
            ltm_records = [(elderly_id, cat, key, val, embed(val)) for cat, key, val in ltm_data]

            execute_values(cur, """
            INSERT INTO long_term_memory (elderly_id, category, key, value, embedding)
            VALUES %s;
            """, ltm_records)

            # Healthcare records
            health_data = [
                ("condition", "Hypertension", "2000-01-01"),
                ("condition", "Diabetes Mellitus", "2010-01-01"),
                ("procedure", "Coronary Artery Disease with angioplasty", "2022-03-15"),
                ("procedure", "Cataract surgery with lens implants", "2024-05-01"),
            ]
            health_records = [(elderly_id, rtype, desc, date, embed(desc)) for rtype, desc, date in health_data]

            execute_values(cur, """
            INSERT INTO healthcare_records (elderly_id, record_type, description, diagnosis_date, embedding)
            VALUES %s;
            """, health_records)

            # Short-term memory
            stm_data = [
                ("I feel dizzy today."),
                ("The chicken rice I ate today was really yummy!")
            ]
            stm_records = [(elderly_id, content, embed(content)) for content in stm_data]

            execute_values(cur, """
            INSERT INTO short_term_memory (elderly_id, content, embedding)
            VALUES %s;
            """, stm_records)

# -----------------------------------------------------------------------
# 8. Commit & Close
# -----------------------------------------------------------------------
            conn.commit()
            print("Migration complete.")

except Exception as e:
    print(f"Connection failed: {e}.")
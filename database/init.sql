-- ElderComp Database Initialization Script
-- This script sets up the PostgreSQL database with pgvector extension
-- and creates the core schema for HCM and LTM modules

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create database schema
CREATE SCHEMA IF NOT EXISTS eldercomp;
SET search_path TO eldercomp, public;

-- Create enum types
CREATE TYPE memory_type AS ENUM ('ltm', 'hcm');
CREATE TYPE data_sensitivity AS ENUM ('public', 'private', 'confidential', 'restricted');
CREATE TYPE relationship_type AS ENUM ('family', 'friend', 'caregiver', 'healthcare_provider', 'neighbor', 'other');
CREATE TYPE medical_record_type AS ENUM ('diagnosis', 'medication', 'allergy', 'procedure', 'lab_result', 'vital_signs', 'appointment');

-- ============================================================================
-- LONG-TERM MEMORY (LTM) TABLES
-- ============================================================================

-- Core elderly person profile
CREATE TABLE elderly_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    preferred_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(20),
    phone_number VARCHAR(20),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Personal preferences and characteristics
CREATE TABLE personal_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL, -- 'food', 'activity', 'music', 'hobby', etc.
    preference_name VARCHAR(200) NOT NULL,
    preference_value TEXT,
    importance_level INTEGER DEFAULT 5 CHECK (importance_level >= 1 AND importance_level <= 10),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Family and social relationships
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    contact_name VARCHAR(200) NOT NULL,
    relationship_type relationship_type NOT NULL,
    phone_number VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    notes TEXT,
    is_primary_contact BOOLEAN DEFAULT FALSE,
    is_emergency_contact BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Life history and important memories
CREATE TABLE life_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    memory_title VARCHAR(200) NOT NULL,
    memory_content TEXT NOT NULL,
    memory_date DATE,
    memory_category VARCHAR(50), -- 'childhood', 'career', 'family', 'achievement', etc.
    importance_level INTEGER DEFAULT 5 CHECK (importance_level >= 1 AND importance_level <= 10),
    embedding vector(1536), -- For semantic search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Personal routines and habits
CREATE TABLE daily_routines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    routine_name VARCHAR(200) NOT NULL,
    routine_description TEXT,
    time_of_day TIME,
    frequency VARCHAR(50), -- 'daily', 'weekly', 'monthly', etc.
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- HEALTHCARE MEMORY (HCM) TABLES - WITH ENCRYPTION
-- ============================================================================

-- Medical records with encryption for sensitive data
CREATE TABLE medical_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    record_type medical_record_type NOT NULL,
    record_title VARCHAR(200) NOT NULL,
    record_content_encrypted BYTEA, -- Encrypted medical content
    record_date DATE NOT NULL,
    healthcare_provider VARCHAR(200),
    sensitivity_level data_sensitivity DEFAULT 'confidential',
    is_active BOOLEAN DEFAULT TRUE,
    embedding vector(1536), -- For semantic search (on non-encrypted metadata)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Current medications with encryption
CREATE TABLE medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    medication_name_encrypted BYTEA NOT NULL, -- Encrypted medication name
    dosage_encrypted BYTEA, -- Encrypted dosage information
    frequency_encrypted BYTEA, -- Encrypted frequency
    prescribing_doctor VARCHAR(200),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    notes_encrypted BYTEA, -- Encrypted notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Medical conditions and diagnoses
CREATE TABLE medical_conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    condition_name_encrypted BYTEA NOT NULL, -- Encrypted condition name
    diagnosis_date DATE,
    severity VARCHAR(20), -- 'mild', 'moderate', 'severe'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'resolved', 'managed'
    treating_physician VARCHAR(200),
    notes_encrypted BYTEA, -- Encrypted notes
    embedding vector(1536), -- For semantic search (on non-encrypted metadata)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Allergies and adverse reactions
CREATE TABLE allergies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    allergen_encrypted BYTEA NOT NULL, -- Encrypted allergen name
    reaction_type VARCHAR(50), -- 'mild', 'moderate', 'severe', 'anaphylaxis'
    symptoms_encrypted BYTEA, -- Encrypted symptoms description
    discovered_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    notes_encrypted BYTEA, -- Encrypted notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Healthcare appointments and visits
CREATE TABLE healthcare_appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    appointment_type VARCHAR(100),
    healthcare_provider VARCHAR(200),
    appointment_date TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    purpose_encrypted BYTEA, -- Encrypted appointment purpose
    notes_encrypted BYTEA, -- Encrypted visit notes
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SHARED TABLES FOR BOTH LTM AND HCM
-- ============================================================================

-- Conversation context and memory retrieval
CREATE TABLE memory_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    elderly_id UUID NOT NULL REFERENCES elderly_profiles(id) ON DELETE CASCADE,
    context_type memory_type NOT NULL,
    reference_id UUID NOT NULL, -- References either LTM or HCM table records
    context_summary TEXT,
    relevance_score FLOAT DEFAULT 0.0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    embedding vector(1536), -- For semantic search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary relationship indexes
CREATE INDEX idx_elderly_profiles_name ON elderly_profiles(first_name, last_name);
CREATE INDEX idx_personal_preferences_elderly_id ON personal_preferences(elderly_id);
CREATE INDEX idx_relationships_elderly_id ON relationships(elderly_id);
CREATE INDEX idx_life_memories_elderly_id ON life_memories(elderly_id);
CREATE INDEX idx_daily_routines_elderly_id ON daily_routines(elderly_id);

-- Medical record indexes
CREATE INDEX idx_medical_records_elderly_id ON medical_records(elderly_id);
CREATE INDEX idx_medical_records_type ON medical_records(record_type);
CREATE INDEX idx_medications_elderly_id ON medications(elderly_id);
CREATE INDEX idx_medical_conditions_elderly_id ON medical_conditions(elderly_id);
CREATE INDEX idx_allergies_elderly_id ON allergies(elderly_id);
CREATE INDEX idx_healthcare_appointments_elderly_id ON healthcare_appointments(elderly_id);

-- Vector similarity search indexes
CREATE INDEX idx_life_memories_embedding ON life_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_medical_records_embedding ON medical_records USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_medical_conditions_embedding ON medical_conditions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_memory_contexts_embedding ON memory_contexts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Composite indexes for common queries
CREATE INDEX idx_memory_contexts_elderly_type ON memory_contexts(elderly_id, context_type);
CREATE INDEX idx_medical_records_elderly_date ON medical_records(elderly_id, record_date DESC);
CREATE INDEX idx_medications_elderly_active ON medications(elderly_id, is_active);

-- ============================================================================
-- FUNCTIONS FOR ENCRYPTION/DECRYPTION
-- ============================================================================

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT, key TEXT DEFAULT 'eldercomp_encryption_key_change_in_production')
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, key);
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data BYTEA, key TEXT DEFAULT 'eldercomp_encryption_key_change_in_production')
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(encrypted_data, key);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all tables with updated_at columns
CREATE TRIGGER update_elderly_profiles_updated_at BEFORE UPDATE ON elderly_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_personal_preferences_updated_at BEFORE UPDATE ON personal_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_relationships_updated_at BEFORE UPDATE ON relationships FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_life_memories_updated_at BEFORE UPDATE ON life_memories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_daily_routines_updated_at BEFORE UPDATE ON daily_routines FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_updated_at BEFORE UPDATE ON medical_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medications_updated_at BEFORE UPDATE ON medications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_conditions_updated_at BEFORE UPDATE ON medical_conditions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_allergies_updated_at BEFORE UPDATE ON allergies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_healthcare_appointments_updated_at BEFORE UPDATE ON healthcare_appointments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL SETUP COMPLETE
-- ============================================================================

-- Grant permissions (adjust as needed for production)
GRANT ALL PRIVILEGES ON SCHEMA eldercomp TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA eldercomp TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA eldercomp TO postgres;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'ElderComp database initialization completed successfully';
    RAISE NOTICE 'Schema: eldercomp';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pgcrypto, vector';
    RAISE NOTICE 'LTM tables: elderly_profiles, personal_preferences, relationships, life_memories, daily_routines';
    RAISE NOTICE 'HCM tables: medical_records, medications, medical_conditions, allergies, healthcare_appointments';
    RAISE NOTICE 'Shared tables: memory_contexts';
    RAISE NOTICE 'Encryption functions: encrypt_sensitive_data(), decrypt_sensitive_data()';
END $$;

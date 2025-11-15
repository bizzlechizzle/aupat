-- ============================================
-- AUPAT Database Initialization Script
-- PostgreSQL 16+
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- Set timezone
SET timezone = 'UTC';

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;

-- Grant privileges
GRANT ALL ON SCHEMA public TO aupat;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aupat;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aupat;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'AUPAT Database initialized successfully at %', NOW();
END $$;

-- Enable pgvector extension for semantic search and AI embeddings
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'pgvector and uuid-ossp extensions enabled successfully.';
END $$;

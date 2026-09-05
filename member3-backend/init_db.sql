-- Optional: run this manually if you prefer raw SQL setup over
-- SQLAlchemy's auto create_all() (which runs automatically on app startup).
-- This mirrors app/models/*.py — keep both in sync if you edit one.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'investigator',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address VARCHAR(100) UNIQUE NOT NULL,
    chain VARCHAR(30) DEFAULT 'ethereum',
    label VARCHAR(255),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    tx_count INTEGER DEFAULT 0,
    latest_risk_score FLOAT,
    latest_risk_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address);

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tx_hash VARCHAR(100) UNIQUE NOT NULL,
    from_address VARCHAR(100) NOT NULL,
    to_address VARCHAR(100) NOT NULL,
    amount FLOAT NOT NULL,
    token_symbol VARCHAR(20) DEFAULT 'ETH',
    chain VARCHAR(30) DEFAULT 'ethereum',
    block_number BIGINT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_address);
CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_address);

CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID NOT NULL REFERENCES wallets(id),
    score FLOAT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    reasons JSONB DEFAULT '[]',
    model_version VARCHAR(50) DEFAULT 'v0-mock',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suspicious_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID NOT NULL REFERENCES wallets(id),
    pattern_type VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    related_addresses JSONB DEFAULT '[]',
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    detected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vasps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    known_addresses JSONB DEFAULT '[]',
    jurisdiction VARCHAR(100),
    entity_type VARCHAR(50) DEFAULT 'exchange',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vasp_attributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID NOT NULL REFERENCES wallets(id),
    vasp_id UUID REFERENCES vasps(id),
    vasp_name_guess VARCHAR(150),
    confidence_score FLOAT DEFAULT 0.0,
    evidence JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID NOT NULL REFERENCES wallets(id),
    file_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'PENDING',
    generated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

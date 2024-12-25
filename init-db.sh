#!/bin/bash
set -e

# Create the scrapeengine database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE scrapeengine'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'scrapeengine')\gexec
EOSQL

# Connect to scrapeengine database and create extensions/tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname scrapeengine <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pgcrypto;

    CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_used_at TIMESTAMP WITH TIME ZONE
    );

    INSERT INTO api_keys (key) VALUES (encode(gen_random_bytes(32), 'hex'))
    ON CONFLICT DO NOTHING;
EOSQL

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Insert initial API key
INSERT INTO api_keys (key) VALUES (encode(gen_random_bytes(32), 'hex')); 
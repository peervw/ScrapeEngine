import psycopg2
from psycopg2.extras import DictCursor
import os
import time
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a PostgreSQL database connection with retries"""
    max_retries = 5
    retry_count = 0
    retry_delay = 1  # seconds

    while retry_count < max_retries:
        try:
            return psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'postgres'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                dbname=os.getenv('POSTGRES_DB', 'scrapeengine'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres')
            )
        except psycopg2.OperationalError as e:
            retry_count += 1
            if retry_count == max_retries:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise
            logger.warning(f"Database connection attempt {retry_count} failed, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

def init_db():
    """Initialize the PostgreSQL database"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Create logs table with JSONB fields for JSON data
        c.execute('''
            CREATE TABLE IF NOT EXISTS scrape_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                runner_id TEXT NOT NULL,
                status TEXT NOT NULL,
                url TEXT NOT NULL,
                duration REAL NOT NULL,
                details JSONB NOT NULL,
                config JSONB,
                result JSONB,
                error TEXT
            )
        ''')
        
        # Create settings table
        c.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Create api_keys table
        c.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP
            )
        ''')

        # Create system_events table
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_events (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                details JSONB
            )
        ''')
        
        # Insert default settings if they don't exist
        c.execute('''
            INSERT INTO settings (key, value)
            VALUES ('num_runners', '3')
            ON CONFLICT (key) DO NOTHING
        ''')
        c.execute('''
            INSERT INTO settings (key, value)
            VALUES ('log_retention_days', '30')
            ON CONFLICT (key) DO NOTHING
        ''')
        c.execute('''
            INSERT INTO settings (key, value)
            VALUES ('webshare_token', '')
            ON CONFLICT (key) DO NOTHING
        ''')
        
        # Generate initial API key if none exists
        c.execute('SELECT COUNT(*) FROM api_keys')
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO api_keys (key) VALUES (encode(gen_random_bytes(32), \'hex\'))')
            logger.info("Generated initial API key")
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise 
from ..session import get_db_connection

async def get_setting(key: str, default_value: str = None) -> str:
    """Get a setting value by key"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT value FROM settings WHERE key = %s', (key,))
        result = c.fetchone()
        return result[0] if result else default_value
    finally:
        conn.close()

async def update_setting(key: str, value: str):
    """Update a setting value"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO settings (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        ''', (key, value))
        conn.commit()
    finally:
        conn.close() 
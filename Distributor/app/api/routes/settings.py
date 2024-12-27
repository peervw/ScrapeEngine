from fastapi import APIRouter, HTTPException, Depends
from ...core.security import token_required
from ...db.session import get_db_connection
from psycopg2.extras import DictCursor

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("")
async def get_settings(authorization: str = Depends(token_required)):
    """Get system settings"""
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=DictCursor)
    c.execute('SELECT key, value FROM settings')
    settings = {row['key']: row['value'] for row in c.fetchall()}
    conn.close()
    return settings

@router.post("")
async def update_settings(
    settings: dict,
    authorization: str = Depends(token_required)
):
    """Update system settings"""
    conn = get_db_connection()
    c = conn.cursor()
    
    for key, value in settings.items():
        c.execute('UPDATE settings SET value = %s WHERE key = %s', (str(value), key))
    
    conn.commit()
    conn.close()
    return {"message": "Settings updated successfully"}

@router.get("/api-key")
async def get_api_key():
    """Get the current API key"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT key FROM api_keys ORDER BY created_at DESC LIMIT 1')
    key = c.fetchone()
    conn.close()
    
    if not key:
        # Return a 404 when no key exists
        raise HTTPException(status_code=404, detail="No API key exists")
    
    return {"key": key[0]}

@router.post("/api-key/regenerate")
async def regenerate_api_key():
    """Generate a new API key"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Generate a new key
    c.execute('INSERT INTO api_keys (key) VALUES (encode(gen_random_bytes(32), \'hex\')) RETURNING key')
    new_key = c.fetchone()[0]
    
    # Delete old keys
    c.execute('DELETE FROM api_keys WHERE key != %s', (new_key,))
    
    conn.commit()
    conn.close()
    
    return {"key": new_key} 
from fastapi import HTTPException, Header
from typing import Optional
import logging
from ..db.session import get_db_connection

logger = logging.getLogger(__name__)

def token_required(authorization: Optional[str] = Header(None)):
    """Validate the authorization token"""
    if not authorization:
        logger.warning("No authorization token provided")
        raise HTTPException(status_code=401, detail="No authorization token provided")
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            logger.warning("Invalid authentication scheme")
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
            
        # Check if token is a valid API key
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id FROM api_keys WHERE key = %s', (token,))
        api_key = c.fetchone()
        
        if api_key:
            # Update last used timestamp
            c.execute('UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = %s', (api_key[0],))
            conn.commit()
            conn.close()
            return authorization
            
        logger.warning("Invalid token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
            
    except ValueError:
        logger.warning("Invalid token format")
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    return authorization 
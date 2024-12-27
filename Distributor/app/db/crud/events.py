from datetime import datetime
import json
import logging
from ..session import get_db_connection
from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)

def store_event(event_data: dict):
    """Store a system event in the database"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO system_events 
        (timestamp, title, description, event_type, severity, details)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        RETURNING id
    ''', (
        datetime.now(),
        event_data['title'],
        event_data['description'],
        event_data['event_type'],
        event_data['severity'],
        json.dumps(event_data.get('details', {}))
    ))
    event_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    return event_id

def get_events(limit: int = 50, offset: int = 0, event_type: str = None):
    """Get paginated system events"""
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=DictCursor)
    
    # Build query based on filters
    query = '''
        SELECT 
            id,
            timestamp,
            title,
            description,
            event_type,
            severity,
            details::text as details
        FROM system_events
    '''
    params = []
    
    if event_type:
        query += ' WHERE event_type = %s'
        params.append(event_type)
    
    # Add ordering and pagination
    query += ' ORDER BY timestamp DESC LIMIT %s OFFSET %s'
    params.extend([limit, offset])
    
    # Get total count
    count_query = 'SELECT COUNT(*) FROM system_events'
    if event_type:
        count_query += ' WHERE event_type = %s'
        c.execute(count_query, [event_type])
    else:
        c.execute(count_query)
    total_count = c.fetchone()[0]
    
    # Get paginated results
    c.execute(query, params)
    
    events = []
    for row in c.fetchall():
        event = dict(row)
        # Convert timestamp to ISO format
        event['timestamp'] = event['timestamp'].isoformat()
        # Parse JSON fields
        if event['details']:
            try:
                event['details'] = json.loads(event['details'])
            except json.JSONDecodeError:
                logger.error(f"Failed to parse details JSON from database")
                event['details'] = {}
        events.append(event)
    
    conn.close()
    return {
        "total": total_count,
        "events": events
    }

def delete_old_events(days: int = 30):
    """Delete events older than specified days"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        DELETE FROM system_events 
        WHERE timestamp < NOW() - INTERVAL '%s days'
    ''', (days,))
    conn.commit()
    conn.close() 
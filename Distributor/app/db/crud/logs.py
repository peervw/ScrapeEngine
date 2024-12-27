from datetime import datetime
import json
import logging
from ..session import get_db_connection
from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)

def store_log(log_data: dict):
    """Store a log entry in the database"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO scrape_logs 
        (timestamp, runner_id, status, url, duration, details, config, result, error)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
    ''', (
        datetime.now(),
        log_data['runner_id'],
        log_data['status'],
        log_data['url'],
        log_data['duration'],
        json.dumps(log_data.get('details', {})),
        json.dumps(log_data.get('config', {})),
        json.dumps(log_data.get('result', {})),
        log_data.get('error')
    ))
    conn.commit()
    conn.close()

def get_logs(limit: int = 50, offset: int = 0):
    """Get paginated scraping logs"""
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=DictCursor)
    
    # Get total count
    c.execute('SELECT COUNT(*) FROM scrape_logs')
    total_count = c.fetchone()[0]
    
    # Get paginated results
    c.execute('''
        SELECT 
            id,
            timestamp,
            runner_id,
            status,
            url,
            duration,
            details::text as details,
            config::text as config,
            result::text as result,
            error
        FROM scrape_logs 
        ORDER BY timestamp DESC 
        LIMIT %s OFFSET %s
    ''', (limit, offset))
    
    logs = []
    for row in c.fetchall():
        log_entry = dict(row)
        # Convert timestamp to ISO format
        log_entry['timestamp'] = log_entry['timestamp'].isoformat()
        # Parse JSON fields
        for field in ['details', 'config', 'result']:
            if log_entry[field]:
                try:
                    log_entry[field] = json.loads(log_entry[field])
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse {field} JSON from database")
                    log_entry[field] = {}
        logs.append(log_entry)
    
    conn.close()
    return {
        "total": total_count,
        "logs": logs
    }

def delete_log(log_id: int) -> bool:
    """Delete a specific log entry by ID"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM scrape_logs WHERE id = %s RETURNING id', (log_id,))
    deleted = c.fetchone()
    conn.commit()
    conn.close()
    return bool(deleted)

def delete_all_logs():
    """Delete all scraping logs from the database"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM scrape_logs')
    conn.commit()
    conn.close() 
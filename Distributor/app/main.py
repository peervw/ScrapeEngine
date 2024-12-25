from fastapi import FastAPI, HTTPException, Depends, Header, Query, Body
from typing import Optional, List
from .services.proxy_manager import ProxyManager
from .services.runner_manager import RunnerManager
from .models import ScrapeRequest
from .config.logging_config import setup_logging
import logging
import os
import asyncio
import psutil
import psycopg2
from psycopg2.extras import DictCursor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import json
from fastapi.middleware.cors import CORSMiddleware
import time
from pydantic import BaseModel

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

# New Pydantic models for proxy management
class ProxyCreate(BaseModel):
    host: str
    port: str
    username: Optional[str] = None
    password: Optional[str] = None

class WebshareToken(BaseModel):
    token: str

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.debug("Starting up distributor service...")
    try:
        # Initialize database
        init_db()
        
        app.state.runner_manager = RunnerManager()
        app.state.proxy_manager = ProxyManager()
        
        # Load Webshare token from settings
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT value FROM settings WHERE key = %s', ('webshare_token',))
        result = c.fetchone()
        if result:
            await app.state.proxy_manager.set_webshare_token(result[0])
        conn.close()
        
        logger.info("Starting proxy maintenance task")
        asyncio.create_task(app.state.proxy_manager.start_proxy_maintenance())
        
        # Start log cleanup task
        async def cleanup_old_logs():
            while True:
                try:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute('SELECT value FROM settings WHERE key = %s', ('log_retention_days',))
                    result = c.fetchone()
                    if not result:
                        logger.warning("Log retention days setting not found, using default of 30 days")
                        retention_days = 30
                    else:
                        retention_days = int(result[0])
                    
                    cutoff_date = datetime.now() - timedelta(days=retention_days)
                    logger.info(f"Cleaning up logs older than {cutoff_date} (retention: {retention_days} days)")
                    
                    c.execute('DELETE FROM scrape_logs WHERE timestamp < %s', (cutoff_date,))
                    deleted_count = c.rowcount
                    conn.commit()
                    logger.info(f"Cleaned up {deleted_count} old log entries")
                    
                    conn.close()
                except Exception as e:
                    logger.error(f"Failed to cleanup logs: {e}", exc_info=True)
                finally:
                    try:
                        conn.close()
                    except:
                        pass
                await asyncio.sleep(24 * 60 * 60)  # Run once per day
        
        # Start the cleanup task
        logger.info("Starting log cleanup task")
        app.state.cleanup_task = asyncio.create_task(cleanup_old_logs())
        logger.info("Startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield  # Server is running
    
    # Cleanup on shutdown
    if hasattr(app.state, 'cleanup_task'):
        logger.info("Cancelling log cleanup task")
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="ScrapeEngine Distributor",
    description="Distributed web scraping service with proxy rotation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Protected endpoints with authentication
@app.post('/api/scrape')
async def scrape_endpoint(
    request: ScrapeRequest,
    authorization: str = Depends(token_required)
):
    try:
        start_time = datetime.now()
        try:
            proxy = await app.state.proxy_manager.get_next_proxy()
        except Exception as e:
            logger.warning(f"Failed to get proxy: {e}, proceeding without proxy")
            proxy = None
            
        task_data = {
            "url": str(request.url),
            "stealth": request.stealth,
            "render": request.render,
            "parse": request.parse,
            "proxy": proxy,
            "headers": None
        }
        
        result = await app.state.runner_manager.distribute_task(task_data)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # Check if the scraping failed
        if result.get("status") == "error":
            if proxy:  # Only update proxy metrics if a proxy was used
                await app.state.proxy_manager.update_proxy_metrics(proxy[0], response_time, False)
            # Store error log
            log_data = {
                "timestamp": start_time.isoformat(),
                "runner_id": result.get("runner_id", "unknown"),
                "status": "failed",
                "url": request.url,
                "duration": response_time,
                "details": result.get("error", "Scraping failed"),
                "config": {
                    "url": str(request.url),
                    "stealth": request.stealth,
                    "render": request.render,
                    "parse": request.parse,
                    "proxy": f"{proxy[0]}:{proxy[1]}" if proxy else "none"
                },
                "error": result.get("error")
            }
            store_log(log_data)
            raise HTTPException(status_code=500, detail=result.get("error", "Scraping failed"))
            
        # Update proxy metrics with response time if proxy was used
        if proxy:
            await app.state.proxy_manager.update_proxy_metrics(proxy[0], response_time, True)
        
        # Store success log
        logger.debug(f"Raw result from runner: {result}")
        
        # Format the response data
        response_data = {
            "url": request.url,
            "stealth": request.stealth,
            "render": request.render,
            "parse": request.parse,
            "proxy_used": f"{proxy[0]}:{proxy[1]}" if proxy else "none",
            "runner_used": result.get("runner_id", "unknown"),
            "method_used": result.get("method_used", "aiohttp"),
            "response_time": response_time,
            "content": {
                "raw_content": result.get("raw_content"),
                "text_content": result.get("text_content"),
                "title": result.get("title"),
                "links": result.get("links", []),
                "parse_error": result.get("parse_error")
            }
        }
        
        # Store log with the same format as the response
        log_data = {
            "timestamp": start_time.isoformat(),
            "runner_id": result.get("runner_id", "unknown"),
            "status": "success",
            "url": request.url,
            "duration": response_time,
            "details": "Successfully scraped content",
            "config": {
                "url": str(request.url),
                "stealth": request.stealth,
                "render": request.render,
                "parse": request.parse,
                "proxy": f"{proxy[0]}:{proxy[1]}" if proxy else "none"
            },
            "result": {
                "proxy_used": f"{proxy[0]}:{proxy[1]}" if proxy else "none",
                "runner_used": result.get("runner_id", "unknown"),
                "method_used": result.get("method_used", "aiohttp"),
                "response_time": response_time,
                "content": {
                    "raw_content": result.get("raw_content"),
                    "text_content": result.get("text_content"),
                    "title": result.get("title"),
                    "links": result.get("links", []),
                    "parse_error": result.get("parse_error")
                }
            }
        }
        
        logger.debug(f"Storing log data: {log_data}")
        store_log(log_data)
        
        return response_data
            
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        if 'proxy' in locals() and proxy:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            await app.state.proxy_manager.update_proxy_metrics(proxy[0], response_time, False)
        # Store error log
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "runner_id": "unknown",
            "status": "failed",
            "url": request.url if 'request' in locals() else "unknown",
            "duration": response_time if 'response_time' in locals() else 0,
            "details": str(e),
            "config": task_data if 'task_data' in locals() else None,
            "error": str(e)
        }
        store_log(log_data)
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/runners/register')
async def register_runner(
    request: dict,
    authorization: str = Depends(token_required)
):
    """Register a new runner with the distributor"""
    logger.info(f"Received registration request: {request}")
    
    runner_id = request.get("runner_id")
    url = request.get("url")
    
    if not runner_id or not url:
        logger.error("Missing runner_id or url in registration request")
        raise HTTPException(status_code=400, detail="Missing runner_id or url")
    
    try:
        await app.state.runner_manager.register_runner(runner_id, url)
        logger.info(f"Successfully registered runner {runner_id} at {url}")
        return {
            "status": "registered",
            "runner_id": runner_id,
            "url": url
        }
    except Exception as e:
        logger.error(f"Failed to register runner {runner_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check(authorization: str = Depends(token_required)):
    return {
        "status": "healthy",
        "version": "1.0.0",
        "active_runners": len(app.state.runner_manager.runners),
        "available_proxies": len(app.state.proxy_manager.available_proxies)
    }

@app.get("/health/public")
async def public_health_check():
    """Public health check endpoint that doesn't require authentication"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/api/debug/proxies")
async def debug_proxies(authorization: str = Depends(token_required)):
    """Debug endpoint to check proxy status"""
    proxy_manager = app.state.proxy_manager
    return {
        "total_proxies": len(proxy_manager.proxies),
        "available_proxies": len(proxy_manager.available_proxies),
        "sample_proxies": [
            {
                "host": proxy_manager.proxies[host]["host"],
                "port": proxy_manager.proxies[host]["port"],
                "last_used": proxy_manager.proxies[host]["last_used"]
            }
            for host in list(proxy_manager.proxies.keys())[:5]
        ]
    }

@app.get("/api/debug/runners")
async def debug_runners(authorization: str = Depends(token_required)):
    """Debug endpoint to check runner status"""
    runner_manager = app.state.runner_manager
    return {
        "active_runners": len(runner_manager.runners),
        "runners": [
            {
                "id": runner_id,
                "url": info["url"],
                "status": info["status"]
            }
            for runner_id, info in runner_manager.runners.items()
        ]
    }

@app.get("/api/debug/test-scrape")
async def test_scrape(authorization: str = Depends(token_required)):
    """Test endpoint to try a scrape operation"""
    try:
        logger.info("Starting test scrape")
        
        # Check if we have runners
        if not app.state.runner_manager.runners:
            logger.error("No runners registered")
            return {
                "status": "error",
                "error": "No runners registered. Please check runner logs."
            }
            
        proxy = await app.state.proxy_manager.get_next_proxy()
        logger.info(f"Got proxy: {proxy[0]}:{proxy[1]}")
        
        task_data = {
            "url": "https://example.com",
            "proxy": proxy,
            "method": "simple",
            "stealth": False,
            "cache": True
        }
        
        result = await app.state.runner_manager.distribute_task(task_data)
        logger.info("Test scrape completed successfully")
        
        return {
            "status": "success",
            "proxy_used": f"{proxy[0]}:{proxy[1]}",
            "result": result,
            "runners_available": len(app.state.runner_manager.runners)
        }
    except Exception as e:
        logger.error(f"Test scrape failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "runners_available": len(app.state.runner_manager.runners)
        }

# Monitoring endpoints for the frontend
@app.get("/api/runners/health")
async def get_runners_health(authorization: str = Depends(token_required)):
    """Get health status of all runners"""
    runners = app.state.runner_manager.runners
    result = []
    
    for runner_id, info in runners.items():
        runner_data = {
            "id": runner_id,
            "status": "active" if info["status"] == "active" else "offline",
            "cpu_usage": psutil.cpu_percent(),  # This would come from the runner's metrics
            "memory_usage": {
                "used": psutil.virtual_memory().used // (1024 * 1024),  # Convert to MB
                "total": psutil.virtual_memory().total // (1024 * 1024)  # Convert to MB
            },
            "active_jobs": 0,  # This would come from the runner's metrics
            "uptime": 0  # This would come from the runner's metrics
        }
        
        if info["status"] == "offline":
            runner_data["last_seen"] = "15m ago"  # This would be calculated
            runner_data["last_status"] = "Connection lost"
            
        result.append(runner_data)
    
    return result

@app.get("/api/metrics")
async def get_system_metrics(authorization: str = Depends(token_required)):
    """Get system-wide metrics"""
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": {
            "used": psutil.virtual_memory().used // (1024 * 1024),  # Convert to MB
            "total": psutil.virtual_memory().total // (1024 * 1024)  # Convert to MB
        },
        "disk_usage": {
            "used": psutil.disk_usage('/').used // (1024 * 1024),  # Convert to MB
            "total": psutil.disk_usage('/').total // (1024 * 1024)  # Convert to MB
        },
        "network": {
            "active_connections": len(app.state.runner_manager.runners),
            "throughput": 0.0,  # This would come from actual network monitoring
            "latency": 0.0  # This would come from actual network monitoring
        }
    }

@app.get("/api/events")
async def get_system_events(authorization: str = Depends(token_required)):
    """Get recent system events"""
    return [
        {
            "title": "System Started",
            "description": "The scraping system has been initialized"
        },
        {
            "title": "Runners Connected",
            "description": f"{len(app.state.runner_manager.runners)} runners are active"
        }
    ]

@app.get("/api/logs")
async def get_scrape_logs(
    authorization: str = Depends(token_required), 
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get recent scraping logs with pagination"""
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

@app.get("/api/settings")
async def get_settings(authorization: str = Depends(token_required)):
    """Get system settings"""
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=DictCursor)
    c.execute('SELECT key, value FROM settings')
    settings = {row['key']: row['value'] for row in c.fetchall()}
    conn.close()
    return settings

@app.post("/api/settings")
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

@app.get("/api/settings/api-key")
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

@app.post("/api/settings/api-key/regenerate")
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

@app.get("/api/proxies")
async def get_proxies(authorization: str = Depends(token_required)):
    """Get all proxies and their stats"""
    proxy_manager = app.state.proxy_manager
    return {
        "total_proxies": len(proxy_manager.proxies),
        "available_proxies": len(proxy_manager.available_proxies),
        "proxies": proxy_manager.get_proxy_stats()
    }

@app.post("/api/proxies")
async def add_proxy(proxy: ProxyCreate, authorization: str = Depends(token_required)):
    """Add a proxy manually"""
    proxy_manager = app.state.proxy_manager
    try:
        await proxy_manager.add_manual_proxy(
            proxy.host,
            proxy.port,
            proxy.username,
            proxy.password
        )
        return {"status": "success", "message": f"Added proxy {proxy.host}:{proxy.port}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/proxies/{host}")
async def delete_proxy(host: str, authorization: str = Depends(token_required)):
    """Delete a proxy"""
    proxy_manager = app.state.proxy_manager
    await proxy_manager.delete_proxy(host)
    return {"status": "success", "message": f"Deleted proxy {host}"}

@app.post("/api/proxies/webshare")
async def set_webshare_token(token: WebshareToken, authorization: str = Depends(token_required)):
    """Set Webshare API token and refresh proxies"""
    proxy_manager = app.state.proxy_manager
    try:
        # Store token in database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO settings (key, value) 
            VALUES ('webshare_token', %s) 
            ON CONFLICT (key) DO UPDATE SET value = %s
        ''', (token.token, token.token))
        conn.commit()
        conn.close()

        # Update proxy manager
        await proxy_manager.set_webshare_token(token.token)
        return {"status": "success", "message": "Updated Webshare token and refreshed proxies"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/proxies/refresh")
async def refresh_proxies(authorization: str = Depends(token_required)):
    """Manually trigger proxy refresh from Webshare"""
    proxy_manager = app.state.proxy_manager
    try:
        await proxy_manager.refresh_proxies()
        return {"status": "success", "message": "Refreshed proxies from Webshare"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

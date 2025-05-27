import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import os

Base = declarative_base()

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)

class ScrapeRecord(Base):
    __tablename__ = "scrape_records"
    
    id = Column(String, primary_key=True)
    url = Column(Text, nullable=False)
    method = Column(String, default="GET")
    status = Column(String, nullable=False)  # success, failed, timeout
    runner_id = Column(String, nullable=True)
    proxy_used = Column(String, nullable=True)
    response_time = Column(Float, nullable=True)  # in seconds
    content_length = Column(Integer, nullable=True)
    api_key_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)

class SystemStats(Base):
    __tablename__ = "system_stats"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    active_jobs = Column(Integer, default=0)
    connected_runners = Column(Integer, default=0)
    total_scrapes_today = Column(Integer, default=0)
    total_scrapes_all_time = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    system_health = Column(Float, default=100.0)
    error_rate = Column(Float, default=0.0)

class DatabaseManager:
    def __init__(self, db_url: str = None):
        if db_url is None:
            db_url = os.getenv("DATABASE_URL", "sqlite:///./scrapeengine.db")
        
        self.engine = create_engine(db_url)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def generate_api_key(self, name: str) -> tuple[str, str]:
        """Generate a new API key and return (key_id, raw_key)"""
        # Generate a secure random key
        raw_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        key_id = secrets.token_urlsafe(8)
        key_hash = f"sk_{raw_key}"
        
        with self.get_session() as session:
            api_key = APIKey(
                id=key_id,
                name=name,
                key_hash=key_hash
            )
            session.add(api_key)
            session.commit()
        
        return key_id, key_hash
    
    def validate_api_key(self, key: str) -> tuple[bool, str]:
        """Validate API key and return (is_valid, key_id)"""
        with self.get_session() as session:
            api_key = session.query(APIKey).filter(
                APIKey.key_hash == key,
                APIKey.is_active == True
            ).first()
            
            if api_key:
                # Update last used and usage count
                api_key.last_used = datetime.utcnow()
                api_key.usage_count += 1
                session.commit()
                return True, api_key.id
            
            return False, ""
    
    def get_api_keys(self) -> list[dict]:
        """Get all API keys (without exposing the actual keys)"""
        with self.get_session() as session:
            keys = session.query(APIKey).all()
            return [
                {
                    "id": key.id,
                    "name": key.name,
                    "created_at": key.created_at.isoformat(),
                    "last_used": key.last_used.isoformat() if key.last_used else None,
                    "is_active": key.is_active,
                    "usage_count": key.usage_count,
                    "key_preview": f"{key.key_hash[:8]}...{key.key_hash[-4:]}"
                }
                for key in keys
            ]
    
    def deactivate_api_key(self, key_id: str) -> bool:
        """Deactivate an API key"""
        with self.get_session() as session:
            api_key = session.query(APIKey).filter(APIKey.id == key_id).first()
            if api_key:
                api_key.is_active = False
                session.commit()
                return True
            return False
    
    def record_scrape(self, url: str, method: str, status: str, runner_id: str = None, 
                     proxy_used: str = None, response_time: float = None, 
                     content_length: int = None, api_key_id: str = None, 
                     error_message: str = None) -> str:
        """Record a scrape attempt"""
        record_id = secrets.token_urlsafe(8)
        
        with self.get_session() as session:
            record = ScrapeRecord(
                id=record_id,
                url=url,
                method=method,
                status=status,
                runner_id=runner_id,
                proxy_used=proxy_used,
                response_time=response_time,
                content_length=content_length,
                api_key_id=api_key_id,
                error_message=error_message
            )
            session.add(record)
            session.commit()
        
        return record_id
    
    def get_recent_scrapes(self, limit: int = 50) -> list[dict]:
        """Get recent scrape records"""
        with self.get_session() as session:
            records = session.query(ScrapeRecord).order_by(
                ScrapeRecord.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": record.id,
                    "url": record.url,
                    "method": record.method,
                    "status": record.status,
                    "runner_id": record.runner_id,
                    "proxy_used": record.proxy_used,
                    "response_time": record.response_time,
                    "content_length": record.content_length,
                    "created_at": record.created_at.isoformat(),
                    "error_message": record.error_message,
                    "api_key_id": record.api_key_id
                }
                for record in records
            ]
    
    def update_system_stats(self, active_jobs: int, connected_runners: int) -> None:
        """Update system statistics"""
        with self.get_session() as session:
            # Calculate stats
            today = datetime.utcnow().date()
            total_scrapes_today = session.query(ScrapeRecord).filter(
                func.date(ScrapeRecord.created_at) == today
            ).count()
            
            total_scrapes_all_time = session.query(ScrapeRecord).count()
            
            # Calculate average response time for successful scrapes in last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            avg_response_time = session.query(func.avg(ScrapeRecord.response_time)).filter(
                ScrapeRecord.created_at >= one_hour_ago,
                ScrapeRecord.status == "success",
                ScrapeRecord.response_time.isnot(None)
            ).scalar() or 0.0
            
            # Calculate error rate for last hour
            total_recent = session.query(ScrapeRecord).filter(
                ScrapeRecord.created_at >= one_hour_ago
            ).count()
            
            failed_recent = session.query(ScrapeRecord).filter(
                ScrapeRecord.created_at >= one_hour_ago,
                ScrapeRecord.status != "success"
            ).count()
            
            error_rate = (failed_recent / total_recent * 100) if total_recent > 0 else 0.0
            
            # Calculate system health (simple heuristic)
            system_health = max(0, 100 - error_rate - (max(0, avg_response_time - 2) * 10))
            
            stats = SystemStats(
                id=secrets.token_urlsafe(8),
                active_jobs=active_jobs,
                connected_runners=connected_runners,
                total_scrapes_today=total_scrapes_today,
                total_scrapes_all_time=total_scrapes_all_time,
                average_response_time=avg_response_time,
                system_health=system_health,
                error_rate=error_rate
            )
            
            session.add(stats)
            session.commit()
    
    def get_latest_stats(self) -> dict:
        """Get the latest system statistics"""
        with self.get_session() as session:
            stats = session.query(SystemStats).order_by(
                SystemStats.timestamp.desc()
            ).first()
            
            if stats:
                return {
                    "active_jobs": stats.active_jobs,
                    "connected_runners": stats.connected_runners,
                    "pages_scraped": stats.total_scrapes_all_time,
                    "system_health": stats.system_health,
                    "total_scrapes_today": stats.total_scrapes_today,
                    "average_response_time": stats.average_response_time,
                    "error_rate": stats.error_rate,
                    "timestamp": stats.timestamp.isoformat()
                }
            
            # Return default values if no stats exist
            return {
                "active_jobs": 0,
                "connected_runners": 0,
                "pages_scraped": 0,
                "system_health": 100.0,
                "total_scrapes_today": 0,
                "average_response_time": 0.0,
                "error_rate": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }

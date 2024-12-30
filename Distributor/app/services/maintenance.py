import asyncio
import logging
from datetime import datetime
from ..db.crud.logs import delete_old_logs
from ..db.crud.events import delete_old_events, store_event
from ..db.crud.settings import get_setting

logger = logging.getLogger(__name__)

class MaintenanceService:
    def __init__(self):
        self._running = False
        self._last_cleanup = datetime.min

    async def start(self):
        """Start the maintenance service"""
        self._running = True
        while self._running:
            try:
                # Get retention period from settings
                retention_days = int(await get_setting('log_retention_days', '30'))
                
                # Run cleanup
                deleted_logs = delete_old_logs(retention_days)
                deleted_events = delete_old_events(retention_days)
                
                # Log cleanup event if any deletions occurred
                if deleted_logs or deleted_events:
                    store_event({
                        "title": "System Maintenance",
                        "description": f"Cleaned up {deleted_logs} logs and {deleted_events} events older than {retention_days} days",
                        "event_type": "maintenance",
                        "severity": "info"
                    })
                
                logger.info(f"Maintenance complete: removed {deleted_logs} logs and {deleted_events} events")
                
                # Run every 24 hours
                await asyncio.sleep(24 * 60 * 60)
                
            except Exception as e:
                logger.error(f"Error during maintenance: {e}")
                # On error, wait 1 hour before retry
                await asyncio.sleep(60 * 60)

    async def stop(self):
        """Stop the maintenance service"""
        self._running = False 
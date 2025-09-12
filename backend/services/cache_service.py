from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.models.database_models import SearchCache
import logging

logger = logging.getLogger(__name__)

def purge_old_cache_entries(db: Session, days: int = 30) -> int:
    """
    Deletes SearchCache entries older than `days`. Returns count of deleted records.
    Pure function — does not close the DB session.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted_count = db.query(SearchCache).filter(SearchCache.timestamp < cutoff).delete()
    logger.info(f"Purged {deleted_count} SearchCache records older than {days} days.")
    return deleted_count

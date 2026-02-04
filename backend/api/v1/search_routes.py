from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.configurations.database import get_db
from backend.adapters.spotify_adapter import SpotifyAdapter
from backend.models.database_models import PlatformAccount, SearchCache
from backend.services.data_sync_service import get_valid_spotify_access_token
from backend.utils.normalize_text import normalize_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")  
def search_tracks(
    query: str = Query(..., description="User search query"),
    platform_account_id: int = Query(..., description="Platform account ID"),
    db: Session = Depends(get_db),
):
    """
    Search for tracks:
    1. Try SearchCache (cache-first).
    2. If not cached, query Spotify via SpotifyAdapter.
    3. Save result back to cache.
    """

    norm_q = normalize_query(query)

    # 1) CACHE FIRST
    cached = (
        db.query(SearchCache)
        .filter(
            SearchCache.platform_account_id == platform_account_id,
            SearchCache.normalized_query == norm_q
        )
        .first()
    )
    if cached:
        logger.info("SearchCache hit for query='%s'", norm_q)
        return {"status": "ok", "results": [{"track_uri": cached.track_uri}], "meta": cached.meta_data}

    # 2) Cache miss -> query Spotify
    account = db.query(PlatformAccount).filter_by(id=platform_account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="PlatformAccount not found")
    if not account.refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available for this account")

    access_token = get_valid_spotify_access_token(db, account)
    adapter = SpotifyAdapter(access_token=access_token)
    uris = adapter.search_track_uris(db, platform_account_id, query, limit=5)

    # 3) Save top result to cache
    if uris:
        try:
            sc = SearchCache(
                platform_account_id=platform_account_id,
                normalized_query=norm_q,
                track_uri=uris[0],
                meta_data={"query": query}
            )
            db.add(sc)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to write SearchCache (non-fatal)")

    results = [{"track_uri": uri} for uri in uris]
    return {"status": "ok", "results": results}
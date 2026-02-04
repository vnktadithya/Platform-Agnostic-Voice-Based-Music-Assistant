import pytest
from backend.models.database_models import PlatformAccount
from backend.models.database_models import SearchCache
from backend.utils.normalize_text import normalize_query
from backend.adapters.spotify_adapter import SpotifyAdapter





def test_search_hits_cache_first(client, test_db, monkeypatch, platform_account_fixture):

    # prevent real token fetch in case route tries
    monkeypatch.setattr(
        "backend.api.v1.search_routes.get_new_access_token",
        lambda rt: "dummy_token"
    )

    norm_q = normalize_query("Bad Romance Lady Gaga")
    sc = SearchCache(
        platform_account_id=platform_account_fixture.id,  # Use real account ID
        normalized_query=norm_q,
        track_uri="spotify:track:Q123",
        meta_data={"track_name": "Bad Romance"}
    )
    test_db.add(sc)
    test_db.commit()

    from backend.adapters.spotify_adapter import SpotifyAdapter
    def fail_search(*args, **kwargs):
        raise AssertionError("Spotify API should not have been called for cache hit")
    monkeypatch.setattr(SpotifyAdapter, "search_track_uris", fail_search)

    resp = client.get("/v1/search", params={
        "query": "bad romance lady gaga",
        "platform_account_id": platform_account_fixture.id
    })
    assert resp.status_code == 200


def test_search_fallback_to_api_and_populate_cache(client, test_db, monkeypatch, platform_account_fixture):

    # patch token fetch to avoid network
    monkeypatch.setattr(
        "backend.api.v1.search_routes.get_new_access_token",
        lambda rt: "dummy_token"
    )

    querytxt = "Unique Song Query"
    fake_result_uris = ["spotify:track:NEWX"]

    monkeypatch.setattr(
        SpotifyAdapter, "search_track_uris",
        lambda self, db, platform_account_id, query, limit=5: fake_result_uris
    )

    resp = client.get("/v1/search", params={
        "query": querytxt,
        "platform_account_id": platform_account_fixture.id
    })
    assert resp.status_code == 200

    cached = test_db.query(SearchCache).filter_by(
        normalized_query=normalize_query(querytxt)
    ).first()
    assert cached is not None

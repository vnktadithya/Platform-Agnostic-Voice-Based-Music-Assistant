import datetime
from backend.utils.normalize_text import normalize_query
from backend.models.database_models import SearchCache
from backend.adapters.spotify_adapter import SpotifyAdapter
from backend.services.cache_service import purge_old_cache_entries

def test_search_cache_hit(test_db, monkeypatch):
    norm_q = normalize_query("Bohemian Rhapsody")
    cache = SearchCache(platform_account_id=1, normalized_query=norm_q, track_uri="spotify:track:Q1", meta_data={})
    test_db.add(cache)
    test_db.commit()

    mock_sp = type("MockSp", (), {"search": lambda *a, **k: None})()

    # Patch __init__ so that it sets self.sp to our mock_sp
    def mock_init(self, access_token):
        self.sp = mock_sp

    monkeypatch.setattr(SpotifyAdapter, "__init__", mock_init)

    adapter = SpotifyAdapter(access_token="dummy_token")
    uris = adapter.search_track_uris(test_db, 1, "Bohemian   rhapsody")
    assert "spotify:track:Q1" in uris


def test_search_cache_miss_and_insert(monkeypatch, test_db):
    def mock_search(*args, **kwargs):
        return {
            "tracks": {
                "items": [{
                    "uri": "spotify:track:newuri",
                    "name": "Something New",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "duration_ms": 100
                }]
            }
        }

    mock_sp = type("MockSp", (), {"search": mock_search})()

    def mock_init(self, access_token):
        self.sp = mock_sp

    monkeypatch.setattr(SpotifyAdapter, "__init__", mock_init)

    adapter = SpotifyAdapter(access_token="dummy_token")
    uris = adapter.search_track_uris(test_db, 1, "Unique Query Not In Cache")
    assert "spotify:track:newuri" in uris

    norm_q = normalize_query("Unique Query Not In Cache")
    assert test_db.query(SearchCache).filter_by(normalized_query=norm_q).first() is not None


def test_purge_expired_search_cache(test_db):
    old_cache = SearchCache(
        platform_account_id=1,
        normalized_query="old",
        track_uri="t1",
        meta_data={},
        timestamp=datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    )
    test_db.add(old_cache)
    test_db.commit()

    count = purge_old_cache_entries(test_db, days=365 * 10)
    test_db.commit()

    assert count == 1
    assert test_db.query(SearchCache).filter_by(normalized_query="old").first() is None

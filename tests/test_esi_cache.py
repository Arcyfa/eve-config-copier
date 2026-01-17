import json
from types import SimpleNamespace

import pytest

from eve_backend.cache import CacheManager
from eve_backend import esi_client


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, content=b''):
        self.status_code = status_code
        self._json = json_data or {}
        self.content = content

    def json(self):
        return self._json


def test_get_character_caches_json(tmp_path, monkeypatch):
    cache = CacheManager(base=tmp_path)
    char_id = 12345
    payload = {"name": "TestChar", "corporation_id": 54321}

    called = {"count": 0}

    def fake_get(url, timeout=10):
        called["count"] += 1
        assert str(char_id) in url
        return DummyResponse(status_code=200, json_data=payload)

    # requests is imported lazily inside esi_client; inject a fake requests module
    import types, sys
    fake_requests = types.SimpleNamespace(get=fake_get)
    monkeypatch.setitem(sys.modules, 'requests', fake_requests)

    # first call should fetch and cache
    res = esi_client.get_character(char_id, cache=cache)
    assert res == payload
    p = cache.json_path(str(char_id), 'char')
    assert p.exists()
    assert called["count"] == 1

    # second call should return cached result and not call requests.get
    def fail_get(*args, **kwargs):
        raise AssertionError('requests.get should not be called on cached data')

    # replace the fake module's get to ensure no network call
    sys.modules['requests'].get = fail_get
    res2 = esi_client.get_character(char_id, cache=cache)
    assert res2 == payload


def test_fetch_character_image_caches_file(tmp_path, monkeypatch):
    cache = CacheManager(base=tmp_path)
    char_id = 22222
    img_bytes = b'PNGDATA'

    def fake_get(url, timeout=10):
        assert str(char_id) in url
        return DummyResponse(status_code=200, content=img_bytes)

    import types, sys
    fake_requests = types.SimpleNamespace(get=fake_get)
    monkeypatch.setitem(sys.modules, 'requests', fake_requests)

    p = esi_client.fetch_character_image(char_id, cache=cache)
    assert p.exists()
    assert p.read_bytes() == img_bytes

    # subsequent call should not hit network
    def fail_get(*args, **kwargs):
        raise AssertionError('requests.get should not be called for cached image')

    sys.modules['requests'].get = fail_get
    p2 = esi_client.fetch_character_image(char_id, cache=cache)
    assert p2 == p

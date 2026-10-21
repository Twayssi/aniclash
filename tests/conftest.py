import pytest
from fastapi.testclient import TestClient
import main
from fakeredis import FakeRedis


@pytest.fixture
def client(monkeypatch):
    fake_redis = FakeRedis(decode_responses=True)
    monkeypatch.setattr(main, 'client', fake_redis)
    
    with TestClient(main.app) as test_client:
        yield test_client
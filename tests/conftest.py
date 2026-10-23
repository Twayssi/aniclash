import pytest
import models
from fastapi.testclient import TestClient
import main
from fakeredis import FakeRedis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base


test_engine = create_engine('sqlite:///./test.db', connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(bind=test_engine)


def get_test_db():
    test_db = TestSessionLocal()
    try:
        yield test_db
    finally:
        test_db.close()


@pytest.fixture
def client(monkeypatch):
    fake_redis = FakeRedis(decode_responses=True)
    monkeypatch.setattr(main, 'client', fake_redis)
    main.app.dependency_overrides[main.get_db] = get_test_db
    with TestClient(main.app) as test_client:
        Base.metadata.create_all(bind=test_engine)
        yield test_client
        Base.metadata.drop_all(bind=test_engine)
        main.app.dependency_overrides.clear()
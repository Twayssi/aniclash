import pytest
import models
from security import decode_token
from fastapi.testclient import TestClient
import main
from fakeredis import FakeRedis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import uuid

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


@pytest.fixture
def user_factory(client):
    def create_user():
        user_salt = uuid.uuid4().hex
        response = client.post(url='/register', json={'username': user_salt, 'password': 'test', 'email': f'{user_salt}@example.com'})
        response = client.post(url='/login', data={'username': user_salt, 'password': 'test'})
        user_token = response.json()['access_token']
        user_id = decode_token(user_token)['sub']
        return {'user_id': user_id, 'user_token': user_token}
    yield create_user


@pytest.fixture
def create_room(client, user_factory):
    host_token = user_factory()['user_token']
    response =  client.post(url='/api/rooms', headers={'Authorization': f'Bearer {host_token}'}, json={'room_name': 'test_room'})
    created_room_dict = response.json()
    yield {'room_id': created_room_dict['room_id'], 'host_id': created_room_dict['host_id'], 'host_token': host_token}
import uuid


def test_get_wrong_room_info(client):
    response = client.get('/api/rooms/wrong_id/info')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Комната не найдена'


def test_room_creating(client):
    login = uuid.uuid4().hex
    response = client.post(url='/register', json={'username': login, 'password': 'test', 'email': f'{login}@example.com'})
    response = client.post(url='/login', data={'username': login, 'password': 'test'})
    user_token = response.json()['access_token']
    
    response = client.post(url='/api/rooms', headers={'Authorization': f'Bearer {user_token}'}, json={'room_name': f'{login} room'})
    
    
    assert response.status_code == 200
    assert 'room_id' in response.json()
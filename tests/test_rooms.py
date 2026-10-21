def test_get_wrong_room_info(client):
    response = client.get('/api/rooms/wrong_id/info')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Комната не найдена'


# def test_room_creating(client):
#     response = client.post(url='/register', json={'username': 'test', 'password': 'test', 'email': 'test@example.com'})
#     # user_token = response
#     print(response.json())
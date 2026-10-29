def test_get_wrong_room_info(client):
    response = client.get('/api/rooms/wrong_id/info')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Комната не найдена'


def test_room_creating(client, user_factory):
    user_token = user_factory()['user_token']
    response = client.post(url='/api/rooms', headers={'Authorization': f'Bearer {user_token}'}, json={'room_name': 'test room','max_members': 4})
    
    assert response.status_code == 200
    assert 'room_id' in response.json()


def test_join_room(client, user_factory, create_room):
    room_dict = create_room
    room_id = room_dict['room_id']

    user = user_factory()
    user_id = user['user_id']
    user_token = user['user_token']

    response = client.post(url=f'/api/rooms/{room_id}/join', headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200
    assert int(user_id) in response.json()


def test_join_twice(client, user_factory, create_room):
    room_dict = create_room
    room_id = room_dict['room_id']

    user = user_factory()
    user_id = user['user_id']
    user_token = user['user_token']
    
    response = client.post(url=f'/api/rooms/{room_id}/join', headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200
    response = client.post(url=f'/api/rooms/{room_id}/join', headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200
    response = client.get(url=f'/api/rooms/{room_id}/info')
    assert len(response.json()['members']) == 2


def test_default_member_leave(client, user_factory, create_room):
    room_dict = create_room
    room_id = room_dict['room_id']

    user = user_factory()
    user_id = user['user_id']
    user_token = user['user_token']

    members_list = client.post(url=f'/api/rooms/{room_id}/join', headers= {'Authorization': f'Bearer {user_token}'})

    assert members_list.status_code == 200
    assert int(user_id) in members_list.json()
    
    response = client.delete(url=f'/api/rooms/{room_id}/leave', headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200

    response = client.get(url=f'/api/rooms/{room_id}/info')
    assert not int(user_id) in response.json()['members']


def test_host_leave(client, user_factory, create_room):
    room_dict = create_room
    host_id = room_dict['host_id']
    host_token = room_dict['host_token']
    room_id = room_dict['room_id']

    user = user_factory()
    user_id = user['user_id']
    user_token = user['user_token']
    
    response = client.post(url=f'/api/rooms/{room_id}/join', headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200
    
    response = client.delete(url=f'/api/rooms/{room_id}/leave', headers={'Authorization': f'Bearer {host_token}'})
    assert response.status_code == 200
    
    response = client.get(url=f'/api/rooms/{room_id}/info')
    assert response.status_code == 200
    assert not host_id in response.json()['members']
    assert response.json()['host_id'] == int(user_id)


def test_last_leave(client, create_room):
    room_dict = create_room
    host_token = room_dict['host_token']
    room_id = room_dict['room_id']

    response = client.delete(url=f'/api/rooms/{room_id}/leave', headers={'Authorization': f'Bearer {host_token}'})
    assert response.status_code == 200

    response = client.get(url=f'/api/rooms/{room_id}/info')
    assert response.status_code == 404

def test_crowded_room(client, user_factory, create_room):
    room_dict = create_room
    room_id = room_dict['room_id']
    room_max_members = room_dict['max_members']
    for user in range(room_max_members - 1):
        user = user_factory()
        user_token = user['user_token']
        response = client.post(url=f'/api/rooms/{room_id}/join', headers={'Authorization': f'Bearer {user_token}'})
        assert response.status_code == 200
    assert len(response.json()) == room_max_members
    extra_user = user_factory()
    extra_user_token = extra_user['user_token']
    response = client.post(url=f'/api/rooms/{room_id}/join', headers={'Authorization': f'Bearer {extra_user_token}'})
    assert response.status_code == 400
    assert response.json()['detail'] == 'Комната переполнена'
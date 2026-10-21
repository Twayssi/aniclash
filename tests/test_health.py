def test_health(client):
    response = client.get('/health')
    
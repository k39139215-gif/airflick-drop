import os
import sys
import io
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import app, bump_file_timestamp, get_lan_ip

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Verifies that the index page returns 200 OK and serves index.html."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"AirFlick" in response.data

def test_tunnel_info_endpoint(client):
    """Verifies /api/tunnel_info returns JSON with lan_ip and status."""
    response = client.get('/api/tunnel_info')
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"
    assert "lan_ip" in data
    assert data["port"] == 5050

def test_bump_file_timestamp(tmp_path):
    """Verifies that bump_file_timestamp updates mtime to current second."""
    test_file = tmp_path / "test_artifact.txt"
    test_file.write_text("airflick payload")
    
    past_time = time.time() - 3600
    os.utime(str(test_file), (past_time, past_time))
    assert os.path.getmtime(str(test_file)) < time.time() - 1000
    
    bump_file_timestamp(str(test_file))
    assert abs(os.path.getmtime(str(test_file)) - time.time()) < 5

def test_lan_ip_detection():
    """Verifies get_lan_ip returns a valid string."""
    ip = get_lan_ip()
    assert isinstance(ip, str)
    assert len(ip.split('.')) == 4

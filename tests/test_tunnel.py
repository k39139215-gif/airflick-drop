import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tunnel import CloudflareTunnel, ensure_cloudflared

def test_cloudflared_binary_availability():
    """Ensures cloudflared executable can be located or resolved."""
    exe = ensure_cloudflared()
    assert exe is not None
    assert os.path.exists(exe)

def test_tunnel_instance_initialization():
    """Ensures CloudflareTunnel initializes with default port."""
    t = CloudflareTunnel(5050)
    assert t.port == 5050
    assert t.is_running is False
    assert t.public_url is None

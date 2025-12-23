import json
import threading
from http.client import HTTPConnection

import chess
import pytest

from server.http_server import make_http_server
from server.chess_state import SandboxState
from server.analysis import StubAnalysisEngine


@pytest.fixture
def http_server():
    state = SandboxState()
    engine = StubAnalysisEngine()

    server = make_http_server("127.0.0.1", 0, state, engine)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield host, port, state

    server.shutdown()
    server.server_close()
    
    
def test_state_initial(http_server):
    host, port, state = http_server
    conn = HTTPConnection(host, port)

    conn.request("GET", "/state")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert response.status == 200
    assert data["type"] == "state"

    assert data["turn"] == "white"
    assert data["move_number"] == 1
    assert data["last_move"] is None

    analysis = data["analysis"]
    assert "depth" in analysis
    assert isinstance(analysis["lines"], list)
    
    
def test_state_after_move(http_server):
    host, port, state = http_server
    conn = HTTPConnection(host, port)

    # play e2e4
    conn.request(
        "POST",
        "/play_move",
        body=json.dumps({"move": "e2e4"}),
        headers={"Content-Type": "application/json"},
    )
    conn.getresponse().read()

    # fetch state
    conn.request("GET", "/state")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert data["turn"] == "black"
    assert data["move_number"] == 1
    assert data["last_move"] == "e2e4"
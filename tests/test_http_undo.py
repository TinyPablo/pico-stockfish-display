import json
import threading

import chess
import pytest
from http.client import HTTPConnection

from server.http_server import make_http_server
from server.chess_state import SandboxState
from server.analysis import StubAnalysisEngine


@pytest.fixture
def http_server():
    """
    Real HTTP server with isolated state per test.
    """
    state = SandboxState()
    engine = StubAnalysisEngine()

    server = make_http_server("127.0.0.1", 0, state, engine)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield host, port, state

    server.shutdown()
    server.server_close()
    
    
def test_undo_empty_game(http_server):
    host, port, state = http_server
    conn = HTTPConnection(host, port)

    conn.request("POST", "/undo")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert response.status == 200
    assert data["type"] == "move_result"
    assert data["ok"] is False

    # Board unchanged
    assert state.board.move_stack == []
    assert state.board.turn is chess.WHITE
    
    
def test_undo_after_single_move(http_server):
    host, port, state = http_server
    conn = HTTPConnection(host, port)

    # Play a legal move
    conn.request(
        "POST",
        "/play_move",
        body=json.dumps({"move": "e2e4"}),
        headers={"Content-Type": "application/json"},
    )
    conn.getresponse().read()

    assert state.board.peek().uci() == "e2e4"
    assert state.board.turn is chess.BLACK

    # Undo it
    conn.request("POST", "/undo")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert response.status == 200
    assert data["ok"] is True

    # Board fully reverted
    assert state.board.move_stack == []
    assert state.board.turn is chess.WHITE    
    
    
def test_undo_twice_is_safe(http_server):
    host, port, state = http_server
    conn = HTTPConnection(host, port)

    # Play one move
    conn.request(
        "POST",
        "/play_move",
        body=json.dumps({"move": "e2e4"}),
        headers={"Content-Type": "application/json"},
    )
    conn.getresponse().read()

    # First undo
    conn.request("POST", "/undo")
    conn.getresponse().read()

    # Second undo (should be safe)
    conn.request("POST", "/undo")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert response.status == 200
    assert data["ok"] is False
    assert state.board.move_stack == []
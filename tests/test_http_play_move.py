import json
import threading

import pytest
import chess
from http.client import HTTPConnection

from server.http_server import make_http_server
from server.chess_state import SandboxState
from server.analysis import StubAnalysisEngine


@pytest.fixture
def http_server():
    """
    Start a real HTTP server in a background thread
    with isolated state and stub analysis.
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


def test_play_move_valid(http_server):
    host, port, state = http_server
    conn = HTTPConnection(host, port)

    payload = json.dumps({"move": "e2e4"})
    conn.request(
        "POST",
        "/play_move",
        body=payload,
        headers={"Content-Type": "application/json"},
    )

    response = conn.getresponse()
    data = json.loads(response.read())

    assert response.status == 200
    assert data["type"] == "move_result"
    assert data["ok"] is True

    # board state actually changed
    assert state.board.peek().uci() == "e2e4"
    assert state.board.turn is chess.BLACK


def test_play_move_illegal(http_server):
    host, port, state = http_server
    conn = HTTPConnection(host, port)

    payload = json.dumps({"move": "e2e5"})  # illegal pawn move
    conn.request(
        "POST",
        "/play_move",
        body=payload,
        headers={"Content-Type": "application/json"},
    )

    response = conn.getresponse()
    data = json.loads(response.read())

    assert response.status == 200
    assert data["type"] == "move_result"
    assert data["ok"] is False
    assert data["reason"] == "illegal_move"

    # board must not change
    assert state.board.move_stack == []
    assert state.board.turn is chess.WHITE


def test_play_move_missing_body(http_server):
    host, port, _ = http_server
    conn = HTTPConnection(host, port)

    conn.request("POST", "/play_move")

    response = conn.getresponse()
    assert response.status == 400


def test_play_move_missing_move_field(http_server):
    host, port, _ = http_server
    conn = HTTPConnection(host, port)

    payload = json.dumps({})
    conn.request(
        "POST",
        "/play_move",
        body=payload,
        headers={"Content-Type": "application/json"},
    )

    response = conn.getresponse()
    assert response.status == 400
import json
import threading
from http.client import HTTPConnection

import pytest
import chess

from server.http_server import make_http_server
from server.chess_state import SandboxState
from server.analysis import StubAnalysisEngine


@pytest.fixture
def http_server():
    state = SandboxState()
    engine = StubAnalysisEngine()

    state = SandboxState()
    engine = StubAnalysisEngine()

    moves = [
        "f2f3",
        "e7e5",
        "g2g4",
        "d8h4",
    ]

    for move in moves:
        state.board.push_uci(move)

    assert state.board.is_checkmate()

    server = make_http_server("127.0.0.1", 0, state, engine)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield host, port

    server.shutdown()
    server.server_close()


def test_undo_after_checkmate(http_server):
    host, port = http_server
    conn = HTTPConnection(host, port)

    # verify checkmate state
    conn.request("GET", "/state")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert data["game_over"] is True
    assert data["checkmate"] is True

    # undo last move
    conn.request("POST", "/undo")
    response = conn.getresponse()
    undo_result = json.loads(response.read())

    assert undo_result["ok"] is True

    # verify game resumed
    conn.request("GET", "/state")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert data["game_over"] is False
    assert data["checkmate"] is False
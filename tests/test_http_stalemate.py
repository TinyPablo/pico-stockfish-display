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

    # force stalemate position
    state.board = chess.Board(
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    )

    server = make_http_server("127.0.0.1", 0, state, engine)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield host, port

    server.shutdown()
    server.server_close()


def test_stalemate_state(http_server):
    host, port = http_server
    conn = HTTPConnection(host, port)

    conn.request("GET", "/state")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert data["game_over"] is True
    assert data["stalemate"] is True
    assert data["checkmate"] is False
    assert data["winner"] is None
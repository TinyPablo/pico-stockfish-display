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

    # White pawn ready to promote on a8
    state.board = chess.Board("8/P7/8/8/8/8/8/k6K w - - 0 1")

    server = make_http_server("127.0.0.1", 0, state, engine)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield host, port

    server.shutdown()
    server.server_close()


def test_play_move_accepts_promotion_uci(http_server):
    host, port = http_server
    conn = HTTPConnection(host, port)

    conn.request(
        "POST",
        "/play_move",
        body=json.dumps({"move": "a7a8q"}),
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    data = json.loads(resp.read())
    assert data["ok"] is True

    conn.request("GET", "/state")
    resp = conn.getresponse()
    state = json.loads(resp.read())

    assert state["last_move"] == "a7a8q"
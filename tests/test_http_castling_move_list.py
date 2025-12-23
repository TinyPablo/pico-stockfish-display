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

    # Only kings + rooks, all castling rights, empty between squares
    state.board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")

    server = make_http_server("127.0.0.1", 0, state, engine)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield host, port

    server.shutdown()
    server.server_close()


def test_move_list_includes_castling_squares_for_white_king(http_server):
    host, port = http_server
    conn = HTTPConnection(host, port)

    conn.request(
        "POST",
        "/move_list",
        body=json.dumps({"from": "e1"}),
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    data = json.loads(resp.read())
    assert resp.status == 200
    assert data["type"] == "move_list"
    assert data["from"] == "e1"

    # Castling destinations are king target squares in UCI
    assert "g1" in data["moves"]  # O-O
    assert "c1" in data["moves"]  # O-O-O
import json
import threading
from http.client import HTTPConnection

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


def post(conn, path, payload):
    conn.request(
        "POST",
        path,
        body=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    conn.getresponse().read()


def test_checkmate_fools_mate(http_server):
    host, port, _ = http_server
    conn = HTTPConnection(host, port)

    post(conn, "/play_move", {"move": "f2f3"})
    post(conn, "/play_move", {"move": "e7e5"})
    post(conn, "/play_move", {"move": "g2g4"})
    post(conn, "/play_move", {"move": "d8h4"})

    conn.request("GET", "/state")
    response = conn.getresponse()
    data = json.loads(response.read())

    assert data["game_over"] is True
    assert data["checkmate"] is True
    assert data["stalemate"] is False
    assert data["winner"] == "black"
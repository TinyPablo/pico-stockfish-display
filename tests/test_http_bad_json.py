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

    yield host, port

    server.shutdown()
    server.server_close()


def test_play_move_bad_json_returns_400(http_server):
    host, port = http_server
    conn = HTTPConnection(host, port)

    conn.request(
        "POST",
        "/play_move",
        body=b'{"move":',  # invalid JSON
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    resp.read()
    assert resp.status == 400


def test_move_list_bad_json_returns_400(http_server):
    host, port = http_server
    conn = HTTPConnection(host, port)

    conn.request(
        "POST",
        "/move_list",
        body=b'{"from":',  # invalid JSON
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    resp.read()
    assert resp.status == 400
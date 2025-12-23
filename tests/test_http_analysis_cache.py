import json
import threading
from http.client import HTTPConnection

import pytest

from server.http_server import make_http_server
from server.chess_state import SandboxState
from server.analysis import AnalysisLine, AnalysisResult


class CountingEngine:
    def __init__(self):
        self.calls = 0

    def analyse(self, board):
        self.calls += 1
        return AnalysisResult(
            depth=1,
            lines=[
                AnalysisLine(move="e2e4", eval=0.0),
                AnalysisLine(move="d2d4", eval=0.0),
                AnalysisLine(move="g1f3", eval=0.0),
            ],
        )


@pytest.fixture
def http_server():
    state = SandboxState()
    engine = CountingEngine()

    server = make_http_server("127.0.0.1", 0, state, engine)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield host, port, state, engine

    server.shutdown()
    server.server_close()


def get_state(conn):
    conn.request("GET", "/state")
    resp = conn.getresponse()
    data = json.loads(resp.read())
    assert resp.status == 200
    return data


def post_json(conn, path, payload):
    conn.request(
        "POST",
        path,
        body=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    data = json.loads(resp.read())
    assert resp.status == 200
    return data


def test_state_uses_cached_analysis_when_fen_unchanged(http_server):
    host, port, _state, engine = http_server
    conn = HTTPConnection(host, port)

    get_state(conn)
    get_state(conn)
    get_state(conn)

    assert engine.calls == 1


def test_cache_invalidates_after_play_move(http_server):
    host, port, _state, engine = http_server
    conn = HTTPConnection(host, port)

    get_state(conn)
    assert engine.calls == 1

    post_json(conn, "/play_move", {"move": "e2e4"})
    get_state(conn)

    assert engine.calls == 2


def test_cache_invalidates_after_undo(http_server):
    host, port, _state, engine = http_server
    conn = HTTPConnection(host, port)

    get_state(conn)
    post_json(conn, "/play_move", {"move": "e2e4"})
    get_state(conn)
    assert engine.calls == 2

    conn.request("POST", "/undo")
    conn.getresponse().read()

    get_state(conn)
    assert engine.calls == 3
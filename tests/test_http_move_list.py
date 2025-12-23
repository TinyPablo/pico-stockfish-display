import json
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from server.chess_state import SandboxState
from server.analysis import StubAnalysisEngine
from server.http_server import make_http_server


def get_json(url):
    with urlopen(url, timeout=2) as r:
        return json.loads(r.read().decode())


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=2) as r:
        return json.loads(r.read().decode())


def start_test_server():
    state = SandboxState()
    engine = StubAnalysisEngine()

    httpd = make_http_server("127.0.0.1", 0, state, engine)
    port = httpd.server_address[1]

    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    base_url = f"http://127.0.0.1:{port}"
    return httpd, base_url


def test_move_list_initial_e2():
    httpd, base = start_test_server()
    try:
        data = post_json(base + "/move_list", {"from": "e2"})
        assert data["type"] == "move_list"
        assert data["from"] == "e2"
        assert data["moves"] == ["e3", "e4"]
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_move_list_missing_from_returns_400():
    httpd, base = start_test_server()
    try:
        try:
            post_json(base + "/move_list", {"nope": "e2"})
            assert False, "Expected HTTP 400"
        except HTTPError as e:
            assert e.code == 400
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_move_list_invalid_square_returns_400():
    httpd, base = start_test_server()
    try:
        try:
            post_json(base + "/move_list", {"from": "z9"})
            assert False, "Expected HTTP 400"
        except HTTPError as e:
            assert e.code == 400
    finally:
        httpd.shutdown()
        httpd.server_close()
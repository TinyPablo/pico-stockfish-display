import json
import threading
from urllib.request import urlopen

from server.chess_state import SandboxState
from server.analysis import StubAnalysisEngine
from server.http_server import make_http_server


def get_json(url):
    with urlopen(url, timeout=2) as r:
        return json.loads(r.read().decode())


def test_piece_list_initial_position():
    state = SandboxState()
    engine = StubAnalysisEngine()

    httpd = make_http_server("127.0.0.1", 0, state, engine)
    port = httpd.server_address[1]

    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    try:
        data = get_json(f"http://127.0.0.1:{port}/piece_list")

        assert data["type"] == "piece_list"
        assert data["pieces"] == [
            "a2", "b1", "b2", "c2", "d2",
            "e2", "f2", "g1", "g2", "h2",
        ]
    finally:
        httpd.shutdown()
        httpd.server_close()
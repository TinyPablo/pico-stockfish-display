import json
import atexit
import chess
from http.server import BaseHTTPRequestHandler, HTTPServer

from server.chess_state import SandboxState
from server.analysis import StockfishAnalysisEngine


HOST = "0.0.0.0"
PORT = 8000
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"


def make_handler(state, engine):
    last_fen = None
    last_analysis = None

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal last_fen, last_analysis

            if self.path == "/state":
                fen = state.board.fen()

                if last_analysis is None or fen != last_fen:
                    analysis = engine.analyse(state.board)
                    last_analysis = analysis
                    last_fen = fen
                else:
                    analysis = last_analysis

                response = {
                    "type": "state",
                    "turn": "white" if state.board.turn else "black",
                    "move_number": state.board.fullmove_number,
                    "last_move": (
                        state.board.peek().uci()
                        if state.board.move_stack
                        else None
                    ),
                    "analysis": {
                        "depth": analysis.depth,
                        "lines": [
                            {"move": l.move, "eval": l.eval}
                            for l in analysis.lines
                        ],
                    },
                }

                self._send_json(200, response)
                return

            if self.path == "/piece_list":
                seen = set()
                pieces = []

                for move in state.board.legal_moves:
                    sq = chess.square_name(move.from_square)
                    if sq not in seen:
                        seen.add(sq)
                        pieces.append(sq)

                pieces.sort()

                response = {
                    "type": "piece_list",
                    "pieces": pieces,
                }

                self._send_json(200, response)
                return

            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            nonlocal last_fen, last_analysis

            if self.path == "/play_move":
                body = self.read_json()
                if not body or "move" not in body:
                    self.send_response(400)
                    self.end_headers()
                    return

                try:
                    state.board.push_uci(body["move"])
                    last_fen = None
                    last_analysis = None
                    self._send_json(200, {"type": "move_result", "ok": True})
                except Exception:
                    self._send_json(
                        200,
                        {
                            "type": "move_result",
                            "ok": False,
                            "reason": "illegal_move",
                        },
                    )
                return

            if self.path == "/undo":
                ok = state.undo()
                last_fen = None
                last_analysis = None
                self._send_json(200, {"type": "move_result", "ok": ok})
                return

            if self.path == "/move_list":
                body = self.read_json()
                if not body or "from" not in body:
                    self.send_response(400)
                    self.end_headers()
                    return

                try:
                    from_sq = chess.parse_square(body["from"])
                except Exception:
                    self.send_response(400)
                    self.end_headers()
                    return

                moves = sorted(
                    {
                        chess.square_name(m.to_square)
                        for m in state.board.legal_moves
                        if m.from_square == from_sq
                    }
                )

                response = {
                    "type": "move_list",
                    "from": body["from"],
                    "moves": moves,
                }

                self._send_json(200, response)
                return

            self.send_response(404)
            self.end_headers()

        def read_json(self):
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return None
            return json.loads(self.rfile.read(length))

        def _send_json(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    return Handler


def make_http_server(host, port, state, engine):
    return HTTPServer((host, port), make_handler(state, engine))


state = SandboxState()
engine = StockfishAnalysisEngine(
    engine_path=STOCKFISH_PATH,
    time_limit=0.2,
)


@atexit.register
def shutdown():
    engine.stop()


def main():
    print(f"Server running on {HOST}:{PORT}")
    httpd = make_http_server(HOST, PORT, state, engine)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
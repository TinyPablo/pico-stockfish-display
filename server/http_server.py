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
            global last_fen, last_analysis

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
                    "last_move": (state.board.peek().uci() if state.board.move_stack else None),
                    "analysis": {
                        "depth": analysis.depth,
                        "lines": [{"move": l.move, "eval": l.eval} for l in analysis.lines],
                    },
                }
                return self._send_json(200, response)

            if self.path == "/piece_list":
                seen = set()
                pieces = []

                for mv in state.board.legal_moves:
                    from_sq = chess.square_name(mv.from_square)
                    if from_sq in seen:
                        continue
                    seen.add(from_sq)

                    piece = state.board.piece_at(mv.from_square)
                    if piece is None:
                        continue

                    pieces.append(
                        {
                            "square": from_sq,
                            "piece": chess.piece_name(piece.piece_type),  # pawn/knight/...
                        }
                    )

                pieces.sort(key=lambda x: x["square"])
                return self._send_json(200, {"type": "piece_list", "pieces": pieces})

            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            global last_fen, last_analysis

            if self.path == "/play_move":
                body = self.read_json()
                if not body or "move" not in body:
                    return self._send_json(400, {"type": "error", "reason": "missing_move"})

                move = body["move"]
                try:
                    state.board.push_uci(move)
                    last_fen = None
                    last_analysis = None
                    return self._send_json(200, {"type": "move_result", "ok": True})
                except Exception:
                    return self._send_json(
                        200,
                        {"type": "move_result", "ok": False, "reason": "illegal_move"},
                    )

            if self.path == "/undo":
                ok = state.undo()
                last_fen = None
                last_analysis = None
                return self._send_json(200, {"type": "move_result", "ok": ok})

            if self.path == "/move_list":
                body = self.read_json()
                if not body or "from" not in body:
                    return self._send_json(400, {"type": "error", "reason": "missing_from"})

                from_str = body["from"]
                try:
                    from_sq = chess.parse_square(from_str)
                except Exception:
                    return self._send_json(400, {"type": "error", "reason": "invalid_square"})

                moves = sorted(
                    {
                        chess.square_name(mv.to_square)
                        for mv in state.board.legal_moves
                        if mv.from_square == from_sq
                    }
                )
                return self._send_json(200, {"type": "move_list", "from": from_str, "moves": moves})

            self.send_response(404)
            self.end_headers()

        def log_message(self, *_):
            pass

        def read_json(self):
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return None
            raw = self.rfile.read(length)
            try:
                return json.loads(raw)
            except Exception:
                return None

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
import json
import atexit
from http.server import BaseHTTPRequestHandler, HTTPServer

from server.chess_state import SandboxState
from server.analysis import StockfishAnalysisEngine


HOST = "0.0.0.0"
PORT = 8000
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"


state = SandboxState()
engine = StockfishAnalysisEngine(
    engine_path=STOCKFISH_PATH,
    time_limit=0.2,
)

last_fen = None
last_analysis = None


@atexit.register
def shutdown():
    engine.stop()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global last_fen, last_analysis

        if self.path != "/state":
            self.send_response(404)
            self.end_headers()
            return

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

        body = json.dumps(response).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass  # silence default logging


def main():
    print(f"Server running on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
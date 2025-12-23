import chess
import chess.engine
from dataclasses import dataclass
import threading
import time


@dataclass
class AnalysisLine:
    move: str
    eval: float


@dataclass
class AnalysisResult:
    depth: int
    lines: list[AnalysisLine]


class StubAnalysisEngine:
    def analyse(self, board) -> AnalysisResult:
        return AnalysisResult(
            depth=1,
            lines=[
                AnalysisLine(move="e2e4", eval=0.20),
                AnalysisLine(move="d2d4", eval=0.15),
                AnalysisLine(move="g1f3", eval=0.10),
            ],
        )


class StockfishAnalysisEngine:
    """
    Live deepening Stockfish analysis.
    - Keeps analysing current FEN in a background thread.
    - Each cycle increases time budget up to max_time.
    - analyse(board) returns latest stored result quickly.
    """

    live = True  # used by http_server to decide caching behavior

    def __init__(
        self,
        engine_path: str,
        base_time: float = 0.10,
        step_time: float = 0.10,
        max_time: float = 1.50,
        interval: float = 1.0,
        multipv: int = 3,
    ):
        self.engine_path = engine_path
        self.base_time = base_time
        self.step_time = step_time
        self.max_time = max_time
        self.interval = interval
        self.multipv = multipv

        self.engine = None

        self._lock = threading.Lock()
        self._target_fen = None
        self._latest = None
        self._budget = self.base_time

        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self.engine is None:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)

    def stop(self):
        self._stop.set()
        t = self._thread
        if t is not None:
            t.join(timeout=2.0)
            self._thread = None

        if self.engine is not None:
            self.engine.quit()
            self.engine = None

    def _ensure_worker(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _set_position(self, board: chess.Board):
        fen = board.fen()
        with self._lock:
            if fen != self._target_fen:
                self._target_fen = fen
                self._latest = None
                self._budget = self.base_time

    def _info_to_result(self, info) -> AnalysisResult:
        # python-chess returns list when multipv>1
        entries = info if isinstance(info, list) else [info]
        lines: list[AnalysisLine] = []

        for entry in entries:
            pv = entry.get("pv")
            if not pv:
                continue
            score = entry["score"].white().score(mate_score=10000)
            if score is None:
                continue
            lines.append(AnalysisLine(move=pv[0].uci(), eval=score / 100.0))

        depth = 0
        if entries and isinstance(entries[0], dict):
            depth = entries[0].get("depth", 0) or 0

        return AnalysisResult(depth=depth, lines=lines)

    def _worker(self):
        self.start()

        while not self._stop.is_set():
            with self._lock:
                fen = self._target_fen
                budget = self._budget

            if not fen:
                time.sleep(0.05)
                continue

            board = chess.Board(fen)

            try:
                info = self.engine.analyse(
                    board,
                    chess.engine.Limit(time=budget),
                    multipv=self.multipv,
                )
                result = self._info_to_result(info)

                with self._lock:
                    # only publish if position didn’t change mid-think
                    if fen == self._target_fen:
                        self._latest = result
                        self._budget = min(self._budget + self.step_time, self.max_time)

            except Exception:
                # keep server alive even if engine hiccups
                time.sleep(0.2)

            time.sleep(self.interval)

    def analyse(self, board: chess.Board) -> AnalysisResult:
        self.start()
        self._ensure_worker()
        self._set_position(board)

        with self._lock:
            latest = self._latest

        # First call after position change might not have a background result yet.
        # Return a quick one-shot so UI has something immediately.
        if latest is None:
            info = self.engine.analyse(
                board,
                chess.engine.Limit(time=self.base_time),
                multipv=self.multipv,
            )
            latest = self._info_to_result(info)
            with self._lock:
                if board.fen() == self._target_fen:
                    self._latest = latest

        return latest
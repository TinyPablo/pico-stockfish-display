import chess
import chess.engine
from dataclasses import dataclass


@dataclass
class AnalysisLine:
    move: str
    eval: float


@dataclass
class AnalysisResult:
    depth: int
    lines: list[AnalysisLine]


class StubAnalysisEngine:
    """
    Deterministic analysis engine for tests and sandbox fallback.
    """

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
    Stockfish-backed analysis engine.
    One-shot analysis per call (time-limited).
    """

    def __init__(self, engine_path: str, time_limit: float = 0.2):
        self.engine_path = engine_path
        self.time_limit = time_limit
        self.engine = None

    def start(self):
        if self.engine is None:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)

    def stop(self):
        if self.engine is not None:
            self.engine.quit()
            self.engine = None

    def analyse(self, board: chess.Board) -> AnalysisResult:
        self.start()

        info = self.engine.analyse(
            board,
            chess.engine.Limit(time=self.time_limit),
            multipv=3,
        )

        lines = []

        for entry in info:
            score = entry["score"].white().score(mate_score=10000)
            pv = entry.get("pv")

            if pv and score is not None:
                lines.append(
                    AnalysisLine(
                        move=pv[0].uci(),
                        eval=score / 100.0,
                    )
                )

        depth = info[0].get("depth", 0)

        return AnalysisResult(depth=depth, lines=lines)
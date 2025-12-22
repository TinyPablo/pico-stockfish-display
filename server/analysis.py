from dataclasses import dataclass


@dataclass
class AnalysisLine:
    move: str
    eval: float


@dataclass
class AnalysisResult:
    depth: int
    lines: list[AnalysisLine]


class AnalysisEngine:
    """
    Stub analysis engine for sandbox mode.
    """

    def analyse(self, board) -> AnalysisResult:
        # deterministic fake output
        return AnalysisResult(
            depth=1,
            lines=[
                AnalysisLine(move="e2e4", eval=0.20),
                AnalysisLine(move="d2d4", eval=0.15),
                AnalysisLine(move="g1f3", eval=0.10),
            ],
        )
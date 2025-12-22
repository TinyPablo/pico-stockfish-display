import chess
from server.chess_state import SandboxState


def test_initial_state():
    state = SandboxState()

    assert state.mode == state.ROOT
    assert isinstance(state.board, chess.Board)
    assert len(state.pieces) > 0
    assert state.selected_from is None


def test_select_piece_populates_moves():
    state = SandboxState()

    state.mode = state.PIECE_LIST
    state.cursor = 0
    state.select()

    assert state.mode == state.MOVE_LIST
    assert state.selected_from is not None
    assert len(state.moves) > 0


def test_make_move_changes_board():
    state = SandboxState()

    # enter piece list
    state.mode = state.PIECE_LIST
    state.cursor = 0
    from_sq = state.pieces[0].split()[0]

    # select piece
    state.select()
    assert state.selected_from == from_sq

    # select first move
    to_sq = state.moves[0]
    fen_before = state.board.fen()

    state.select()

    assert state.board.fen() != fen_before
    assert state.mode == state.ROOT
    assert state.selected_from is None


def test_back_from_move_list():
    state = SandboxState()

    state.mode = state.PIECE_LIST
    state.cursor = 0
    state.select()

    assert state.mode == state.MOVE_LIST

    state.back()

    assert state.mode == state.PIECE_LIST
    assert state.selected_from is None
    
def test_undo_on_empty_is_safe():
    state = SandboxState()
    assert state.undo() is False


def test_undo_reverts_last_move():
    state = SandboxState()

    # make one legal move using the state API
    state.mode = state.PIECE_LIST
    state.cursor = 0
    state.select()          # -> MOVE_LIST
    state.cursor = 0
    fen_before = state.board.fen()
    state.select()          # plays move, back to ROOT

    assert state.board.move_stack  # one move exists

    assert state.undo() is True
    assert state.board.move_stack == []
    assert state.mode == state.ROOT
    assert state.selected_from is None
    
from server.analysis import AnalysisEngine


def test_analysis_stub_returns_lines():
    engine = AnalysisEngine()
    state = SandboxState()

    result = engine.analyse(state.board)

    assert result.depth >= 1
    assert len(result.lines) == 3
    assert all(hasattr(l, "move") for l in result.lines)
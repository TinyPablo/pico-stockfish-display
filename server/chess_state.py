import chess


class SandboxState:
    """
    Sandbox UI state backed by python-chess.
    """

    ROOT = "root"
    PIECE_LIST = "piece_list"
    MOVE_LIST = "move_list"

    def __init__(self):
        self.mode = self.ROOT
        self.cursor = 0 
        self.last_key = None

        self.board = chess.Board()
        self.pieces = []
        self.moves = []
        
        self.selected_from = None
        
        self.update_pieces()

    def move_cursor_up(self):
        self.cursor = max(0, self.cursor - 1)

    def move_cursor_down(self, max_items: int):
        self.cursor = min(max_items - 1, self.cursor + 1)

    def select(self):
        if self.mode == self.ROOT:
            self.mode = self.PIECE_LIST
            self.cursor = 0

        elif self.mode == self.PIECE_LIST:
            self.selected_from = self.pieces[self.cursor].split()[0]
            self.update_moves(self.selected_from)
            self.mode = self.MOVE_LIST
            self.cursor = 0

        elif self.mode == self.MOVE_LIST:
            to_sq = self.moves[self.cursor]
            self.board.push_uci(self.selected_from + to_sq)
            self.selected_from = None
            self.update_pieces()
            self.mode = self.ROOT
            self.cursor = 0

    def back(self):
        if self.mode == self.MOVE_LIST:
            self.mode = self.PIECE_LIST
            self.cursor = 0
            self.selected_from = None
        elif self.mode == self.PIECE_LIST:
            self.mode = self.ROOT
            self.cursor = 0
            
    def update_pieces(self):
        seen = set()
        self.pieces = []

        for move in self.board.legal_moves:
            sq = chess.square_name(move.from_square)
            if sq not in seen:
                seen.add(sq)
                piece = self.board.piece_at(move.from_square)
                self.pieces.append(f"{sq} {piece.symbol().lower()}")

        self.pieces.sort()
        
    def update_moves(self, from_square: str):
        sq = chess.parse_square(from_square)
        self.moves = sorted({
            chess.square_name(m.to_square)
            for m in self.board.legal_moves
            if m.from_square == sq
        })

    def undo(self) -> bool:
        """
        Undo the last move. Returns True if a move was undone.
        """
        if not self.board.move_stack:
            return False

        self.board.pop()
        self.selected_from = None
        self.mode = self.ROOT
        self.cursor = 0
        self.update_pieces()
        self.moves = []
        return True
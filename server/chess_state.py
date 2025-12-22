class SandboxState:
    """
    Sandbox UI state (no chess logic yet).
    """

    ROOT = "root"
    PIECE_LIST = "piece_list"
    MOVE_LIST = "move_list"

    def __init__(self):
        self.mode = self.ROOT
        self.cursor = 0 
        self.last_key = None

        # fake data
        self.pieces = ["e2 pawn", "g1 knight", "f1 bishop"]
        self.moves = ["e3", "e4"]

    def move_cursor_up(self):
        self.cursor = max(0, self.cursor - 1)

    def move_cursor_down(self, max_items: int):
        self.cursor = min(max_items - 1, self.cursor + 1)

    def select(self):
        if self.mode == self.ROOT:
            self.mode = self.PIECE_LIST
            self.cursor = 0
        elif self.mode == self.PIECE_LIST:
            self.mode = self.MOVE_LIST
            self.cursor = 0
        elif self.mode == self.MOVE_LIST:
            self.mode = self.ROOT
            self.cursor = 0

    def back(self):
        if self.mode == self.MOVE_LIST:
            self.mode = self.PIECE_LIST
            self.cursor = 0
        elif self.mode == self.PIECE_LIST:
            self.mode = self.ROOT
            self.cursor = 0
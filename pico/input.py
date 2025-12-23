from machine import Pin
import time


# Public events
UP = "UP"
DOWN = "DOWN"
SELECT = "SELECT"
BACK = "BACK"
UNDO = "UNDO"


class Input:
    """
    4x4 matrix keypad scanner.
    - Columns: outputs (default HIGH), one column driven LOW during scan.
    - Rows: inputs with PULL_UP (pressed reads LOW).
    - Emits event only on a *new press* (edge), with debounce.

    Assumes at most 1 key pressed at a time (your constraint).
    """

    def __init__(self, debounce_ms=60):
        # Columns in col1..col4 order (important for s-number mapping)
        # Given: p1 gpio8 col4, p2 gpio9 col3, p3 gpio10 col2, p4 gpio11 col1
        self.cols = [
            Pin(11, Pin.OUT, value=1),  # col1
            Pin(10, Pin.OUT, value=1),  # col2
            Pin(9,  Pin.OUT, value=1),  # col3
            Pin(8,  Pin.OUT, value=1),  # col4
        ]

        # Rows in row1..row4 order
        self.rows = [
            Pin(12, Pin.IN, Pin.PULL_UP),  # row1
            Pin(13, Pin.IN, Pin.PULL_UP),  # row2
            Pin(14, Pin.IN, Pin.PULL_UP),  # row3
            Pin(15, Pin.IN, Pin.PULL_UP),  # row4
        ]

        # Map switch number -> event
        self.keymap = {
            9: UP,
            13: DOWN,
            14: SELECT,
            15: BACK,
            16: UNDO,
        }

        self.debounce_ms = debounce_ms

        # Debounce state
        self._candidate = None
        self._candidate_t = time.ticks_ms()
        self._stable = None  # stable key number or None

    def _all_cols_high(self):
        for c in self.cols:
            c.value(1)

    def _scan_raw_key(self):
        """
        Returns key number 1..16 if pressed, else None.
        Ignores multi-press (returns None) if more than one row reads LOW.
        """
        self._all_cols_high()

        for col_idx, col_pin in enumerate(self.cols, start=1):  # col 1..4
            col_pin.value(0)
            time.sleep_us(50)  # settle

            pressed_rows = []
            for row_idx, row_pin in enumerate(self.rows, start=1):  # row 1..4
                if row_pin.value() == 0:
                    pressed_rows.append(row_idx)

            col_pin.value(1)

            if len(pressed_rows) == 1:
                row = pressed_rows[0]
                s = (row - 1) * 4 + col_idx  # s1..s16
                return s

            if len(pressed_rows) > 1:
                # multi-press / ghosting -> ignore (your "one at a time" rule)
                return None

        return None

    def read(self):
        """
        Returns one of: UP/DOWN/SELECT/BACK/UNDO on new press, else None.
        """
        raw = self._scan_raw_key()

        now = time.ticks_ms()

        # debounce: track candidate changes
        if raw != self._candidate:
            self._candidate = raw
            self._candidate_t = now
            return None

        if time.ticks_diff(now, self._candidate_t) < self.debounce_ms:
            return None

        # candidate is stable; edge-detect press
        if self._stable != self._candidate:
            prev = self._stable
            self._stable = self._candidate

            # emit only on press edge (None -> key)
            if prev is None and self._stable is not None:
                return self.keymap.get(self._stable)

        return None
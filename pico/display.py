from machine import I2C, Pin
from lib.ssd1306 import SSD1306_I2C


class Display:
    def __init__(self):
        # I2C0 -> INPUT / STATE OLED
        self.i2c0 = I2C(0, sda=Pin(0), scl=Pin(1), freq=400_000)

        # I2C1 -> ANALYSIS OLED
        self.i2c1 = I2C(1, sda=Pin(6), scl=Pin(7), freq=400_000)

        self.state_oled = SSD1306_I2C(128, 64, self.i2c0)
        self.analysis_oled = SSD1306_I2C(128, 64, self.i2c1)

        self.clear_all()

    def clear_all(self):
        self.state_oled.fill(0)
        self.state_oled.show()
        self.analysis_oled.fill(0)
        self.analysis_oled.show()

    # ---------- ROOT STATE ----------
    def show_state(self, turn, move_number, last_move):
        oled = self.state_oled
        oled.fill(0)

        oled.text("Turn: %s" % (turn,), 0, 0)
        oled.text("Move: %s" % (move_number,), 0, 12)
        oled.text("Last: %s" % (last_move or "--",), 0, 24)

        oled.text("SEL=pieces", 0, 54)
        oled.show()

    # ---------- MENUS ----------
    def _menu_window(self, cursor: int, n: int, max_visible: int) -> int:
        if n <= max_visible:
            return 0
        offset = cursor - (max_visible // 2)
        if offset < 0:
            offset = 0
        max_off = n - max_visible
        if offset > max_off:
            offset = max_off
        return offset

    def _show_menu(self, title: str, lines: list, cursor: int, footer: str = ""):
        oled = self.state_oled
        oled.fill(0)

        # No title line (remove "PIECES"/"MOVES")
        max_visible = 4
        n = len(lines)
        off = self._menu_window(cursor, n, max_visible)

        y = 0
        for i in range(off, min(off + max_visible, n)):
            prefix = ">" if i == cursor else " "
            oled.text((prefix + str(lines[i]))[:16], 0, y)
            y += 12

        if footer:
            oled.text(str(footer)[:16], 0, 54)

        oled.show()

    def _piece_to_label(self, p) -> str:
        # p can be dict {"square": "...", "piece": "..."} OR string "e2 pawn"
        if isinstance(p, dict):
            sq = p.get("square", "??")
            name = p.get("piece", "?")
            return "%s %s" % (sq, name)
        s = str(p)
        parts = s.split()
        if len(parts) >= 2:
            return "%s %s" % (parts[0], parts[1])
        if len(parts) == 1:
            return parts[0]
        return "?? ?"

    def show_piece_list(self, pieces, cursor: int):
        lines = [self._piece_to_label(p) for p in (pieces or [])]
        self._show_menu("", lines, cursor, "UD SEL BK")

    def show_move_list(self, from_sq: str, moves: list, cursor: int):
        lines = ["%s->%s" % (from_sq, m) for m in (moves or [])]
        self._show_menu("", lines, cursor, "UD SEL BK")

    # ---------- ANALYSIS OLED ----------
    def show_analysis(self, depth, lines):
        oled = self.analysis_oled
        oled.fill(0)

        # header: depth + eval indicator
        if lines:
            e = lines[0].get("eval", 0.0)
            side = "W" if e >= 0 else "B"
            ev = abs(e)
            oled.text("D:%d %s%.2f" % (depth, side, ev), 0, 0)
        else:
            oled.text("D:%d --" % (depth,), 0, 0)

        y = 16
        for i, line in enumerate(lines[:3], 1):
            move = line["move"]
            eval_ = line["eval"]
            sign = "+" if eval_ >= 0 else ""
            oled.text("%d %s %s%.2f" % (i, move, sign, eval_), 0, y)
            y += 12

        oled.show()
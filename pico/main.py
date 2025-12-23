import time

from wifi import connect
from display import Display
from protocol import ServerClient
from input import (
    Input,
    UP, DOWN, SELECT, BACK, UNDO,
    BEST1, BEST2, BEST3,
    RESET, TOGGLE_MODE,
)

SERVER_IP = "192.168.1.114"  # CHANGE THIS

MODE_ROOT = 0
MODE_PIECES = 1
MODE_MOVES = 2


def piece_square(item):
    if isinstance(item, dict):
        return item.get("square")
    if isinstance(item, str):
        parts = item.split()
        return parts[0] if parts else None
    return None


def main():
    connect()

    display = Display()
    client = ServerClient(SERVER_IP)
    inp = Input(debounce_ms=40)

    mode = MODE_ROOT
    cursor = 0

    pieces = []
    moves = []
    selected_from = None

    last_state_poll = time.ticks_ms()
    poll_ms = 500

    analysis_lines = []  # latest /state analysis.lines for BEST1/2/3

    fast_mode = False  # False=Slow(S), True=Fast(F)
    need_enter_pieces = False  # used to auto-enter pieces after commands

    def mode_char():
        return "F" if fast_mode else "S"

    def refresh_state(update_state_oled: bool):
        nonlocal analysis_lines

        st = client.get_state(fresh=False)
        if not st or st.get("type") != "state":
            return

        if update_state_oled:
            display.show_state(
                turn=st.get("turn", "?"),
                move_number=st.get("move_number", 0),
                last_move=st.get("last_move"),
                mode_char=mode_char(),
            )

        analysis = st.get("analysis")
        if isinstance(analysis, dict):
            analysis_lines = analysis.get("lines", []) or []
            display.show_analysis(
                depth=analysis.get("depth", 0),
                lines=analysis_lines,
            )

    def enter_pieces():
        nonlocal mode, cursor, pieces, moves, selected_from
        r = client.piece_list()
        if r and r.get("type") == "piece_list":
            pieces = r.get("pieces", [])
            moves = []
            selected_from = None
            cursor = 0
            mode = MODE_PIECES
            display.show_piece_list(pieces, cursor, mode_char=mode_char())

    # initial draw
    refresh_state(update_state_oled=True)

    while True:
        now = time.ticks_ms()

        # polling: keep analysis fresh always; state OLED only in ROOT+slow
        if time.ticks_diff(now, last_state_poll) >= poll_ms:
            refresh_state(update_state_oled=(mode == MODE_ROOT and not fast_mode))
            last_state_poll = now

        # fast-mode: after any command returning to ROOT, auto-enter pieces once
        if mode == MODE_ROOT and fast_mode and need_enter_pieces:
            need_enter_pieces = False
            enter_pieces()
            time.sleep_ms(10)
            continue

        key = inp.read()
        if not key:
            time.sleep_ms(10)
            continue

        # ----- global keys -----

        if key == TOGGLE_MODE:
            fast_mode = not fast_mode

            mode = MODE_ROOT
            cursor = 0
            pieces = []
            moves = []
            selected_from = None

            if fast_mode:
                need_enter_pieces = True
                # keep analysis updated; don’t redraw state
                refresh_state(update_state_oled=False)
            else:
                need_enter_pieces = False
                refresh_state(update_state_oled=True)
            continue

        if key == UNDO:
            client.undo()
            mode = MODE_ROOT
            cursor = 0
            pieces = []
            moves = []
            selected_from = None

            need_enter_pieces = fast_mode
            refresh_state(update_state_oled=not fast_mode)
            continue

        if key == RESET:
            client.reset()
            mode = MODE_ROOT
            cursor = 0
            pieces = []
            moves = []
            selected_from = None

            need_enter_pieces = fast_mode
            refresh_state(update_state_oled=not fast_mode)
            continue

        if key in (BEST1, BEST2, BEST3):
            idx = 0 if key == BEST1 else (1 if key == BEST2 else 2)
            if idx < len(analysis_lines):
                mv = analysis_lines[idx].get("move")
                if mv:
                    client.play_move(mv)

                    mode = MODE_ROOT
                    cursor = 0
                    pieces = []
                    moves = []
                    selected_from = None

                    need_enter_pieces = fast_mode
                    refresh_state(update_state_oled=not fast_mode)
            continue

        # ----- UI state machine -----

        if mode == MODE_ROOT:
            if fast_mode:
                # in fast mode we normally auto-enter; allow SELECT as manual fallback
                if key == SELECT:
                    enter_pieces()
            else:
                if key == SELECT:
                    enter_pieces()
                else:
                    # keep slow root visible on any other key
                    refresh_state(update_state_oled=True)
            continue

        if mode == MODE_PIECES:
            if key == UP:
                cursor = max(0, cursor - 1)
                display.show_piece_list(pieces, cursor, mode_char=mode_char())

            elif key == DOWN:
                cursor = min(max(0, len(pieces) - 1), cursor + 1)
                display.show_piece_list(pieces, cursor, mode_char=mode_char())

            elif key == BACK:
                mode = MODE_ROOT
                cursor = 0
                pieces = []
                moves = []
                selected_from = None

                need_enter_pieces = fast_mode
                refresh_state(update_state_oled=not fast_mode)

            elif key == SELECT:
                if not pieces:
                    continue

                selected_from = piece_square(pieces[cursor])
                if not selected_from:
                    continue

                r = client.move_list(selected_from)
                if r and r.get("type") == "move_list":
                    moves = r.get("moves", [])
                    cursor = 0
                    mode = MODE_MOVES
                    display.show_move_list(selected_from, moves, cursor, mode_char=mode_char())

            continue

        if mode == MODE_MOVES:
            if key == UP:
                cursor = max(0, cursor - 1)
                display.show_move_list(selected_from, moves, cursor, mode_char=mode_char())

            elif key == DOWN:
                cursor = min(max(0, len(moves) - 1), cursor + 1)
                display.show_move_list(selected_from, moves, cursor, mode_char=mode_char())

            elif key == BACK:
                mode = MODE_PIECES
                cursor = 0
                moves = []
                selected_from = None
                display.show_piece_list(pieces, cursor, mode_char=mode_char())

            elif key == SELECT:
                if not moves or not selected_from:
                    continue

                to_sq = moves[cursor]
                client.play_move(selected_from + to_sq)

                mode = MODE_ROOT
                cursor = 0
                pieces = []
                moves = []
                selected_from = None

                need_enter_pieces = fast_mode
                refresh_state(update_state_oled=not fast_mode)

            continue


main()
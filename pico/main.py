import time

from wifi import connect
from display import Display
from protocol import ServerClient
from input import Input, UP, DOWN, SELECT, BACK, UNDO


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

    def refresh_state(update_state_oled: bool):
        st = client.get_state()
        if not st or st.get("type") != "state":
            return

        if update_state_oled:
            display.show_state(
                turn=st.get("turn", "?"),
                move_number=st.get("move_number", 0),
                last_move=st.get("last_move"),
            )

        analysis = st.get("analysis")
        if isinstance(analysis, dict):
            display.show_analysis(
                depth=analysis.get("depth", 0),
                lines=analysis.get("lines", []),
            )

    refresh_state(update_state_oled=True)

    while True:
        now = time.ticks_ms()

        # keep analysis fresh always; state OLED only in ROOT
        if time.ticks_diff(now, last_state_poll) >= poll_ms:
            refresh_state(update_state_oled=(mode == MODE_ROOT))
            last_state_poll = now

        key = inp.read()
        if not key:
            time.sleep_ms(10)
            continue

        # UNDO is global
        if key == UNDO:
            client.undo()
            mode = MODE_ROOT
            cursor = 0
            pieces = []
            moves = []
            selected_from = None
            refresh_state(update_state_oled=True)
            continue

        if mode == MODE_ROOT:
            if key == SELECT:
                r = client.piece_list()
                if r and r.get("type") == "piece_list":
                    pieces = r.get("pieces", [])
                    cursor = 0
                    mode = MODE_PIECES
                    display.show_piece_list(pieces, cursor)
            continue

        if mode == MODE_PIECES:
            if key == UP:
                cursor = max(0, cursor - 1)
                display.show_piece_list(pieces, cursor)

            elif key == DOWN:
                cursor = min(max(0, len(pieces) - 1), cursor + 1)
                display.show_piece_list(pieces, cursor)

            elif key == BACK:
                mode = MODE_ROOT
                cursor = 0
                pieces = []
                moves = []
                selected_from = None
                refresh_state(update_state_oled=True)

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
                    display.show_move_list(selected_from, moves, cursor)

            continue

        if mode == MODE_MOVES:
            if key == UP:
                cursor = max(0, cursor - 1)
                display.show_move_list(selected_from, moves, cursor)

            elif key == DOWN:
                cursor = min(max(0, len(moves) - 1), cursor + 1)
                display.show_move_list(selected_from, moves, cursor)

            elif key == BACK:
                mode = MODE_PIECES
                cursor = 0
                moves = []
                selected_from = None
                display.show_piece_list(pieces, cursor)

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
                refresh_state(update_state_oled=True)

            continue


main()
from wifi import connect
from display import Display
from protocol import ServerClient
import time


SERVER_IP = "192.168.1.114"  # CHANGE THIS


def main():
    connect()

    display = Display()
    client = ServerClient(SERVER_IP)

    while True:
        state = client.get_state()

        if state and state.get("type") == "state":
            display.show_state(
                turn=state.get("turn", "?"),
                move_number=state.get("move_number", 0),
                last_move=state.get("last_move"),
            )

            analysis = state.get("analysis")
            if analysis:
                display.show_analysis(
                    depth=analysis.get("depth", 0),
                    lines=analysis.get("lines", []),
                )

        time.sleep(0.5)


main()
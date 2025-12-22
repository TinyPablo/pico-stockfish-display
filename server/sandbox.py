"""
Local sandbox for simulating Pico keypad and OLED output.

- Plain terminal UI
- Numeric key input
- No networking
- No hardware
"""

from chess_state import SandboxState
from analysis import AnalysisEngine

def draw(state, analysis):
    print("\033c", end="")

    print("=== INPUT OLED ===")

    if state.mode == state.ROOT:
        print("Sandbox root")
        print("5 = select")
    elif state.mode == state.PIECE_LIST:
        for i, p in enumerate(state.pieces):
            prefix = ">" if i == state.cursor else " "
            print(f"{prefix} {p}")
    elif state.mode == state.MOVE_LIST:
        for i, m in enumerate(state.moves):
            prefix = ">" if i == state.cursor else " "
            print(f"{prefix} {m}")

    print("\n=== ANALYSIS OLED ===")
    print(f"Depth: {analysis.depth}")
    for i, line in enumerate(analysis.lines, 1):
        sign = "+" if line.eval >= 0 else ""
        print(f"{i}. {line.move} {sign}{line.eval:.2f}")
        
    print("\nKeys: 2↑ 8↓ 5✓ 0← 9=undo q quit")


def main():
    state = SandboxState()
    engine = AnalysisEngine()

    while True:
        analysis = engine.analyse(state.board)
        draw(state, analysis)
        key = input("> ").strip()

        if key == "q":
            break
        elif key == "2":
            state.move_cursor_up()
        elif key == "8":
            max_items = (
                len(state.pieces)
                if state.mode == state.PIECE_LIST
                else len(state.moves)
            )
            state.move_cursor_down(max_items)
        elif key == "5":
            state.select()
        elif key == "0":
            state.back()
        elif key == "9":
            state.undo()


if __name__ == "__main__":
    main()
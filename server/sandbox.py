"""
Local sandbox for simulating Pico keypad and OLED output.

- Plain terminal UI
- Numeric key input
- No networking
- No hardware
"""

from chess_state import SandboxState


def draw(last_key: str | None):
    print("\033c", end="")  # clear terminal

    print("=== INPUT OLED ===")
    print("Use keys 1–16 to simulate keypad")
    print()
    if last_key is None:
        print("Last key: -")
    else:
        print(f"Last key: {last_key}")

    print("\n=== ANALYSIS OLED ===")
    print("No analysis (sandbox mode)")
    print("\n(q to quit)")


def main():
    state = SandboxState()

    while True:
        draw(state.last_key)
        key = input("> ").strip()

        if key == "q":
            break

        if key.isdigit() and 1 <= int(key) <= 16:
            state.register_key(key)
        else:
            state.register_key("invalid")


if __name__ == "__main__":
    main()
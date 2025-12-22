"""
Local sandbox for simulating Pico keypad and OLED output.

- Plain terminal UI
- Numeric key input
- No networking
- No hardware
"""
def draw(input_key: str | None):
    print("\033c", end="")  # clear terminal

    print("=== INPUT OLED ===")
    print("Use keys 1–16 to simulate keypad")
    print()
    if input_key is None:
        print("Last key: -")
    else:
        print(f"Last key: {input_key}")

    print("\n=== ANALYSIS OLED ===")
    print("No analysis (sandbox mode)")
    print("\n(q to quit)")


def main():
    last_key = None

    while True:
        draw(last_key)
        key = input("> ").strip()

        if key == "q":
            break

        if key.isdigit() and 1 <= int(key) <= 16:
            last_key = key
        else:
            last_key = "invalid"


if __name__ == "__main__":
    main()
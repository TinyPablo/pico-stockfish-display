# pico-stockfish-display

Raspberry Pi Pico W client that displays live Stockfish chess analysis
received over Wi-Fi from a Mac-based Python server.

The project consists of:

- a Python server running Stockfish and exposing a simple protocol
- a MicroPython client handling keypad input and OLED output

Development is incremental and sandbox-driven.

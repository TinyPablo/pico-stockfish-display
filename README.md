## Current status

**v0.1 – Pico read-only display**

Implemented:

- Python server with Stockfish-backed analysis
- HTTP polling endpoint (`/state`)
- Raspberry Pi Pico W client
- Dual SSD1306 OLED output (state + analysis)
- Wi-Fi connectivity and periodic refresh

Not yet implemented:

- Pico keypad input
- Pico → server command wiring

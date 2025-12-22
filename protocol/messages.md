# Message protocol

This document defines the JSON message protocol used between:

- **Server** (Mac, Python, Stockfish)
- **Client** (Raspberry Pi Pico W, MicroPython)

Transport: **HTTP (JSON over REST)**  
Encoding: UTF-8 JSON  
State authority: **Server-only**

The Pico client never maintains authoritative chess state.

---

## Communication model

The protocol is **client-driven pull with command interrupts**:

- The Pico periodically requests the current state and analysis.
- The Pico may interrupt at any time by sending a command (e.g. play move, undo).
- The server responds immediately to commands and updates its internal state.
- Subsequent client fetches reflect the new state.

The server does **not** push unsolicited messages.

---

## Common fields

All messages include:

- `type` — string identifying the message purpose

---

## Client → Server messages

All client commands are sent via **HTTP POST** unless stated otherwise.

### `get_state`

Request the current game and analysis state.

Used periodically (e.g. every 300–500 ms).

```json
{
  "type": "get_state"
}
```

---

### `request_piece_list`

Request a list of pieces that can be moved by the current player.

```json
{
  "type": "request_piece_list"
}
```

---

### `request_move_list`

Request legal destination squares for a given source square.

```json
{
  "type": "request_move_list",
  "from": "e2"
}
```

---

### `play_move`

Submit a move for validation and execution.

```json
{
  "type": "play_move",
  "move": "e2e4"
}
```

---

### `undo`

Undo the last move.

```json
{
  "type": "undo"
}
```

---

## Server → Client messages

### `state`

Returned in response to `get_state`.

```json
{
  "type": "state",
  "turn": "white",
  "move_number": 1,
  "last_move": null
}
```

---

### `piece_list`

Response to `request_piece_list`.

```json
{
  "type": "piece_list",
  "pieces": [
    { "square": "e2", "piece": "pawn" },
    { "square": "g1", "piece": "knight" }
  ]
}
```

---

### `move_list`

Response to `request_move_list`.

```json
{
  "type": "move_list",
  "from": "e2",
  "moves": ["e3", "e4"]
}
```

---

### `analysis`

Returned as part of `get_state` responses.

```json
{
  "type": "analysis",
  "depth": 18,
  "lines": [
    { "move": "e2e4", "eval": 0.32 },
    { "move": "d2d4", "eval": 0.28 },
    { "move": "g1f3", "eval": 0.21 }
  ]
}
```

---

### `move_result`

Response to `play_move`.

```json
{
  "type": "move_result",
  "ok": true
}
```

If invalid:

```json
{
  "type": "move_result",
  "ok": false,
  "reason": "illegal_move"
}
```

---

### `error`

Generic error response.

```json
{
  "type": "error",
  "reason": "invalid_request"
}
```

---

## Design rules

- The server is the single source of truth.
- The Pico never assumes state.
- After any command (`play_move`, `undo`), the client must request `get_state`.
- Unknown message types must be ignored safely.

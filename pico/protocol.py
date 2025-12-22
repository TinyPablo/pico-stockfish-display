import urequests
import time


class ServerClient:
    def __init__(self, host, port=8000, timeout=2):
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout

    def get_state(self):
        try:
            r = urequests.get(self.base_url + "/state", timeout=self.timeout)
            data = r.json()
            r.close()
            return data
        except Exception as e:
            print("Protocol error (get_state):", e)
            return None

    def play_move(self, move: str):
        try:
            r = urequests.post(
                self.base_url + "/play_move",
                json={"move": move},
                timeout=self.timeout,
            )
            data = r.json()
            r.close()
            return data
        except Exception as e:
            print("Protocol error (play_move):", e)
            return None

    def undo(self):
        try:
            r = urequests.post(
                self.base_url + "/undo",
                timeout=self.timeout,
            )
            data = r.json()
            r.close()
            return data
        except Exception as e:
            print("Protocol error (undo):", e)
            return None
import urequests
import time


class ServerClient:
    def __init__(self, host, port=8000, timeout=2):
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout

    def get_state(self):
        url = self.base_url + "/state"
        try:
            r = urequests.get(url, timeout=self.timeout)
            data = r.json()
            r.close()
            return data
        except Exception as e:
            print("Protocol error:", e)
            return None
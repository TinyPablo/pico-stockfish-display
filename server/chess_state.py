class SandboxState:
    """
    Minimal state holder for the sandbox.

    This is NOT chess logic yet.
    It only models what the UI needs to display.
    """

    def __init__(self):
        self.last_key: str | None = None

    def register_key(self, key: str):
        self.last_key = key
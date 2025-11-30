class HIDProtocolError(ValueError):
    """Exception raised for errors in the HID protocol parsing."""
    def __init__(self, message: str):
        super().__init__(f"HID Protocol Error: {message}")
from .generic_desktop import GenericDesktop
from .button import ButtonPage
from .consumer import ConsumerPage
from .keyboard import KeyboardPage
from .led import LedPage
__all__ = [
    "GenericDesktop",
    "ButtonPage",
    "ConsumerPage",
    "KeyboardPage",
    "LedPage",
    "KNOWN_USAGE_PAGES",
]

KNOWN_USAGE_PAGES = {
    GenericDesktop.PAGE_ID: ("Generic Desktop", GenericDesktop),
    ButtonPage.PAGE_ID: ("Button", ButtonPage),
    ConsumerPage.PAGE_ID: ("Consumer", ConsumerPage),
    KeyboardPage.PAGE_ID: ("Keyboard/Keypad", KeyboardPage),
    LedPage.PAGE_ID: ("LED", LedPage),
}



__doc__ = """
HID Tables module aggregates known HID usage pages and their corresponding enumerations.
It provides a mapping of usage page IDs to their names and associated enums for easy lookup.

See official HID Usage Tables for more details:
https://www.usb.org/sites/default/files/documents/hut1_3.pdf
"""
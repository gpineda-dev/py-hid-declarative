from enum import IntEnum


class GenericDesktop(IntEnum):
    """
    HID Usage Table 1: Generic Desktop Page
    Ref: USB HID Usage Tables 1.12, Section 4
    """
    _ignore_ = 'PAGE_ID'

    # Pointer / Mouse / Keyboard
    POINTER                = 0x01
    MOUSE                  = 0x02
    JOYSTICK               = 0x04
    GAMEPAD                = 0x05
    KEYBOARD               = 0x06
    KEYPAD                 = 0x07
    MULTI_AXIS_CONTROLLER  = 0x08

    # Axes
    X                      = 0x30
    Y                      = 0x31
    Z                      = 0x32
    RX                     = 0x33
    RY                     = 0x34
    RZ                     = 0x35
    SLIDER                 = 0x36
    DIAL                   = 0x37
    WHEEL                  = 0x38
    HAT_SWITCH             = 0x39

    # System Controls
    SYSTEM_CONTROL         = 0x80
    SYSTEM_POWER_DOWN      = 0x81
    SYSTEM_SLEEP           = 0x82
    SYSTEM_WAKE_UP         = 0x83
    SYSTEM_CONTEXT_MENU    = 0x84
    SYSTEM_MAIN_MENU       = 0x85
    SYSTEM_APP_MENU        = 0x86
    SYSTEM_MENU_HELP       = 0x87
    SYSTEM_MENU_EXIT       = 0x88
    SYSTEM_MENU_SELECT     = 0x89
    SYSTEM_MENU_RIGHT      = 0x8A
    SYSTEM_MENU_LEFT       = 0x8B
    SYSTEM_MENU_UP         = 0x8C
    SYSTEM_MENU_DOWN       = 0x8D

GenericDesktop.PAGE_ID = 0x01
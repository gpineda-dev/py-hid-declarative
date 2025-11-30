from enum import IntEnum

class KeyboardPage(IntEnum):
    """
    HID Usage Table 7: Keyboard/Keypad Page (0x07)
    """
    _ignore_ = 'PAGE_ID'
    PAGE_ID = 0x07
    
    # Error codes
    NO_EVENT = 0x00
    ERROR_ROLL_OVER = 0x01
    POST_FAIL = 0x02
    ERROR_UNDEFINED = 0x03
    
    # Letters
    A = 0x04
    B = 0x05
    C = 0x06
    D = 0x07
    E = 0x08
    F = 0x09
    G = 0x0A
    H = 0x0B
    I = 0x0C
    J = 0x0D
    K = 0x0E
    L = 0x0F
    M = 0x10
    N = 0x11
    O = 0x12
    P = 0x13
    Q = 0x14
    R = 0x15
    S = 0x16
    T = 0x17
    U = 0x18
    V = 0x19
    W = 0x1A
    X = 0x1B
    Y = 0x1C
    Z = 0x1D
    
    # Numbers
    KEY_1 = 0x1E
    KEY_2 = 0x1F
    KEY_3 = 0x20
    KEY_4 = 0x21
    KEY_5 = 0x22
    KEY_6 = 0x23
    KEY_7 = 0x24
    KEY_8 = 0x25
    KEY_9 = 0x26
    KEY_0 = 0x27
    
    ENTER = 0x28
    ESCAPE = 0x29
    BACKSPACE = 0x2A
    TAB = 0x2B
    SPACE = 0x2C
    
    # Modifiers (Left)
    LEFT_CONTROL = 0xE0
    LEFT_SHIFT   = 0xE1
    LEFT_ALT     = 0xE2
    LEFT_GUI     = 0xE3
    
    # Modifiers (Right)
    RIGHT_CONTROL = 0xE4
    RIGHT_SHIFT   = 0xE5
    RIGHT_ALT     = 0xE6
    RIGHT_GUI     = 0xE7

# Reinject PAGE_ID after class definition
KeyboardPage.PAGE_ID = 0x07
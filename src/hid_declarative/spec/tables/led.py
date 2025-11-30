from enum import IntEnum

class LedPage(IntEnum):
    """HID Usage Table 8: LEDs"""
    _ignore_ = 'PAGE_ID'
    PAGE_ID = 0x08
    
    NUM_LOCK = 0x01
    CAPS_LOCK = 0x02
    SCROLL_LOCK = 0x03
    COMPOSE = 0x04
    KANA = 0x05
    POWER = 0x06
    SHIFT = 0x07
    DO_NOT_DISTURB = 0x08
    MUTE = 0x09
    TONE_ENABLE = 0x0A
    HIGH_CUT_FILTER = 0x0B
    LOW_CUT_FILTER = 0x0C
    EQUALIZER_ENABLE = 0x0D
    SOUND_FIELD_ON = 0x0E
    SURROUND_ON = 0x0F
    REPEAT = 0x10
    STEREO = 0x11
    SAMPLING_RATE_DETECT = 0x12

LedPage.PAGE_ID = 0x08
from enum import IntEnum

class ConsumerPage(IntEnum):
    """
    HID Usage Table 12: Consumer Page (0x0C)
    """
    _ignore_ = 'PAGE_ID'
    PAGE_ID = 0x0C
    
    CONSUMER_CONTROL = 0x01
    # Power
    POWER = 0x30
    RESET = 0x31
    SLEEP = 0x32
    
    # Media Transport
    PLAY = 0xB0
    PAUSE = 0xB1
    RECORD = 0xB2
    FAST_FORWARD = 0xB3
    REWIND = 0xB4
    SCAN_NEXT_TRACK = 0xB5
    SCAN_PREV_TRACK = 0xB6
    STOP = 0xB7
    EJECT = 0xB8
    RANDOM_PLAY = 0xB9
    
    # Audio
    VOLUME = 0xE0
    MUTE = 0xE2
    BASS = 0xE3
    TREBLE = 0xE4
    BASS_BOOST = 0xE5
    VOLUME_INCREMENT = 0xE9
    VOLUME_DECREMENT = 0xEA
    
    # Application Launch
    AL_CALCULATOR = 0x192
    AL_LOCAL_BROWSER = 0x194
    
    # AC (Application Control)
    AC_SEARCH = 0x221
    AC_HOME = 0x223
    AC_BACK = 0x224
    AC_FORWARD = 0x225
    AC_STOP = 0x226
    AC_REFRESH = 0x227
    AC_BOOKMARKS = 0x22A

# Reinject PAGE_ID after class definition
ConsumerPage.PAGE_ID = 0x0C
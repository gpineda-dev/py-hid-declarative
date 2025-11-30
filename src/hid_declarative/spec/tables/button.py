from enum import IntEnum


class ButtonPage(IntEnum):
    """
    HID Usage Table 9: Button Page
    Ref: USB HID Usage Tables 1.12, Section 12
    """    
    _ignore_ = 'PAGE_ID'

    # Buttons 1 to 32
    BUTTON_1  = 0x01
    BUTTON_2  = 0x02
    BUTTON_3  = 0x03
    BUTTON_4  = 0x04
    BUTTON_5  = 0x05
    BUTTON_6  = 0x06
    BUTTON_7  = 0x07
    BUTTON_8  = 0x08
    BUTTON_9  = 0x09
    BUTTON_10 = 0x0A
    BUTTON_11 = 0x0B
    BUTTON_12 = 0x0C
    BUTTON_13 = 0x0D
    BUTTON_14 = 0x0E
    BUTTON_15 = 0x0F
    BUTTON_16 = 0x10
    BUTTON_17 = 0x11
    BUTTON_18 = 0x12
    BUTTON_19 = 0x13
    BUTTON_20 = 0x14
    BUTTON_21 = 0x15
    BUTTON_22 = 0x16
    BUTTON_23 = 0x17
    BUTTON_24 = 0x18
    BUTTON_25 = 0x19
    BUTTON_26 = 0x1A
    BUTTON_27 = 0x1B
    BUTTON_28 = 0x1C
    BUTTON_29 = 0x1D
    BUTTON_30 = 0x1E
    BUTTON_31 = 0x1F
    BUTTON_32 = 0x20

    NO_BUTTON = 0x00  # No Button Pressed


    @classmethod
    def make_button_usage(cls, button_number: int) -> int:
        """Return the usage ID for a given button number (1-based)."""
        if 1 <= button_number <= 32:
            return cls.BUTTON_1 + (button_number - 1)
        else:
            raise ValueError("Button number must be between 1 and 32.")
        
    @classmethod
    def get_button_number(cls, usage_id: int) -> int:
        """Return the button number (1-based) for a given usage ID."""
        if cls.BUTTON_1 <= usage_id <= cls.BUTTON_32:
            return usage_id - cls.BUTTON_1 + 1
        else:
            raise ValueError("Usage ID is not in the Button Page range.")


ButtonPage.PAGE_ID = 0x09
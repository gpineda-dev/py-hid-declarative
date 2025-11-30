from enum import IntEnum


class CollectionType(IntEnum):
    """
    HID Collection Types
    Ref: USB HID Usage Tables 1.12, Section 6.2
    """
    PHYSICAL        = 0x00
    APPLICATION     = 0x01
    LOGICAL         = 0x02
    REPORT          = 0x03
    NAMED_ARRAY     = 0x04
    USAGE_SWITCH    = 0x05
    USAGE_MODIFIER  = 0x06
    # 0x07 to 0x7F = Reserved
    # 0x80 to 0xFF = Vendor Defined

class UnitSystem(IntEnum):
    """
    HID Unit Systems
    Ref: USB HID Usage Tables 1.12, Section 6.5
    """
    NONE            = 0x00
    SI_LINEAR      = 0x01
    SI_ROTATION    = 0x02
    ENGLISH_LINEAR = 0x03
    ENGLISH_ROTATION = 0x04
    VENDOR_DEFINED  = 0x0F

class UnitExponent(IntEnum):
    """
    HID Unit Exponents
    Ref: USB HID Usage Tables 1.12, Section 6.5
    """
    EXPONENT_NEG_8 = -8
    EXPONENT_NEG_7 = -7
    EXPONENT_NEG_6 = -6
    EXPONENT_NEG_5 = -5
    EXPONENT_NEG_4 = -4
    EXPONENT_NEG_3 = -3
    EXPONENT_NEG_2 = -2
    EXPONENT_NEG_1 = -1
    EXPONENT_0     = 0
    EXPONENT_1     = 1
    EXPONENT_2     = 2
    EXPONENT_3     = 3
    EXPONENT_4     = 4
    EXPONENT_5     = 5
    EXPONENT_6     = 6
    EXPONENT_7     = 7
    EXPONENT_8     = 8


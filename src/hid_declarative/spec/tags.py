from enum import IntEnum

class ItemType(IntEnum):
    MAIN = 0
    GLOBAL = 1
    LOCAL = 2
    RESERVED = 3

class ItemTag(IntEnum):
    """
    Enumeration of HID Report Descriptor Item Tags.
    Each tag is represented by its byte value.
    """


    # --- Main Items (Type = 0) ---
    INPUT          = 0x80 # 1000 00 nn
    OUTPUT         = 0x90 # 1001 00 nn
    FEATURE        = 0xB0 # 1011 00 nn
    COLLECTION     = 0xA0 # 1010 00 nn
    END_COLLECTION = 0xC0 # 1100 00 nn

    # --- Global Items (Type = 1) ---
    USAGE_PAGE     = 0x04 # 0000 01 nn
    LOGICAL_MIN    = 0x14 # 0001 01 nn
    LOGICAL_MAX    = 0x24 # 0010 01 nn
    PHYSICAL_MIN   = 0x34 # 0011 01 nn
    PHYSICAL_MAX   = 0x44 # 0100 01 nn
    UNIT_EXPONENT  = 0x54 # 0101 01 nn
    UNIT           = 0x64 # 0110 01 nn
    REPORT_SIZE    = 0x74 # 0111 01 nn
    REPORT_ID      = 0x84 # 1000 01 nn
    REPORT_COUNT   = 0x94 # 1001 01 nn
    PUSH           = 0xA4 # 1010 01 nn
    POP            = 0xB4 # 1011 01 nn

    # --- Local Items (Type = 2) ---
    USAGE          = 0x08 # 0000 10 nn
    USAGE_MIN      = 0x18 # 0001 10 nn
    USAGE_MAX      = 0x28 # 0010 10 nn


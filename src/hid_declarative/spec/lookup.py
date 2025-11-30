from typing import Optional, Tuple, Type
from enum import IntEnum

from .enums import CollectionType
from .tables import KNOWN_USAGE_PAGES, ButtonPage

class HIDLookup:
    """
    Utility class for looking up HID usage page names, usage names, and collection types.
    Based on the "registered" HID usage tables via KNOWN_USAGE_PAGES.
    """

    @staticmethod
    def get_page_name(page_id: int) -> str:
        entry = KNOWN_USAGE_PAGES.get(page_id)
        if entry:
            return entry[0]
        
        if 0xFF00 <= page_id <= 0xFFFF:
            return f"Vendor Defined (0x{page_id:04X})"
    
        return f"Unknown Page {page_id:#02x}"
    
    @staticmethod
    def get_usage_name(page_id: int, usage_id: int) -> str:
        
        if usage_id == 0:
            return "Padding / Reserved"
        
        page_info = KNOWN_USAGE_PAGES.get(page_id)

        if page_info and page_info[1]:
            enum_cls: Type[IntEnum] = page_info[1]
            try:
                if page_id == ButtonPage.PAGE_ID:
                    # Special handling for Button Page
                    button_number = ButtonPage.get_button_number(usage_id)
                    return f"Button_{button_number}"
                return enum_cls(usage_id).name.replace(' ','_').title()
            except ValueError:
                pass

        return f"Usage 0x{usage_id:02X}"
    
    @staticmethod
    def get_collection_type(type_id: int) -> str:
        try:
            return CollectionType(type_id).name.replace('_', ' ').title()
        except ValueError:
            return f"Unknown Collection Type {type_id:#02x}"
import struct
from dataclasses import dataclass
from typing import Union, ClassVar
from .tags import ItemTag, ItemType

@dataclass
class SpecItem:
    """
    Represents a generic "Short Item" in a HID Report Descriptor.
    Defined in the spec such as: [Header (1 byte)] + [Data (0, 1, 2, 4 bytes)]
    Header = (Tag & 0xFC) | Size_Code
    """
    tag: int
    data: Union[int, list, None] = None

    def __post_init__(self):
        self.validate()

    def validate(self):
        """Validate the data based on critical constraints."""
        if self.data is not None:
            if not isinstance(self.data, (int, list, bytes, type(None))):
                raise TypeError("Data must be an int, list, bytes, or None, got {}".format(type(self.data)))
        
        # check the data size .. can it fit in 4 bytes?
        if isinstance(self.data, int):
            if not (-2147483648 <= self.data <= 2147483647):
                raise ValueError(f"Data {self.data} too large for HID Short Item (max 4 bytes)")

    def to_bytes(self) -> bytes:
        """Serialize the SpecItem to bytes."""
        value = self.data or 0
        
        if isinstance(value, list) or isinstance(value, bytes):
            payload = bytes(value)
            size_code = len(payload)
            if size_code == 4: size_code = 3  # 4 bytes is represented as 3 in size code
        else:
            if -128 <= value <= 127:
                size_code = 1
                payload = struct.pack('<b', value) # 1 byte signed
            elif -32768 <= value <= 32767:
                size_code = 2
                payload = struct.pack('<h', value) # 2 bytes signed
            elif -2147483648 <= value <= 2147483647:
                size_code = 3
                payload = struct.pack('<i', value) # 4 bytes signed
            else:
                raise ValueError("Value out of range for HID item data.")
        
        # Construct header
        # Tags defined in the spec as: Tag (bits 7-2), Type (bits 1-0)
        # We apply the FC mask to keep only the Tag bits and add the size code
        header = (self.tag & 0xFC) | size_code
        return bytes([header]) + payload
    

    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(data={self.data})"
    
# Main Items
class InputItem(SpecItem):
    def __init__(self, flags: int):
        super().__init__(tag=ItemTag.INPUT, data=flags)

class OutputItem(SpecItem):
    def __init__(self, flags: int):
        super().__init__(tag=ItemTag.OUTPUT, data=flags)

class FeatureItem(SpecItem):
    def __init__(self, flags: int):
        super().__init__(tag=ItemTag.FEATURE, data=flags)

class CollectionItem(SpecItem):
    def __init__(self, collection_type: int):
        super().__init__(tag=ItemTag.COLLECTION, data=collection_type)

class EndCollectionItem(SpecItem):
    def __init__(self, data=None):
        super().__init__(tag=ItemTag.END_COLLECTION, data=None)

    def to_bytes(self):
        return b'\xC0'  # Fixed byte for End Collection
    


# --- Global Items ---

class UsagePageItem(SpecItem):
    def __init__(self, page_id: int):
        super().__init__(tag=ItemTag.USAGE_PAGE, data=page_id)

class LogicalMinItem(SpecItem):
    def __init__(self, value: int):
        super().__init__(tag=ItemTag.LOGICAL_MIN, data=value)
            

class LogicalMaxItem(SpecItem):
    def __init__(self, value: int):
        super().__init__(tag=ItemTag.LOGICAL_MAX, data=value)

class PhysicalMinItem(SpecItem):
    def __init__(self, value: int):
        super().__init__(tag=ItemTag.PHYSICAL_MIN, data=value)

class PhysicalMaxItem(SpecItem):
    def __init__(self, value: int):
        super().__init__(tag=ItemTag.PHYSICAL_MAX, data=value)

class UnitExponentItem(SpecItem):
    def __init__(self, exponent: int):
        super().__init__(tag=ItemTag.UNIT_EXPONENT, data=exponent)

class UnitItem(SpecItem):
    def __init__(self, unit: int):
        super().__init__(tag=ItemTag.UNIT, data=unit)

class ReportSizeItem(SpecItem):
    def __init__(self, size: int):
        super().__init__(tag=ItemTag.REPORT_SIZE, data=size)

    def validate(self):
        super().validate()
        if isinstance(self.data, int) and self.data < 0:
            raise ValueError(f"Report Size cannot be negative: {self.data}")

class ReportCountItem(SpecItem):
    def __init__(self, count: int):
        super().__init__(tag=ItemTag.REPORT_COUNT, data=count)

    def validate(self):
        super().validate()
        if isinstance(self.data, int) and self.data < 0:
            raise ValueError(f"Report Count cannot be negative: {self.data}")

class ReportIDItem(SpecItem):
    def __init__(self, report_id: int):
        super().__init__(tag=ItemTag.REPORT_ID, data=report_id)

class PushItem(SpecItem):
    def __init__(self):
        super().__init__(tag=ItemTag.PUSH, data=None)

class PopItem(SpecItem):
    def __init__(self):
        super().__init__(tag=ItemTag.POP, data=None)

# --- Local Items ---

class UsageItem(SpecItem):
    def __init__(self, usage_id: int):
        super().__init__(tag=ItemTag.USAGE, data=usage_id)

class UsageMinItem(SpecItem):
    def __init__(self, usage_min: int):
        super().__init__(tag=ItemTag.USAGE_MIN, data=usage_min)

class UsageMaxItem(SpecItem):
    def __init__(self, usage_max: int):
        super().__init__(tag=ItemTag.USAGE_MAX, data=usage_max)



# Reverse lookup for item classes based on tags
ITEM_REGISTRY = {
    ItemTag.INPUT: InputItem,
    ItemTag.OUTPUT: OutputItem,
    ItemTag.FEATURE: FeatureItem,
    ItemTag.COLLECTION: CollectionItem,
    ItemTag.END_COLLECTION: EndCollectionItem,
    ItemTag.USAGE_PAGE: UsagePageItem,
    ItemTag.LOGICAL_MIN: LogicalMinItem,
    ItemTag.LOGICAL_MAX: LogicalMaxItem,
    ItemTag.PHYSICAL_MIN: PhysicalMinItem,
    ItemTag.PHYSICAL_MAX: PhysicalMaxItem,
    ItemTag.UNIT_EXPONENT: UnitExponentItem,
    ItemTag.UNIT: UnitItem,
    ItemTag.REPORT_SIZE: ReportSizeItem,
    ItemTag.REPORT_COUNT: ReportCountItem,
    ItemTag.REPORT_ID: ReportIDItem,
    ItemTag.PUSH: PushItem,
    ItemTag.POP: PopItem,
    ItemTag.USAGE: UsageItem,
    ItemTag.USAGE_MIN: UsageMinItem,
    ItemTag.USAGE_MAX: UsageMaxItem,
}
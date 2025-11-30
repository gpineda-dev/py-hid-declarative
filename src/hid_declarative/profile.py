from dataclasses import dataclass
from typing import Optional

from hid_declarative.spec.descriptor import ReportDescriptor
from .schema.nodes import Node



@dataclass
class HIDProfile:
    """
    Configuration container for a HID Device.
    This object links the logical schema (Node tree) with metadata
    required for compilation.
    """
    # The logical tree (The What)
    
    # Metadata (The Who)
    name: str = "HID_Device"
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None
    manufacturer: str = "Unknown"
    serial_number: str = "0000"
    
    # Compilation options (The How)
    auto_pad: bool = True
    
    # Prfile requires either a root node or a raw descriptor
    root: Optional[Node] = None
    raw_descriptor: Optional[bytes] = None
    descriptor: Optional[ReportDescriptor] = None


    def __post_init__(self):
        # Light validation
        if self.raw_descriptor is not None and self.root is not None and self.descriptor is not None:
            raise ValueError("HIDProfile can only have one of root, raw_descriptor or descriptor defined.")

        if self.root is not None:
            if not hasattr(self.root, 'children') and not hasattr(self.root, 'usage_page'):
                raise ValueError("root must be a valid Node (Collection or ReportItem)")
        
    def is_compilable(self) -> bool:
        """Returns True if the profile has a root schema to compile."""
        return self.root is not None
    
    def is_parsable(self) -> bool:
        """Returns True if the profile has a raw descriptor to parse."""
        return self.raw_descriptor is not None
    
    def has_compiled_descriptor(self) -> bool:
        """Returns True if the profile has a compiled descriptor."""
        return self.descriptor is not None
    
    def has_descriptor(self) -> bool:
        """Returns True if the profile has either a raw or compiled descriptor."""
        return self.raw_descriptor is not None or self.descriptor is not None
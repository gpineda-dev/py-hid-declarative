import base64
from dataclasses import dataclass
from typing import List, Dict, Any

from hid_declarative.runtime.context import HIDContext
from hid_declarative.spec import HIDLookup
from hid_declarative.spec.descriptor import ReportDescriptor

from .spec.items import SpecItem
from .runtime.layout import DescriptorLayout, ReportLayout

# Note: is DescriptorResult really usefull? Should this object contains the HIDProfile as well?
# -- is it part of the runtime module ?

@dataclass
class DescriptorResult:
    """Holds the result of analyzing a HID report descriptor."""
    descriptor: ReportDescriptor
    layout: DescriptorLayout

    @classmethod
    def from_context(cls, context: "HIDContext") -> "DescriptorResult":
        """Creates a DescriptorResult from a HIDContext."""
        return cls(
            descriptor=context.descriptor,
            layout=context.descriptor_layout
        )

    @property
    def raw_bytes(self) -> bytes:
        """Returns the raw bytes of the descriptor."""
        return self.descriptor.bytes

    @property
    def size_bytes(self) -> int:
        """Returns the size of the descriptor in bytes."""
        return len(self.raw_bytes)
    
    @property
    def as_hex(self) -> str:
        """Returns the raw bytes as a hex string."""
        return self.raw_bytes.hex().upper()
    
    @property
    def as_base64(self) -> str:
        """Returns the raw bytes as a base64-encoded string."""
        return base64.b64encode(self.raw_bytes).decode('utf-8')
    
    def __post_init__(self):
        for op in self.layout.fields:
            if not op.usage_page_name: 
                op.usage_page_name = HIDLookup.get_page_name(op.usage_page)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the DescriptorResult to a dictionary."""

        return {
            "meta": { 
                "size_bytes": self.size_bytes,
                "hex": self.as_hex,
                "base64": self.as_base64,
            },
            "layout": self.layout.to_dict(),
            "structure": self.descriptor.to_dict(),
        }
        

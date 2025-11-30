from dataclasses import dataclass
from typing import List, Optional

from hid_declarative.schema import Collection, Node, ReportItem
from hid_declarative.schema.nodes import ReportGroup
from hid_declarative.spec import CollectionItem, EndCollectionItem, InputItem, LogicalMaxItem, LogicalMinItem, PhysicalMaxItem, PhysicalMinItem, ReportCountItem, ReportSizeItem, SpecItem, UnitExponentItem, UnitItem, UsageItem, UsageMaxItem, UsageMinItem, UsagePageItem
from hid_declarative.spec import ReportDescriptor
from hid_declarative.spec.items import FeatureItem, OutputItem, ReportIDItem

__doc__ = """
HID Compiler module that transforms a HID schema (AST) into a ReportDescriptor (binary).
It optimizes the output by tracking the state of GLOBAL registers to avoid redundant entries.
"""

@dataclass
class CompilerState:
    """
    Tracks the current state of GLOBAL registers in the generated binary stream.
    Used to optimize output (Deduplication).
    """
    usage_page: Optional[int] = None
    logical_min: Optional[int] = None
    logical_max: Optional[int] = None
    physical_min: Optional[int] = None
    physical_max: Optional[int] = None
    unit_exponent: Optional[int] = None
    unit: Optional[int] = None
    report_size: Optional[int] = None
    report_count: Optional[int] = None
    
    # Cursor for automatic padding
    bit_cursor: int = 0
    current_report_id: int = 0

    def reset(self):
        self.usage_page = None
        self.logical_min = None
        self.logical_max = None
        self.physical_min = None
        self.physical_max = None
        self.unit_exponent = None
        self.unit = None
        self.report_size = None
        self.report_count = None
        self.bit_cursor = 0
        self.current_report_id = 0

class HIDCompiler:
    """
    Compiler that transforms a HID schema into a List of SpecItems.
    """
    def __init__(self):
        self.descriptor = ReportDescriptor()
        self.state = CompilerState()

    def compile(self, root: Node, auto_pad=True) -> ReportDescriptor:
        self.descriptor = ReportDescriptor()
        self.state.reset()
        
        self._visit(root)
        
        if auto_pad:
            self._align_to_byte()
            
        return self.descriptor
    
    def _visit(self, node: Node):
        if isinstance(node, Collection):
            self._emit_collection(node)
        elif isinstance(node, ReportItem):
            self._emit_item(node)
        elif isinstance(node, ReportGroup):
            self._emit_report_scope(node)

    def _emit_report_scope(self, node: ReportGroup):
        if node.id != self.state.current_report_id:
            self.descriptor.append(ReportIDItem(node.id))
            self.state.current_report_id = node.id

        for child in node.children:
            self._visit(child)

    def _emit_collection(self, node: Collection):
        # 1. Define Usage Page if needed
        if node.usage_page != self.state.usage_page:
            self.descriptor.append(UsagePageItem(node.usage_page))
            self.state.usage_page = node.usage_page
            
        # 2. Usage of the collection
        self.descriptor.append(UsageItem(node.usage))
        
        # 3. Opening
        self.descriptor.append(CollectionItem(node.type_id))
        
        # 4. Children
        for child in node.children:
            self._visit(child)
            
        # 5. Closing
        self.descriptor.append(EndCollectionItem())

    def _emit_item(self, node: ReportItem):
        """
        Internal method to emit a ReportItem into the descriptor,
        optimizing the output by tracking the state of GLOBAL registers.
        """

        is_padding = node.is_constant and node.usages
        if not is_padding and node.usage_page != self.state.usage_page:
             self.descriptor.append(UsagePageItem(node.usage_page))
             self.state.usage_page = node.usage_page

        if node.logical_min != self.state.logical_min:
            self.descriptor.append(LogicalMinItem(node.logical_min))
            self.state.logical_min = node.logical_min

        if node.logical_max != self.state.logical_max:
            self.descriptor.append(LogicalMaxItem(node.logical_max))
            self.state.logical_max = node.logical_max

        if node.physical_min is not None and node.physical_min != self.state.physical_min:
            self.descriptor.append(PhysicalMinItem(node.physical_min))
            self.state.physical_min = node.physical_min
        
        if node.physical_max is not None and node.physical_max != self.state.physical_max:
            self.descriptor.append(PhysicalMaxItem(node.physical_max))
            self.state.physical_max = node.physical_max

        if node.unit_exponent is not None and node.unit_exponent != self.state.unit_exponent:
            self.descriptor.append(UnitExponentItem(node.unit_exponent))
            self.state.unit_exponent = node.unit_exponent

        if node.unit is not None and node.unit != self.state.unit:
            self.descriptor.append(UnitItem(node.unit))
            self.state.unit = node.unit

        if node.size != self.state.report_size:
            self.descriptor.append(ReportSizeItem(node.size))
            self.state.report_size = node.size

        if node.count != self.state.report_count:
            self.descriptor.append(ReportCountItem(node.count))
            self.state.report_count = node.count

        # --- Emission of Usages ---
        if not node.usages:
            pass # Padding
        elif len(node.usages) == 1:
            self.descriptor.append(UsageItem(node.usages[0]))
        else:
            # Optimization "Range" (1, 2, 3 -> Min 1, Max 3)
            # Check if the list is contiguous: [1, 2, 3] ok, [1, 3] not ok
            is_contiguous = True
            if len(node.usages) > 1:
                sorted_usages = sorted(node.usages)
                for i in range(1, len(sorted_usages)):
                    if sorted_usages[i] != sorted_usages[i-1] + 1:
                        is_contiguous = False
                        break
            
            if is_contiguous and len(node.usages) > 1:
                self.descriptor.append(UsageMinItem(node.usages[0]))
                self.descriptor.append(UsageMaxItem(node.usages[-1]))
            else:
                for u in node.usages:
                    self.descriptor.append(UsageItem(u))

        # --- Emission of the Input/Output/Feature item ---
        flags = 0
        if node.is_constant:  flags |= 0x01  # Const
        if not node.is_array: flags |= 0x02  # Variable
        if node.is_relative:  flags |= 0x04  # Relative

        rtype = node.report_type.lower()
        if rtype == "input":
            self.descriptor.append(InputItem(flags))
        elif rtype == "output":
            self.descriptor.append(OutputItem(flags))
        elif rtype == "feature":
            self.descriptor.append(FeatureItem(flags))
        else:
            raise ValueError(f"Unknown report type: {node.report_type}")

        # Advance the bit cursor for auto-padding purposes
        self.state.bit_cursor += (node.size * node.count)

    def _align_to_byte(self):
        """Adds padding if we do not end on a complete byte."""
        remainder = self.state.bit_cursor % 8
        if remainder != 0:
            pad_size = 8 - remainder
            # For padding, we force the writing of properties
            # because we do not want to depend on the previous state
            self.descriptor.append(ReportSizeItem(pad_size))
            self.descriptor.append(ReportCountItem(1))
            self.descriptor.append(InputItem(0x01 | 0x02)) # Const, Var
            # We do not update the state here because this is an end of cycle
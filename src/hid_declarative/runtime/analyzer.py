from typing import Dict, List

from hid_declarative.spec.descriptor import ReportDescriptor

from ..spec.items import SpecItem, InputItem
from hid_declarative.spec.lookup import HIDLookup
from ..spec.tags import ItemTag
from .layout import DescriptorLayout, FieldOp, ReportLayout

class ScanState:
    """Holds the state while scanning HID report descriptors."""
    def __init__(self):
        # Global Items
        self.usage_page: int = 0
        self.logical_min: int = 0
        self.logical_max: int = 0
        self.physical_min: int = 0
        self.physical_max: int = 0
        self.unit_exponent: int = 0
        self.unit: int = 0
        self.report_size: int = 0
        self.report_count: int = 0
        self.report_id: int = 0

        # Local Items
        self.usages: List[int] = []
        self.usage_min: int = 0
        self.usage_max: int = 0
        self._pending_min: int = 0

        # Virtual cursor (Position in bits)
        self.cursors: Dict[int, Dict[str, int]] = {}
        self.current_report_id: int = 0

        self._global_stack: List[Dict[str, int]] = []

    def push(self):
        """Push the current state onto a stack."""
        snapshot = {
            'usage_page': self.usage_page,
            'logical_min': self.logical_min,
            'logical_max': self.logical_max,
            'physical_min': self.physical_min,
            'physical_max': self.physical_max,
            'unit_exponent': self.unit_exponent,
            'unit': self.unit,
            'report_size': self.report_size,
            'report_count': self.report_count,
            'report_id': self.report_id,
        }
        self._global_stack.append(snapshot)

    def pop(self):
        """Pop the last state from the stack."""
        if not self._global_stack:
            return # Stack underflow (Spec HID: behavior undefined -> ignore)
        
        snapshot = self._global_stack.pop()
        self.usage_page = snapshot['usage_page']
        self.logical_min = snapshot['logical_min']
        self.logical_max = snapshot['logical_max']
        self.physical_min = snapshot['physical_min']
        self.physical_max = snapshot['physical_max']
        self.unit_exponent = snapshot['unit_exponent']
        self.unit = snapshot['unit']
        self.report_size = snapshot['report_size']
        self.report_count = snapshot['report_count']
        self.report_id = snapshot['report_id']

    def get_cusror(self, report_type: str, report_id: int = None) -> int:
        """Get the current bit cursor for a given report type and ID."""
        rid = report_id if report_id is not None else self.current_report_id
        if rid not in self.cursors:
            self.cursors[rid] = {'input': 0, 'output': 0, 'feature': 0}
        return self.cursors[rid].get(report_type, 0)
    
    def advance_cursor(self, report_type: str, amount: int, report_id: int = None):
        """Advance the bit cursor for a given report type and ID."""
        rid = report_id if report_id is not None else self.current_report_id
        if rid not in self.cursors:
            self.cursors[rid] = {'input': 0, 'output': 0, 'feature': 0}
        self.cursors[rid][report_type] += amount
    
class DescriptorAnalyzer:
    """Analyzes HID report descriptors and builds field operations."""
    
    def analyze(self, descriptor: ReportDescriptor) -> DescriptorLayout:
        state = ScanState()
        layout = DescriptorLayout()
        name_tracker: Dict[str, int] = {}

        for item in descriptor:
            # 1. Handle Global Items
            if item.tag == ItemTag.USAGE_PAGE:
                state.usage_page = item.data if item.data is not None else 0
            elif item.tag == ItemTag.LOGICAL_MIN:
                state.logical_min = item.data if item.data is not None else 0
            elif item.tag == ItemTag.LOGICAL_MAX:
                state.logical_max = item.data if item.data is not None else 0
            elif item.tag == ItemTag.PHYSICAL_MIN:
                state.physical_min = item.data if item.data is not None else 0
            elif item.tag == ItemTag.PHYSICAL_MAX:
                state.physical_max = item.data if item.data is not None else 0
            elif item.tag == ItemTag.UNIT_EXPONENT:
                state.unit_exponent = item.data if item.data is not None else 0
            elif item.tag == ItemTag.UNIT:
                state.unit = item.data if item.data is not None else 0
            elif item.tag == ItemTag.REPORT_SIZE:
                state.report_size = item.data if item.data is not None else 0
            elif item.tag == ItemTag.REPORT_COUNT:
                state.report_count = item.data if item.data is not None else 0
            elif item.tag == ItemTag.REPORT_ID:
                state.current_report_id = item.data if item.data is not None else 0
                state.bit_cursor = 0  # Reset cursor for new report ID

            elif item.tag == ItemTag.PUSH:
                state.push()
            elif item.tag == ItemTag.POP:
                state.pop()
            
            # 2. Handle Local Items
            elif item.tag == ItemTag.USAGE_MIN:
                state._pending_min = item.data
            elif item.tag == ItemTag.USAGE_MAX:
                if hasattr(state, '_pending_min'):
                     state.usages.extend(range(state._pending_min, item.data + 1))
                     del state._pending_min
            elif item.tag == ItemTag.USAGE:
                if item.data is not None:
                    state.usages.append(item.data)

            # 3. Handle Main Items
            elif item.tag == ItemTag.COLLECTION:
                state.usages.clear()  # Clear usages on new collection
            
            elif item.tag == ItemTag.INPUT:
                self._process_main_item(state, layout, "input", item.data if item.data is not None else 0, name_tracker)
            elif item.tag == ItemTag.OUTPUT:
                self._process_main_item(state, layout, "output", item.data if item.data is not None else 0, name_tracker)
            elif item.tag == ItemTag.FEATURE:
                self._process_main_item(state, layout, "feature", item.data if item.data is not None else 0, name_tracker)

        return layout
    
    def _process_main_item(self, state: ScanState, layout: DescriptorLayout, rtype: str, flags: int, name_tracker: Dict[str, int]):
        new_ops = self._generate_ops(state, rtype, name_tracker, flags)
        current_id = state.current_report_id
        for op in new_ops:
            layout.add_field(field=op, report_id=current_id)
        state.usages.clear()  # Clear usages after processing
    
    def _generate_ops(self, state: ScanState, report_type: str, tracker: Dict[str, int], flags: int) -> List[FieldOp]:
        ops: List[FieldOp] = []
        count = state.report_count
        size = state.report_size

        is_signed = state.logical_min < 0
        current_offset = state.get_cusror(report_type)
        is_array = not (flags & 0x02)

        for i in range(count):
            usage_id = 0
            if len(state.usages) > 0:
                if i < len(state.usages):
                    usage_id = state.usages[i]
                else:
                    usage_id = state.usages[-1]  # Repeat last usage if not enough

            # 1. Resolve base name
            if is_array:
                page_name = self._resolve_page_name_only(state.usage_page)
                base_name = f"{page_name} Idx"
            else:
                base_name = self._resolve_name(state.usage_page, usage_id)
            
            # 2. Handle collisions (X -> X_2 -> X_3)
            final_name = base_name
            
            # Ignore padding for uniqueness (we don't care)
            if base_name != "Padding":
                if base_name in tracker:
                    tracker[base_name] += 1
                    final_name = f"{base_name}_{tracker[base_name]}"
                else:
                    tracker[base_name] = 1
            
            op = FieldOp(
                bit_offset=current_offset,
                bit_size=size,
                usage_page=state.usage_page,
                usage_id=usage_id,
                logical_min=state.logical_min,
                logical_max=state.logical_max,
                physical_min=state.physical_min,
                physical_max=state.physical_max,
                is_signed=is_signed,
                report_type=report_type,
                name=final_name
            )

            ops.append(op)
            current_offset += size
        
        state.advance_cursor(report_type, size * count)
        return ops
        
    def _resolve_name(self, page: int, usage: int) -> str:
        return HIDLookup.get_usage_name(page, usage)
        
    def _resolve_page_name_only(self, page: int) -> str:
        return HIDLookup.get_page_name(page)

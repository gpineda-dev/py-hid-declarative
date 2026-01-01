from typing import Any, Dict, List, Optional, Tuple, Union
from hid_declarative.runtime.layout import DescriptorLayout, ReportLayoutGroup
from hid_declarative.runtime.reports import DataFeatureReport, DataInputReport, DataOutputReport, DataReportType

__doc__ = """
HIDReportCodec module provides encoding and decoding functionalities for HID reports (fixed report_id, type)
based on a given DescriptorLayout.
"""

class HIDReportCodec:

    TYPE = None  # To be defined in subclasses: "input", "output", "feature"

    def __init__(self, layout: ReportLayoutGroup):
        assert isinstance(layout, ReportLayoutGroup), "layout must be an instance of ReportLayoutGroup"
        assert layout.report_type == self.TYPE, f"Layout report type '{layout.report_type}' does not match class TYPE '{self.TYPE}'"
        self.layout: ReportLayoutGroup = layout

    @property
    def report_id(self) -> int:
        return self.layout.report_id
    
    @property
    def report_type(self) -> str:
        return self.layout.report_type
    
    @property
    def size_bytes(self) -> Optional[int]:
        return self.layout.size_bytes
    
    def get_layout(self) -> ReportLayoutGroup:
        return self.layout
    
    def create_report(self) -> DataReportType:
        raise NotImplementedError("Subclasses must implement create_report() method.")
    
    def decode_payload(self, payload: bytes, raise_if_invalid_size: bool = True) -> Dict[str, Any]:
        """Decode raw payload bytes into a dictionary of field values based on the layout."""
        result = {}

        # check if payload has the expected size
        if raise_if_invalid_size:
            expected_size = self.size_bytes
            if expected_size is not None and len(payload) != expected_size:
                raise ValueError(
                    f"Payload size {len(payload)} does not match expected size {expected_size} "
                    f"for report ID {self.report_id}."
                )
            
        fields = self.layout.fields
        if not fields:
            return result
        
        # Convert payload to a big integer for bit manipulation
        big_int = int.from_bytes(payload, byteorder='little')

        for op in fields:
            
            if op.usage_id == 0: continue  # Skip padding fields

            # 1. Extract the raw value
            mask = (1 << op.bit_size) - 1
            val = (big_int >> op.bit_offset) & mask

            # 2. Handle signed values
            if op.is_signed and (val & (1 << (op.bit_size - 1))):
                val -= (1 << op.bit_size)
            
            key = op.name

            if op.usage_page == 0x09 and op.bit_size == 1:
                 result[key] = bool(val)
            else:
                 result[key] = val

        return result
    
    def encode_payload(self, data: Dict[str, Any], validate: bool = True) -> bytes:
        if validate:
            self.layout.validate(data)

        fields = self.layout.fields
        size = self.layout.size_bytes
        if size is None:
            raise ValueError(f"Report size is zero for report ID {self.report_id}.")
        
        big_int = 0

        for op in fields:
            val = int(data.get(op.name, 0))

            mask = (1 << op.bit_size) - 1
            if val < 0: val = (1 << op.bit_size) + val
            if val < 0 or val > mask:
                raise ValueError(f"Value for field '{op.name}' ({val}) out of range for size {op.bit_size} bits.")

            # Set the bits in the big integer
            big_int |= (val & mask) << op.bit_offset
        
        payload = big_int.to_bytes(size, byteorder='little')
        return payload


class ReportInputCodec(HIDReportCodec):
    TYPE = "input"

    def create_report(self) -> DataInputReport:
        return DataInputReport.from_layout_group(self.layout)
    
    def decode_payload(self, payload, raise_if_invalid_size = True) -> DataInputReport:
        return super().decode_payload(payload, raise_if_invalid_size)
    
    def encode_payload(self, data: Dict[str, Any], validate: bool = True) -> bytes:
        return super().encode_payload(data, validate)
    
class ReportOutputCodec(HIDReportCodec):
    TYPE = "output"

    def create_report(self) -> DataOutputReport:
        return DataOutputReport.from_layout_group(self.layout)
    
    def decode_payload(self, payload, raise_if_invalid_size = True) -> DataOutputReport:
        return super().decode_payload(payload, raise_if_invalid_size)
    
    def encode_payload(self, data: Dict[str, Any], validate: bool = True) -> bytes:
        return super().encode_payload(data, validate)
    
class ReportFeatureCodec(HIDReportCodec):
    TYPE = "feature"

    def create_report(self) -> DataFeatureReport:
        return DataFeatureReport.from_layout_group(self.layout)
    
    def decode_payload(self, payload, raise_if_invalid_size = True) -> DataFeatureReport:
        return super().decode_payload(payload, raise_if_invalid_size)
    
    def encode_payload(self, data: Dict[str, Any], validate: bool = True) -> bytes:
        return super().encode_payload(data, validate)
    
    
REPORT_CODEC_MAP = {
    "input": ReportInputCodec,
    "output": ReportOutputCodec,
    "feature": ReportFeatureCodec,
}


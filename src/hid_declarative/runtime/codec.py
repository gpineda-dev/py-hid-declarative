from typing import Any, Dict, List, Optional, Tuple, Union
from hid_declarative.runtime.layout import DescriptorLayout, ReportLayoutGroup
from hid_declarative.runtime.reports import DataFeatureReport, DataInputReport, DataOutputReport, DataReportType

__doc__ = """
HIDCodec module provides encoding and decoding functionalities for HID reports
based on a given DescriptorLayout.
"""

class HIDCodec:
    """
    Encoder/Decoder for HID reports based on a given DescriptorLayout.
    Are supported report types: "input", "output", "feature".
    """

    def __init__(self, map_layout: DescriptorLayout):
        assert isinstance(map_layout, DescriptorLayout), "layout must be an instance of DescriptorLayout"
        self.map_layout = map_layout

       
    def _extract_report_id(self, data: bytes) -> Tuple[int, bytes]:
        """
        Analyze the raw data to separate the report ID (if any) from the payload.
        Returns:
            report_id (int): The report ID extracted (0 if none).
            payload (bytes): The remaining data after removing the report ID byte.
        """

        if not data:
            return None, b''
        
        if self.map_layout.has_multiple_report_ids():
            report_id = data[0]
            payload = data[1:]
            return report_id, payload
        
        return None, data

    def create_report(self, report_id: Optional[int] = None, report_type: Optional[str] = "input") -> DataReportType:
        """Create an empty DataReport for the specified report ID."""
        target_id = self.map_layout.resolve_report_id(report_id)

        layout = self.map_layout.get_report_layout_group(target_id, report_type=report_type, raise_if_not_found=True)
        if report_type == "input":
            return DataInputReport.from_layout_group(layout)
        elif report_type == "output":
            return DataOutputReport.from_layout_group(layout)
        elif report_type == "feature":
            return DataFeatureReport.from_layout_group(layout)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def decode(self, data: bytes, report_type: Optional[str] = "input", raise_if_invalid_size: bool = True) -> DataReportType:
        """Decode raw bytes into a dictionary of field values based on the layout."""
        
        report_id, payload = self._extract_report_id(data)
        report_id = self.map_layout.resolve_report_id(report_id)
        result = self.create_report(report_id=report_id, report_type=report_type)

        
        # check if payload has the expected size
        if raise_if_invalid_size:
            expected_size = self.map_layout.get_size(report_id, report_type=report_type)
            if expected_size is not None and len(payload) != expected_size:
                raise ValueError(
                    f"Payload size {len(payload)} does not match expected size {expected_size} "
                    f"for report ID {report_id}."
                )

        fields = self.map_layout.get_fields(report_id, report_type=report_type)
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
    
    def encode(self, data: Dict[str, Any], report_id: Optional[int] = None, report_type: Optional[str] = "input", validate: bool = True) -> bytes:
        """Encode a dictionary of field values into raw bytes based on the layout and report_id."""
        target_id = self.map_layout.resolve_report_id(report_id)

        layout: ReportLayoutGroup = self.map_layout.get_report_layout_group(target_id, report_type=report_type, raise_if_not_found=True)
        if validate:
            layout.validate(data)

        fields = layout.fields
        size = layout.size_bytes
        if size is None:
            raise ValueError(f"Report size is zero for report ID {report_id}.")
        
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

        if self.map_layout.has_multiple_report_ids():
            return bytes([report_id]) + payload
        return payload
    
    
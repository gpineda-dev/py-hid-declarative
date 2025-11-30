from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from hid_declarative.runtime.layout import ReportLayout, ReportLayoutGroup

if TYPE_CHECKING:
    from .codec import HIDCodec

__doc__ = """
HID Reports module defines classes for representing HID reports (input, output, feature)
and provides methods for encoding, decoding, and manipulating report data.

A Data*Report is consumed for encoding (raw bytes) via HIDCodec.encode() and produced
by HIDCodec.decode() from raw bytes.
"""

class DataBaseReport:
    """
    Base class for HID Data Reports (Input, Output, Feature).
    Provides methods for manipulating report data, encoding, decoding, and computing deltas.

    Please use the specialized subclasses:
    - DataInputReport
    - DataOutputReport
    - DataFeatureReport
    """

    TYPE = None  # To be defined in subclasses: "input", "output", "feature"

    @classmethod
    def from_layout(cls, layout: ReportLayout, report_type: str) -> 'DataBaseReport':
        if cls.TYPE is not None:
            assert report_type == cls.TYPE, f"Layout report type '{report_type}' does not match class TYPE '{cls.TYPE}'"

        ReportLayout.raise_if_not_group_type(report_type)
        group = layout.get_group(report_type)
        return cls(layout=group)

    @classmethod
    def from_layout_group(cls, layout: ReportLayoutGroup) -> 'DataBaseReport':
        return cls(layout=layout)

    def __init__(self, layout: ReportLayoutGroup, initial_data: Optional[Dict[str, Any]] = None):
        assert isinstance(layout, ReportLayoutGroup), f"layout must be an instance of ReportLayoutGroup, got {type(layout)}"
        if self.TYPE is not None:
            assert layout.report_type == self.TYPE, f"Layout report type '{layout.report_type}' does not match class TYPE '{self.TYPE}'"
        else:
            assert layout.report_type in ReportLayout.list_group_types(), f"Unknown report type: {layout.report_type}"
        
        self.layout = layout
        self._values = layout.get_default_values()

        if initial_data:
            self._values.update(initial_data)

    @property
    def report_type(self) -> str:
        return self.layout.report_type

    @property
    def report_id(self) -> int:
        return self.layout.report_id
    
    def validate(self):
        self.layout.validate(self._values)
    
    def __iter__(self):
        return iter(self._values.items())
    
    def __getitem__(self, key: str) -> Any:
        return self._values[key]
    
    def __setitem__(self, key: str, value: Any):
        if key not in self._values:
            raise KeyError(f"Field '{key}' not found in report layout.")
        self._values[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._values)
    
    def encode(self, codec: 'HIDCodec') -> bytes:
        """Encodes the report data into raw bytes using the provided HIDCodec once validated."""
        self.validate()
        return codec.encode(data=self._values, report_id=self.report_id, report_type=self.report_type)
    

    def delta(self, other: 'DataBaseReport') -> Dict[str, Union[int, float]]:
        """Computes the delta between this report and another report."""
        if self.report_id != other.report_id:
            raise ValueError("Cannot compute delta: Report IDs do not match.")
        
        if self.report_type != other.report_type:
            raise ValueError("Cannot compute delta: Report types do not match.")
        
        deltas = {}
        for field in self.layout:
            name = field.name
            val1 = self._values.get(name)
            val2 = other._values.get(name)
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                delta_val = val2 - val1
                if delta_val != 0:
                    deltas[name] = delta_val
        return deltas
    
    def copy(self) -> 'DataBaseReport':
        copied_values = self.to_dict()
        return self.__class__(layout=self.layout, initial_data=copied_values)
    

class DataInputReport(DataBaseReport):
    """
    Data container for an HID Input Report.
    """
    TYPE = "input"

    def delta(self, other: 'DataInputReport') -> Dict[str, Union[int, float]]:
        """Computes the delta between this input report and another input report."""
        return super().delta(other)

class DataOutputReport(DataBaseReport):
    """
    Data container for an HID Output Report.
    """
    TYPE = "output"

    def delta(self, other: 'DataOutputReport') -> Dict[str, Union[int, float]]:
        """Computes the delta between this output report and another output report."""
        return super().delta(other)

class DataFeatureReport(DataBaseReport):
    """
    Data container for an HID Feature Report.
    """
    TYPE = "feature"

    def delta(self, other: 'DataFeatureReport') -> Dict[str, Union[int, float]]:
        """Computes the delta between this feature report and another feature report."""
        return super().delta(other)


DataReportType = Union[DataInputReport, DataOutputReport, DataFeatureReport]
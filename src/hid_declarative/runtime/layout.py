from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

__doc__ = """
HID Descriptor Layout Representation

Once the HID descriptor has been parsed, its layout can be represented.
This is a tokenized representation of the HID report descriptor structure,
focusing on the fields and their properties for encoding/decoding reports.

This is a multi-layered structure:
- DescriptorLayout: The top-level container for multiple ReportLayouts.
- ReportLayout: Represents an individual HID report (report_id fixed), containing input, output, and feature report groups.
- ReportLayoutGroup: Represents a group of fields for a specific report type (input, output, feature).
- FieldOp: Represents a single field within a report, including its bit offset, size, usage, and logical/physical properties.
"""


@dataclass
class FieldOp:
    """
    Represent a field in the message report layout.
    This dataclass encapsulates both the bit-level details and semantic information
    about a field in a HID report.
    """

    # Bit-level details on location and size
    bit_offset: int
    bit_size: int
    
    # Semantic details
    usage_page: int
    usage_id: int
    name: str = "Unknown"

    # Mathematical and physical properties
    logical_min: int = 0
    logical_max: int = 0
    physical_min: int = 0
    physical_max: int = 0

    is_signed: bool = False

    # Type of report this field belongs to
    report_id: int = 0
    report_type: Literal["input", "output", "feature"] = "input"

    usage_page_name: str = ""  # Optional: resolved name of the usage page

    @property
    def mask(self) -> int:
        """Returns the bitmask for this field based on its size."""
        return (1 << self.bit_size) - 1
    
    @property
    def byte_offset(self) -> int:
        """Returns the byte offset of this field in the report."""
        return self.bit_offset // 8

    def to_dict(self) -> dict:
        """Converts the FieldOp to a dictionary representation."""
        return {
            "bit_offset": self.bit_offset,
            "bit_size": self.bit_size,
            "mask": self.mask,
            "byte_offset": self.byte_offset,
            "usage_page": self.usage_page,
            "usage_id": self.usage_id,
            "name": self.name,
            "logical_min": self.logical_min,
            "logical_max": self.logical_max,
            "physical_min": self.physical_min,
            "physical_max": self.physical_max,
            "is_signed": self.is_signed,
            "report_type": self.report_type,
            "report_id": self.report_id,
            "usage_page_name": self.usage_page_name,
        }
    
    def validate_value(self, value: Any) -> bool:
        """Validates if the given value fits within the logical range of this field."""
        return self.logical_min <= value <= self.logical_max

    def get_default_value(self) -> Any:
        """Returns the default value for this field based on its logical minimum."""
        return self.logical_min if self.is_signed else 0

        


@dataclass
class ReportLayoutGroup:
    report_type: Literal["input", "output", "feature"]
    fields: List[FieldOp] = field(default_factory=list)
    _size_bytes: int = None
    report_id: int = 0

    @property
    def size_bytes(self) -> int:
        """Cached size in bytes of the report group, recomputed when fields are added."""
        if self._size_bytes is None:
            self._size_bytes = self.compute_endbyte()
        return self._size_bytes


    def add_field(self, field: FieldOp):
        """Add a field to the report group and invalidate cached size."""
        assert field.report_type == self.report_type, f"Field report type mismatch ({field.report_type} != {self.report_type})"
        field.report_id = self.report_id
        self.fields.append(field)
        self._size_bytes = None

    def compute_endbyte(self) -> int:
        """Computes the size in bytes of the report group based on its fields."""
        end_byte = 0
        for field in self.fields:
            field_end = (field.bit_offset + field.bit_size + 7) // 8
            if field_end > end_byte:
                end_byte = field_end
        return end_byte
    
    def __len__(self) -> int:
        return len(self.fields)
    
    def __iter__(self):
        return iter(self.fields)
    
    def to_dict(self) -> dict:
        """Converts the ReportLayoutGroup to a dictionary representation."""
        return {
            "report_type": self.report_type,
            "report_id": self.report_id,
            "size_bytes": self.size_bytes,
            "fields": [f.to_dict() for f in self.fields]
        }
    
    def get_default_values(self) -> Dict[str, Any]:
        """Returns a dictionary of default values for all fields in the report group."""
        defaults = {}
        for field in self.fields:
            defaults[field.name] = field.get_default_value()
        return defaults
    
    def validate(self, data: Dict[str, Any], allow_missing: bool = False, allow_extra: bool = False):
        """Validates the provided data against the report group layout."""
        for field in self.fields:
            if field.name not in data:
                if not allow_missing:
                    raise KeyError(f"Field '{field.name}' missing in data.")
                else:
                    continue
            value = data[field.name]
            if not field.validate_value(value):
                raise ValueError(
                    f"Value {value} for field '{field.name}' out of range "
                    f"({field.logical_min} to {field.logical_max})."
                )
        if not allow_extra:
            for key in data.keys():
                if key not in [f.name for f in self.fields]:
                    raise KeyError(f"Extra field '{key}' found in data.")
                
    def has_fields(self) -> bool:
        return len(self.fields) > 0
                


@dataclass
class ReportLayout:
    """
    Represents the layout of an individual HID report (report_id fixed), containing input, output, and feature report groups.
    """
    input: ReportLayoutGroup = field(default_factory=lambda: ReportLayoutGroup(report_type="input"))
    output: ReportLayoutGroup = field(default_factory=lambda: ReportLayoutGroup(report_type="output"))
    feature: ReportLayoutGroup = field(default_factory=lambda: ReportLayoutGroup(report_type="feature"))

    report_id: int = 0

    @classmethod
    def list_group_types(cls) -> List[str]:
        return ["input", "output", "feature"]

    @classmethod
    def is_group_type(cls, report_type: str) -> bool:
        """Checks if the given report_type is a valid group type."""
        return report_type in cls.list_group_types()
    
    @classmethod
    def raise_if_not_group_type(cls, report_type: str):
        """Raises a ValueError if the given report_type is not a valid group type."""
        if not cls.is_group_type(report_type):
            raise ValueError(f"Unknown report type: {report_type}")
    
    @classmethod
    def from_fields(cls, report_id: int, fields: List[FieldOp]) -> 'ReportLayout':
        """Creates a ReportLayout from a list of FieldOp for the given report_id (ie. fields.report_id is enforced)."""
        layout = cls(report_id=report_id)
        for field in fields:
            layout.add_field(field)
        return layout

    @property
    def fields(self) -> List[FieldOp]:
        """Returns all fields across input, output, and feature report groups."""
        all_fields = []
        all_fields.extend(self.input.fields)
        all_fields.extend(self.output.fields)
        all_fields.extend(self.feature.fields)
        return all_fields

    def to_dict(self) -> dict:
        """Converts the ReportLayout to a dictionary representation."""
        return {
            "report_id": self.report_id,
            "input": self.input.to_dict(),
            "output": self.output.to_dict(),
            "feature": self.feature.to_dict(),
        }
    
    def get_group(self, report_type: Literal["input", "output", "feature"]) -> ReportLayoutGroup:
        """Returns the ReportLayoutGroup for the specified report type."""
        if report_type == "input":
            return self.input
        elif report_type == "output":
            return self.output
        elif report_type == "feature":
            return self.feature
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
    def add_field(self, field: FieldOp):
        """Adds a field to the report layout and updates size."""
        assert field.report_id == self.report_id, f"Field report ID mismatch ({field.report_id} != {self.report_id})"

        field.report_id = self.report_id
        group = self.get_group(field.report_type)
        group.add_field(field)



        
class DescriptorLayout:
    """
    A container for multiple ReportLayouts, representing the full HID descriptor layout.
    """

    def __init__(self):
        self.reports: Dict[int, ReportLayout] = {}

    def list_report_ids(self) -> List[int]:
        return list(self.reports.keys())
    
    def get_report_layout(self, report_id: int, raise_if_not_found: bool = False) -> Optional[ReportLayout]:
        """
        Retrieves the ReportLayout for a given report ID.
        Args:
            report_id: The ID of the report.
            raise_if_not_found: If True, raises a KeyError if the report ID is not found.
        Returns:
            The ReportLayout for the report ID, or None if not found and raise_if_not_found is False.
        """        
        layout = self.reports.get(report_id)
        if layout is None and raise_if_not_found:
            raise KeyError(f"Report ID {report_id} not found in layout.")
        return layout
    
    def get_report_layout_group(self, report_id: int, report_type: Literal["input", "output", "feature"], raise_if_not_found: bool = False) -> Optional[ReportLayoutGroup]:
        """
        Retrieves the ReportLayoutGroup for a given report ID and type.
        Args:
            report_id: The ID of the report.
            report_type: The type of the report ("input", "output", "feature").
            raise_if_not_found: If True, raises a KeyError if the report ID is not found.
        Returns:
            The ReportLayoutGroup for the report ID and type, or None if not found and raise_if_not_found is False.
        """        
        layout = self.get_report_layout(report_id, raise_if_not_found=raise_if_not_found)
        if layout is None:
            return None
        return layout.get_group(report_type)
    
    def has_multiple_report_ids(self) -> bool:
        """Checks if the layout contains multiple report IDs."""
        keys = list(self.reports.keys())
        if not keys: return False
        if len(keys) > 1: return True
        return keys[0] != 0

    def set_report_layout(self, report_layout: ReportLayout):
        """Sets (replaces) the ReportLayout for a given report ID."""
        self.reports[report_layout.report_id] = report_layout

    def add_field(self, field: FieldOp, report_id: Optional[int] = None):
        """Adds a field to the specified report ID layout."""
        report_id = self.resolve_report_id(report_id, raise_if_not_found=False) or report_id or 0
        self.initialise_report_layout(report_id)
        field.report_id = report_id
        self.reports[report_id].add_field(field)

    def initialise_report_layout(self, report_id: int):
        """Initializes an empty ReportLayout for the given report ID."""
        if report_id not in self.reports:
            self.reports[report_id] = ReportLayout(report_id=report_id)

    def resolve_report_id(self, report_id: Optional[int] = None, raise_if_not_found: bool = True) -> int:
        """Resolves the report ID, ensuring it's unambiguous (ie. only one report ID exists if none is provided)."""
        if report_id is not None:
            if report_id in self.reports:
                return report_id
            else:
                if raise_if_not_found:
                    raise KeyError(f"Report ID {report_id} not found in layout.")
                return None
        
        available_ids = sorted(self.list_report_ids())
        if len(available_ids) > 1:
            raise ValueError(f"Ambiguous: Device has multiple Report IDs {available_ids}, but none was specified.")
        elif not available_ids:
            return 0
        return available_ids[0]

    def to_dict(self) -> dict:
        """Converts the DescriptorLayout to a dictionary representation."""
        return {
            "reports": {
                rid: self.reports[rid].to_dict()
                for rid in self.reports
            }
        }
    
    def get_flatted_fields(self) -> List[FieldOp]:
        """Returns all fields across all report layouts in a flattened list (as references)."""
        all_fields = []
        for rid in sorted(self.reports.keys()):
            all_fields.extend(self.reports[rid].fields)
        return all_fields
    
    @classmethod
    def from_fields(cls, fields: List[FieldOp]) -> 'DescriptorLayout':
        """Creates a DescriptorLayout from a list of FieldOps."""
        layout = cls()
        for field in fields:
            layout.add_field(field, field.report_id)
        return layout

    @property
    def fields(self) -> List[FieldOp]:
        """Returns all fields across all report layouts."""
        return self.get_flatted_fields()

    def get_fields(self, report_id: Optional[int] = None, report_type: Optional[Literal["input", "output", "feature"]] = None, raise_if_not_found: bool = False) -> Optional[List[FieldOp]]:
        """
        Retrieves the fields for a given report ID.

        Args:
            report_id: The ID of the report.
            raise_if_not_found: If True, raises a KeyError if the report ID is not found.
        Returns:
            A list of FieldOp for the report, or None if not found and raise_if_not_found is False.
        """
        report_type = report_type or "input"
        ReportLayout.raise_if_not_group_type(report_type)

        report_id = self.resolve_report_id(report_id, raise_if_not_found=raise_if_not_found)
        layout = self.reports.get(report_id)
        if layout is None:
            if raise_if_not_found:
                raise KeyError(f"Report ID {report_id} not found in layout.")
            return None
        return layout.get_group(report_type).fields if layout else None

    def get_size(self, report_id: Optional[int] = None, report_type: Optional[Literal["input", "output", "feature"]] = None, raise_if_not_found: bool = False) -> Optional[int]:
        """
        Retrieves the size for a given report ID.

        Args:
            report_id: The ID of the report.
            raise_if_not_found: If True, raises a KeyError if the report ID is not found.
        Returns:
            The size of the report, or None if not found and raise_if_not_found is False.
        """
        report_type = report_type or "input"
        ReportLayout.raise_if_not_group_type(report_type)


        report_id = self.resolve_report_id(report_id)
        layout = self.reports.get(report_id)
        if layout is None:
            if raise_if_not_found:
                raise KeyError(f"Report ID {report_id} not found in layout.")
            return None
        group = layout.get_group(report_type)
        return group.size_bytes
    
    def __len__(self) -> int:
        return len(self.fields)
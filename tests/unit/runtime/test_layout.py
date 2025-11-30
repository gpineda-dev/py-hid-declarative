import pytest
from hid_declarative.runtime.layout import DescriptorLayout, FieldOp, ReportLayout

def test_descriptor_layout_init():
    """Test initialization of DescriptorLayout."""
    layout = DescriptorLayout()
    assert layout.reports == {}
    assert len(layout) == 0
    assert layout.list_report_ids() == []

def test_add_field_single_report():
    """Test adding a field to a specific report ID."""
    layout = DescriptorLayout()
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, name="F1", report_type="input")
    
    # Add to report ID 0 explicitly
    layout.add_field(f1, report_id=0)
    
    assert 0 in layout.reports
    assert len(layout.reports[0].input.fields) == 1
    assert layout.reports[0].input.fields[0] == f1
    # Ensure field's report_id was updated
    assert f1.report_id == 0

def test_add_field_multiple_reports():
    """Test adding fields to different report IDs."""
    layout = DescriptorLayout()
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, name="F1", report_type="input")
    f2 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=2, name="F2", report_type="output")
    
    layout.add_field(f1, report_id=1)
    layout.add_field(f2, report_id=2)
    
    assert 1 in layout.reports
    assert 2 in layout.reports
    assert len(layout.reports[1].input.fields) == 1
    assert len(layout.reports[2].output.fields) == 1

def test_resolve_report_id():
    """Test logic for resolving ambiguous or implicit report IDs."""
    layout = DescriptorLayout()
    
    # Case: No reports, defaults to 0
    assert layout.resolve_report_id() == 0
    
    # Case: Single report ID 5
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, report_type="input")
    layout.add_field(f1, report_id=5)
    assert layout.resolve_report_id() == 5
    assert layout.resolve_report_id(5) == 5
    
    # Case: Multiple reports
    f2 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=2, report_type="input")
    layout.add_field(f2, report_id=6)
    
    # Ambiguous if not specified
    with pytest.raises(ValueError, match="Ambiguous"):
        layout.resolve_report_id()
        
    # Specific ID works
    assert layout.resolve_report_id(6) == 6
    
    # Non-existent ID
    with pytest.raises(KeyError):
        layout.resolve_report_id(99)

def test_get_report_layout():
    """Test retrieving a ReportLayout object."""
    layout = DescriptorLayout()
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, report_type="input")
    layout.add_field(f1, report_id=1)
    
    assert layout.get_report_layout(1) is not None
    assert layout.get_report_layout(2) is None
    
    with pytest.raises(KeyError):
        layout.get_report_layout(2, raise_if_not_found=True)

def test_get_report_layout_group():
    """Test retrieving a specific group (input/output/feature) from a layout."""
    layout = DescriptorLayout()
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, report_type="feature")
    layout.add_field(f1, report_id=1)

    group = layout.get_report_layout_group(1, "feature")
    assert group is not None
    assert len(group.fields) == 1
    
    # Wrong type
    group_input = layout.get_report_layout_group(1, "input")
    assert len(group_input.fields) == 0

    # Missing ID
    assert layout.get_report_layout_group(99, "input") is None

def test_get_size():
    """Test size calculation for reports."""
    layout = DescriptorLayout()
    # 8 bits -> 1 byte
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, report_type="input")
    layout.add_field(f1, report_id=1)
    
    assert layout.get_size(report_id=1, report_type="input") == 1
    
    # Add another field: 8 bits at offset 8 -> total 2 bytes
    f2 = FieldOp(bit_offset=8, bit_size=8, usage_page=1, usage_id=2, report_type="input")
    layout.add_field(f2, report_id=1)
    
    assert layout.get_size(report_id=1, report_type="input") == 2
    
    # Check output report size (empty)
    assert layout.get_size(report_id=1, report_type="output") == 0

def test_has_multiple_report_ids():
    """Test detection of multiple or non-zero report IDs."""
    layout = DescriptorLayout()
    assert layout.has_multiple_report_ids() is False
    
    # Single ID 0 -> False (Standard single report)
    f1 = FieldOp(bit_offset=0, bit_size=1, usage_page=1, usage_id=1, report_type="input")
    layout.add_field(f1, report_id=0)
    assert layout.has_multiple_report_ids() is False
    
    # Single ID != 0 -> True (Numbered report)
    layout = DescriptorLayout()
    layout.add_field(f1, report_id=1)
    assert layout.has_multiple_report_ids() is True
    
    # Multiple IDs -> True
    layout.add_field(f1, report_id=2)
    assert layout.has_multiple_report_ids() is True

def test_from_fields():
    """Test creating a layout from a list of fields."""
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, report_type="input", report_id=1)
    f2 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=2, report_type="output", report_id=1)
    f3 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=3, report_type="input", report_id=2)
    
    layout = DescriptorLayout.from_fields([f1, f2, f3])
    
    assert len(layout.reports) == 2
    assert 1 in layout.reports
    assert 2 in layout.reports
    
    assert len(layout.reports[1].input.fields) == 1
    assert len(layout.reports[1].output.fields) == 1
    assert len(layout.reports[2].input.fields) == 1

def test_get_fields():
    """Test retrieving fields with filtering."""
    layout = DescriptorLayout()
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, report_type="input")
    layout.add_field(f1, report_id=1)
    
    fields = layout.get_fields(report_id=1, report_type="input")
    assert len(fields) == 1
    assert fields[0] == f1
    
    # Wrong type
    fields_out = layout.get_fields(report_id=1, report_type="output")
    assert len(fields_out) == 0
    
    # Wrong ID
    assert layout.get_fields(report_id=99) is None
    with pytest.raises(KeyError):
        layout.get_fields(report_id=99, raise_if_not_found=True)

def test_to_dict():
    """Test dictionary serialization."""
    layout = DescriptorLayout()
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, name="test", report_type="input")
    layout.add_field(f1, report_id=1)
    
    d = layout.to_dict()
    assert "reports" in d
    assert 1 in d["reports"]
    assert d["reports"][1]["report_id"] == 1
    assert len(d["reports"][1]["input"]["fields"]) == 1
    assert d["reports"][1]["input"]["fields"][0]["name"] == "test"

def test_get_flatted_fields():
    """Test retrieving all fields across all reports."""
    layout = DescriptorLayout()
    f1 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=1, report_type="input")
    f2 = FieldOp(bit_offset=0, bit_size=8, usage_page=1, usage_id=2, report_type="output")
    
    layout.add_field(f1, report_id=1)
    layout.add_field(f2, report_id=2)
    
    flat = layout.get_flatted_fields()
    assert len(flat) == 2
    assert f1 in flat
    assert f2 in flat
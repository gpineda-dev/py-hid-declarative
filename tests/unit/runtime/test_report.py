import pytest
from unittest.mock import MagicMock, Mock, patch
from hid_declarative.runtime.reports import DataBaseReport, DataInputReport, DataOutputReport, DataFeatureReport
from hid_declarative.runtime.layout import ReportLayout, ReportLayoutGroup
from hid_declarative.runtime.codec import HIDCodec

@pytest.fixture
def mock_layout_group():
    DEFAULT_DICT = {"field1": 0, "field2": 10}
    group = MagicMock(spec=ReportLayoutGroup)
    group.report_type = "input"
    group.report_id = 1

    # ensure get_default_values returns a fresh copy each time
    group.get_default_values.side_effect = lambda: DEFAULT_DICT.copy()
    
    # Mock iteration over fields for delta calculation
    field1 = Mock()
    field1.name = "field1"
    field2 = Mock()
    field2.name = "field2"
    group.__iter__.return_value = iter([field1, field2])
    
    return group

@pytest.fixture
def mock_codec():
    return MagicMock(spec=HIDCodec)

def test_init_base_report(mock_layout_group):
    """Test initialization of the base report class."""
    # DataBaseReport checks ReportLayout.list_group_types() if TYPE is None
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input", "output"]):
        report = DataBaseReport(mock_layout_group)
        assert report.layout == mock_layout_group
        assert report.report_type == "input"
        assert report.report_id == 1
        assert report["field1"] == 0

def test_init_with_initial_data(mock_layout_group):
    """Test initialization with override data."""
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input"]):
        report = DataBaseReport(mock_layout_group, initial_data={"field1": 99})
        assert report["field1"] == 99
        assert report["field2"] == 10  # Default value preserved

def test_init_subclass_type_check_pass(mock_layout_group):
    """Test that subclasses validate the report type correctly."""
    mock_layout_group.report_type = "input"
    report = DataInputReport(mock_layout_group)
    assert report.report_type == "input"

def test_init_subclass_type_check_fail(mock_layout_group):
    """Test that subclasses raise AssertionError if report type mismatches."""
    mock_layout_group.report_type = "output"
    with pytest.raises(AssertionError, match="does not match class TYPE"):
        DataInputReport(mock_layout_group)

def test_getitem_setitem(mock_layout_group):
    """Test dictionary-like access."""
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input"]):
        report = DataBaseReport(mock_layout_group)
        
        # Set valid field
        report["field1"] = 55
        assert report["field1"] == 55
        
        # Set invalid field
        with pytest.raises(KeyError, match="Field 'unknown' not found"):
            report["unknown"] = 1

        # Get invalid field (standard dict behavior from _values)
        with pytest.raises(KeyError):
            _ = report["unknown"]

def test_validate(mock_layout_group):
    """Test validation delegation."""
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input"]):
        report = DataBaseReport(mock_layout_group)
        report.validate()
        mock_layout_group.validate.assert_called_once_with({"field1": 0, "field2": 10})

def test_encode(mock_layout_group, mock_codec):
    """Test encoding delegation."""
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input"]):
        report = DataBaseReport(mock_layout_group)
        report["field1"] = 123
        
        mock_codec.encode.return_value = b'\xCA\xFE'
        
        result = report.encode(mock_codec)
        
        assert result == b'\xCA\xFE'
        mock_layout_group.validate.assert_called()
        mock_codec.encode.assert_called_once_with(
            data={"field1": 123, "field2": 10},
            report_id=1,
            report_type="input"
        )

def test_delta_calculation(mock_layout_group):
    """Test delta calculation between two reports."""
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input"]):
        r1 = DataBaseReport(mock_layout_group, initial_data={"field1": 10, "field2": 20})
        r2 = DataBaseReport(mock_layout_group, initial_data={"field1": 15, "field2": 20})
        
        # Delta is r2 - r1
        delta = r1.delta(r2)
        
        # field1 changed by +5, field2 changed by 0 (should be omitted)
        assert delta == {"field1": 5}

def test_delta_mismatch_errors(mock_layout_group):
    """Test delta raises errors for incompatible reports."""
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input", "output"]):
        r1 = DataBaseReport(mock_layout_group)
        
        # Mismatch ID
        group2 = MagicMock(spec=ReportLayoutGroup)
        group2.report_type = "input"
        group2.report_id = 999
        group2.get_default_values.return_value = {}
        r2 = DataBaseReport(group2)
        
        with pytest.raises(ValueError, match="Report IDs do not match"):
            r1.delta(r2)
            
        # Mismatch Type
        group3 = MagicMock(spec=ReportLayoutGroup)
        group3.report_type = "output"
        group3.report_id = 1
        group3.get_default_values.return_value = {}
        r3 = DataBaseReport(group3)
        
        with pytest.raises(ValueError, match="Report types do not match"):
            r1.delta(r3)

def test_copy(mock_layout_group):
    """Test creating a copy of the report."""
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input"]):
        r1 = DataBaseReport(mock_layout_group, initial_data={"field1": 42})
        r2 = r1.copy()
        
        assert r2 is not r1
        assert id(r2._values) != id(r1._values)
        assert r2.layout is r1.layout
        assert r2["field1"] == 42
        
        # Ensure deep(ish) copy of values
        r2["field1"] = 100
        assert r1["field1"] == 42

def test_from_layout_factory(mock_layout_group):
    """Test the from_layout factory method."""
    layout = MagicMock(spec=ReportLayout)
    layout.get_group.return_value = mock_layout_group
    mock_layout_group.report_type = "input"
    
    # Mock the class method call on ReportLayout
    with patch("hid_declarative.runtime.reports.ReportLayout.raise_if_not_group_type") as mock_check:
        report = DataInputReport.from_layout(layout, "input")
        
        assert isinstance(report, DataInputReport)
        assert report.layout == mock_layout_group
        mock_check.assert_called_with("input")
        layout.get_group.assert_called_with("input")

def test_from_layout_group_factory(mock_layout_group):
    """Test the from_layout_group factory method."""
    mock_layout_group.report_type = "feature"
    report = DataFeatureReport.from_layout_group(mock_layout_group)
    assert isinstance(report, DataFeatureReport)
    assert report.layout == mock_layout_group

def test_to_dict(mock_layout_group):
    """Test conversion to dictionary."""
    with patch("hid_declarative.runtime.reports.ReportLayout.list_group_types", return_value=["input"]):
        report = DataBaseReport(mock_layout_group)
        d = report.to_dict()
        assert isinstance(d, dict)
        assert d == {"field1": 0, "field2": 10}
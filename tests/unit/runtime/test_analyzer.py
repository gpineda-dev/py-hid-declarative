import pytest
from hid_declarative.spec.descriptor import ReportDescriptor
from hid_declarative.spec.enums import CollectionType
from hid_declarative.spec.items import (
    CollectionItem, ReportIDItem, UsageMaxItem, UsageMinItem, UsagePageItem, UsageItem, ReportSizeItem, ReportCountItem, 
    LogicalMinItem, LogicalMaxItem, InputItem
)
from hid_declarative.runtime.analyzer import DescriptorAnalyzer, ScanState
from hid_declarative.spec.tables.button import ButtonPage
from hid_declarative.spec.tables.generic_desktop import GenericDesktop

from hid_declarative.spec.items import (
    PushItem, PopItem, OutputItem, FeatureItem
)

def test_analyze_simple_sequence():
    items = [
        UsagePageItem(0x01),        # Generic Desktop
        ReportSizeItem(8),
        ReportCountItem(2),
        LogicalMinItem(-127),
        LogicalMaxItem(127),
        UsageItem(0x30),            # X
        UsageItem(0x31),            # Y
        InputItem(0x02)             # Data/Variable/Absolute
    ]
    descriptor = ReportDescriptor(items)

    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)

    assert len(layout.fields) == 2

    # First field (X)
    op_x = layout.fields[0]
    assert op_x.bit_offset == 0
    assert op_x.bit_size == 8
    assert op_x.usage_id == 0x30
    assert op_x.is_signed is True

    # Second field (Y)
    op_y = layout.fields[1]
    assert op_y.bit_offset == 8
    assert op_y.bit_size == 8
    assert op_y.usage_id == 0x31

def test_analyzer_consumes_usages_on_collection_start():
    items = [
        UsagePageItem(GenericDesktop.PAGE_ID),
        UsageItem(GenericDesktop.MOUSE),            
        CollectionItem(CollectionType.APPLICATION), 
            UsagePageItem(ButtonPage.PAGE_ID),
            UsageItem(1),                           
            ReportSizeItem(1),
            ReportCountItem(1),
            InputItem(0)
    ]
    descriptor = ReportDescriptor(items)

    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)

    assert len(layout.fields) == 1

    op = layout.fields[0]
    assert op.usage_page == ButtonPage.PAGE_ID
    assert op.usage_id == 1
    assert op.bit_size == 1

def test_analyzer_usage_range():
    items = [
        UsagePageItem(ButtonPage.PAGE_ID),
        UsageMinItem(1),
        UsageMaxItem(3),
        ReportSizeItem(1),
        ReportCountItem(3),
        InputItem(0)
    ]
    descriptor = ReportDescriptor(items)
    
    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)

    assert len(layout.fields) == 3

    for i, op in enumerate(layout.fields, start=1):
        assert op.usage_page == ButtonPage.PAGE_ID
        assert op.usage_id == i
        assert op.bit_size == 1


def test_scan_state_push_pop_logic():
    state = ScanState()

    state.usage_page = 0x01
    state.logical_min = -127
    state.report_size = 8

    state.push()

    state.usage_page = 0x09
    state.logical_min = 1
    state.report_size = 1

    assert state.usage_page == 0x09
    assert state.logical_min == 1

    state.pop()

    assert state.usage_page == 0x01
    assert state.logical_min == -127
    assert state.report_size == 8

def test_scan_state_pop_empty_safety():
    state = ScanState()

    # Popping without a prior push should not raise an error
    try:
        state.pop()
    except IndexError:
        pytest.fail("Pop on empty stack raised IndexError")


def test_analyze_report_ids_reset_cursor():
    """Test that switching Report IDs resets the bit cursor for that report."""
    items = [
        UsagePageItem(GenericDesktop.PAGE_ID),
        ReportSizeItem(8),
        ReportCountItem(1),
        
        # Report 1
        ReportIDItem(1),
        UsageItem(0x30), # X
        InputItem(0x02), # Variable
        
        # Report 2
        ReportIDItem(2),
        UsageItem(0x31), # Y
        InputItem(0x02), # Variable
    ]
    descriptor = ReportDescriptor(items)
    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)
    
    assert len(layout.fields) == 2
    
    op1 = layout.fields[0]
    op2 = layout.fields[1]
    
    # Both should start at offset 0 because they belong to different reports
    assert op1.bit_offset == 0
    assert op1.usage_id == 0x30
    
    assert op2.bit_offset == 0
    assert op2.usage_id == 0x31

def test_analyze_push_pop_items():
    """Test PUSH and POP items restore global state correctly."""
    items = [
        UsagePageItem(GenericDesktop.PAGE_ID), # 0x01
        PushItem(),
        
        UsagePageItem(ButtonPage.PAGE_ID),     # 0x09
        UsageItem(1),
        ReportSizeItem(1),
        ReportCountItem(1),
        InputItem(0x02),
        
        PopItem(),
        # Should be back to Generic Desktop (0x01)
        UsageItem(0x30), # X
        InputItem(0x02)
    ]
    descriptor = ReportDescriptor(items)
    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)
    
    assert len(layout.fields) == 2
    
    btn_op = layout.fields[0]
    assert btn_op.usage_page == ButtonPage.PAGE_ID
    
    desktop_op = layout.fields[1]
    assert desktop_op.usage_page == GenericDesktop.PAGE_ID

def test_analyze_name_collision_handling():
    """Test that duplicate names get suffixed with _2, _3, etc."""
    items = [
        UsagePageItem(GenericDesktop.PAGE_ID),
        ReportSizeItem(8),
        ReportCountItem(1),
        
        UsageItem(0x30), # X
        InputItem(0x02),
        
        UsageItem(0x30), # X again
        InputItem(0x02),
        
        UsageItem(0x30), # X again
        InputItem(0x02),
    ]
    descriptor = ReportDescriptor(items)
    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)
    
    assert len(layout.fields) == 3
    assert layout.fields[0].name == "X"
    assert layout.fields[1].name == "X_2"
    assert layout.fields[2].name == "X_3"

def test_analyze_report_types():
    """Test Input, Output, and Feature items are categorized correctly."""
    items = [
        UsagePageItem(GenericDesktop.PAGE_ID),
        ReportSizeItem(8),
        ReportCountItem(1),
        
        UsageItem(0x30),
        InputItem(0x02),
        
        UsageItem(0x31),
        OutputItem(0x02),
        
        UsageItem(0x32),
        FeatureItem(0x02),
    ]
    descriptor = ReportDescriptor(items)
    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)
    
    assert len(layout.fields) == 3
    assert layout.fields[0].report_type == "input"
    assert layout.fields[1].report_type == "output"
    assert layout.fields[2].report_type == "feature"

def test_analyze_array_naming():
    """Test that Array items (Variable flag = 0) get 'Idx' suffix."""
    items = [
        UsagePageItem(GenericDesktop.PAGE_ID),
        ReportSizeItem(8),
        ReportCountItem(1),
        
        UsageItem(0x30),
        InputItem(0x00), # Data, Array, Absolute
    ]
    descriptor = ReportDescriptor(items)
    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)
    
    op = layout.fields[0]
    # Expecting "Generic Desktop Idx" or similar based on page name
    assert "Idx" in op.name

def test_analyze_usage_repetition():
    """Test that the last usage is repeated if ReportCount > len(Usages)."""
    items = [
        UsagePageItem(ButtonPage.PAGE_ID),
        ReportSizeItem(1),
        ReportCountItem(3),
        
        UsageItem(1), # Button 1
        InputItem(0x02)
    ]
    descriptor = ReportDescriptor(items)
    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(descriptor)
    
    assert len(layout.fields) == 3
    assert layout.fields[0].usage_id == 1
    assert layout.fields[1].usage_id == 1
    assert layout.fields[2].usage_id == 1
from typing import List
import pytest
from hid_declarative.spec.items import (
    UsagePageItem, LogicalMinItem, LogicalMaxItem, InputItem, OutputItem,
    FeatureItem, CollectionItem, EndCollectionItem, ReportSizeItem,
    ReportCountItem, ReportIDItem, UsageItem, UsageMinItem, UsageMaxItem,
    PhysicalMinItem, PhysicalMaxItem, UnitExponentItem, UnitItem, PushItem, PopItem, SpecItem
)

def test_usage_page_serialization():
    # Generic Desktop (0x01) -> Tag 0x04 | Size 1 -> 0x05
    item = UsagePageItem(0x01)
    assert item.to_bytes() == b'\x05\x01'

def test_logical_min_negative_one_byte():
    # -127 -> Tag 0x14 | Size 1 -> 0x15
    # -127 in 1 byte signed is 0x81
    item = LogicalMinItem(-127)
    assert item.to_bytes() == b'\x15\x81'
    
def test_logical_max_positive_one_byte():
    # 127 -> Tag 0x24 | Size 1 -> 0x25
    item = LogicalMaxItem(127)
    assert item.to_bytes() == b'\x25\x7f'

def test_logical_min_two_bytes():
    # -200 -> Tag 0x14 | Size 2 -> 0x16
    item = LogicalMinItem(-200)
    assert item.to_bytes() == b'\x16\x38\xff'

def test_logical_max_two_bytes():
    # 1000 -> Tag 0x24 | Size 2 -> 0x26
    item = LogicalMaxItem(1000)
    assert item.to_bytes() == b'\x26\xe8\x03'

def test_logical_min_four_bytes():
    # -100000 -> Tag 0x14 | Size 3 (4 bytes) -> 0x17
    item = LogicalMinItem(-100000)
    assert item.to_bytes() == b'\x17\x60\x79\xfe\xff'

def test_input_item():
    # Data/Variable/Absolute (0x02) -> Tag 0x80 | Size 1 -> 0x81
    item = InputItem(0x02)
    assert item.to_bytes() == b'\x81\x02'

def test_output_item():
    # Data/Variable/Absolute (0x02) -> Tag 0x90 | Size 1 -> 0x91
    item = OutputItem(0x02)
    assert item.to_bytes() == b'\x91\x02'

def test_feature_item():
    # Data/Variable/Absolute (0x02) -> Tag 0xB0 | Size 1 -> 0xB1
    item = FeatureItem(0x02)
    assert item.to_bytes() == b'\xb1\x02'

def test_collection_item():
    # Application (0x01) -> Tag 0xA0 | Size 1 -> 0xA1
    item = CollectionItem(0x01)
    assert item.to_bytes() == b'\xa1\x01'

def test_end_collection_item():
    # Fixed byte 0xC0
    item = EndCollectionItem()
    assert item.to_bytes() == b'\xc0'

def test_report_size_item():
    # 8 bits -> Tag 0x74 | Size 1 -> 0x75
    item = ReportSizeItem(8)
    assert item.to_bytes() == b'\x75\x08'

def test_report_count_item():
    # 3 reports -> Tag 0x94 | Size 1 -> 0x95
    item = ReportCountItem(3)
    assert item.to_bytes() == b'\x95\x03'

def test_report_id_item():
    # Report ID 1 -> Tag 0x84 | Size 1 -> 0x85
    item = ReportIDItem(1)
    assert item.to_bytes() == b'\x85\x01'

def test_usage_item():
    # X axis (0x30) -> Tag 0x08 | Size 1 -> 0x09
    item = UsageItem(0x30)
    assert item.to_bytes() == b'\x09\x30'

def test_usage_min_item():
    # Usage min 1 -> Tag 0x18 | Size 1 -> 0x19
    item = UsageMinItem(1)
    assert item.to_bytes() == b'\x19\x01'

def test_usage_max_item():
    # Usage max 5 -> Tag 0x28 | Size 1 -> 0x29
    item = UsageMaxItem(5)
    assert item.to_bytes() == b'\x29\x05'

def test_physical_min_item():
    # Physical min 0 -> Tag 0x34 | Size 1 -> 0x35
    item = PhysicalMinItem(0)
    assert item.to_bytes() == b'\x35\x00'

def test_physical_max_item():
    # Physical max 255 -> Tag 0x44 | Size 2 -> 0x46
    item = PhysicalMaxItem(255)
    assert item.to_bytes() == b'\x46\xff\x00'

def test_unit_exponent_item():
    # Exponent 0 -> Tag 0x54 | Size 1 -> 0x55
    item = UnitExponentItem(0)
    assert item.to_bytes() == b'\x55\x00'

def test_unit_item():
    # None (0x00) -> Tag 0x64 | Size 1 -> 0x65
    item = UnitItem(0)
    assert item.to_bytes() == b'\x65\x00'

# Test items with tables
from hid_declarative.spec.tables.generic_desktop import GenericDesktop
from hid_declarative.spec.tables.button import ButtonPage

def test_generic_desktop_usage_item():
    # Create a UsageItem for the X axis
    item = UsageItem(GenericDesktop.X)
    assert item.to_bytes() == b'\x09\x30'

def test_button_page_usage_item():
    # Create a UsageItem for Button 1
    item = UsageItem(ButtonPage.BUTTON_1)
    assert item.to_bytes() == b'\x09\x01'

def test_button_page_make_button_usage():
    usage_id = ButtonPage.make_button_usage(5)
    assert usage_id == ButtonPage.BUTTON_5

def test_button_page_get_button_number():
    button_number = ButtonPage.get_button_number(ButtonPage.BUTTON_10)
    assert button_number == 10

def test_button_page_make_button_usage_invalid():
    with pytest.raises(ValueError):
        ButtonPage.make_button_usage(0)  # Invalid button number
    with pytest.raises(ValueError):
        ButtonPage.make_button_usage(33)  # Invalid button number

def test_button_page_get_button_number_invalid():
    with pytest.raises(ValueError):
        ButtonPage.get_button_number(0x00)  # Invalid usage ID
    with pytest.raises(ValueError):
        ButtonPage.get_button_number(0x21)  # Invalid usage ID

from hid_declarative.spec.enums import CollectionType

def test_collection_nesting_simulation():
    # Simulate a nested collection structure
    items: List[SpecItem] = [
        CollectionItem(CollectionType.APPLICATION),                  
            UsageItem(GenericDesktop.POINTER),
            CollectionItem(CollectionType.PHYSICAL),               
                UsageItem(GenericDesktop.X),
                UsageItem(GenericDesktop.Y),
            EndCollectionItem(),   
        EndCollectionItem()    
    ]
    
    expected_bytes = b''.join(item.to_bytes() for item in items)
    actual_bytes = (
        b'\xa1\x01' +      # Collection (Application)
        b'\x09\x01' +      # Usage (Pointer)
        b'\xa1\x00' +      # Collection (Physical)
        b'\x09\x30' +      # Usage (X)
        b'\x09\x31' +      # Usage (Y)
        b'\xc0' +          # End Collection (Physical)
        b'\xc0'            # End Collection (Application)
    )
    
    assert expected_bytes == actual_bytes
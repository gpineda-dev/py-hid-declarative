import pytest
from hid_declarative.exceptions import HIDProtocolError
from hid_declarative.parser import HIDParser
from hid_declarative.spec.items import (
    UsagePageItem, UsageItem, CollectionItem, 
    InputItem, EndCollectionItem, LogicalMinItem
)
from hid_declarative.spec.enums import CollectionType
from hid_declarative.spec.tables.generic_desktop import GenericDesktop
from hid_declarative.spec.items import ITEM_REGISTRY, SpecItem

def test_parse_simple_mouse_fragment():
    blob = b'\x05\x01\x09\x02\xa1\x01\x15\x81'

    parser = HIDParser()
    items = parser.parse(blob)

    assert len(items) == 4

    assert isinstance(items[0], UsagePageItem)
    assert items[0].data == GenericDesktop.PAGE_ID

    assert isinstance(items[1], UsageItem)
    assert items[1].data == GenericDesktop.MOUSE

    assert isinstance(items[2], CollectionItem)
    assert items[2].data == CollectionType.APPLICATION

    assert isinstance(items[3], LogicalMinItem)
    assert items[3].data == -127

def test_parse_incomplete_blob_raises_error():
    blob = b'\x06\x01' 
    
    parser = HIDParser()
    with pytest.raises(HIDProtocolError, match="Insufficient data for item payload."):
        parser.parse(blob)

def test_parse_long_item_raises_error():
    # Tag 0xFE indicates a Long Item (1111 1110)
    blob = b'\xFE\x00'
    
    parser = HIDParser()
    with pytest.raises(HIDProtocolError, match="Long Items are not supported yet."):
        parser.parse(blob)

def test_parse_unknown_item_fallback():
    # Use a tag that likely isn't in ITEM_REGISTRY but is valid short item format.
    # Tag: 0xF0 (1111 0000), Size: 1 (01) -> Header: 0xF1
    blob = b'\xF1\x55'
    
    parser = HIDParser()
    items = parser.parse(blob)
    
    assert len(items) == 1
    # Should fallback to generic SpecItem
    assert type(items[0]).__name__ == 'SpecItem'
    assert items[0].tag == 0xF0
    assert items[0].data == 0x55

def test_parse_signed_integers():
    # Test parsing of signed values for 1, 2, and 4 bytes
    # 1 byte: 0x15 (Logical Min), size 1 -> -1 (0xFF)
    # 2 bytes: 0x16 (Logical Min), size 2 -> -1 (0xFFFF)
    # 4 bytes: 0x17 (Logical Min), size 3(4) -> -1 (0xFFFFFFFF)
    
    # Note: Logical Min tag is 0001 01xx -> 0x14 base
    # Size 1: 0x15, Data: 0xFF
    # Size 2: 0x16, Data: 0xFF 0xFF
    # Size 4: 0x17, Data: 0xFF 0xFF 0xFF 0xFF
    
    blob = b'\x15\xFF\x16\xFF\xFF\x17\xFF\xFF\xFF\xFF'
    
    parser = HIDParser()
    items = parser.parse(blob)
    
    assert len(items) == 3
    assert items[0].data == -1
    assert items[1].data == -1
    assert items[2].data == -1

def test_parse_unsigned_integers():
    # Usage (0x08) is defined as unsigned in the parser logic.
    # Header 0x09: Tag 0x08 (Usage), Size 1. Data 0xFF.
    # If signed: -1. If unsigned: 255.
    
    # Header 0x0A: Tag 0x08 (Usage), Size 2. Data 0xFFFF.
    # If signed: -1. If unsigned: 65535.
    
    blob = b'\x09\xFF\x0A\xFF\xFF'
    
    parser = HIDParser()
    items = parser.parse(blob)
    
    assert len(items) == 2
    assert isinstance(items[0], UsageItem)
    assert items[0].data == 255
    
    assert isinstance(items[1], UsageItem)
    assert items[1].data == 65535

def test_parse_zero_size_item():
    # End Collection: Tag 0xC0 (1100 00xx), Size 0 (00) -> Header 0xC0
    blob = b'\xC0'
    
    parser = HIDParser()
    items = parser.parse(blob)
    
    assert len(items) == 1
    assert isinstance(items[0], EndCollectionItem)
    assert items[0].data is None

def test_parse_from_file(tmp_path):
    # Create a temporary binary file
    blob = b'\x05\x01' # Usage Page (Generic Desktop)
    descriptor_file = tmp_path / "test_descriptor.bin"
    descriptor_file.write_bytes(blob)
    
    parser = HIDParser()
    items = parser.parse_from_file(descriptor_file)
    
    assert len(items) == 1
    assert isinstance(items[0], UsagePageItem)
    assert items[0].data == GenericDesktop.PAGE_ID

def test_parse_validation_error(monkeypatch):
    # Import here to avoid modifying top-level imports of the existing file
    
    # Define a mock item that fails validation
    class BrokenItem(SpecItem):
        def validate(self):
            raise ValueError("Validation failed intentionally")

    # Use a custom tag 0xF4 (1111 0100) -> Header 0xF4 (size 0)
    # We must ensure the parser sees this mapping in the global registry
    tag = 0xF4
    monkeypatch.setitem(ITEM_REGISTRY, tag, BrokenItem)
    
    blob = b'\xF4'
    parser = HIDParser()
    
    with pytest.raises(HIDProtocolError, match="Error instantiating item BrokenItem: Validation failed intentionally"):
        parser.parse(blob)
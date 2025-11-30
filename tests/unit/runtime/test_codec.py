import pytest
from hid_declarative.runtime.codec import HIDCodec
from hid_declarative.runtime.layout import FieldOp, DescriptorLayout, ReportLayout

@pytest.fixture
def simple_layout():
    return DescriptorLayout.from_fields([
        FieldOp(bit_offset=0, bit_size=1, usage_page=9, usage_id=1, name="Btn1", is_signed=False, report_id=0),
        FieldOp(bit_offset=1, bit_size=1, usage_page=9, usage_id=2, name="Btn2", is_signed=False, report_id=0),
        FieldOp(bit_offset=2, bit_size=6, usage_page=9, usage_id=0, name="Pad", is_signed=False, report_id=0),
        FieldOp(bit_offset=8, bit_size=8, usage_page=1, usage_id=48, name="X", is_signed=True, logical_min=-127, logical_max=127, report_id=0)
    ])

def test_decode_buttons(simple_layout):
    data = b'\x03\x00'

    codec = HIDCodec(simple_layout)

    decoded = codec.decode(data)
    print(decoded)
    assert decoded["Btn1"] is True
    assert decoded["Btn2"] is True
    assert "Pad" not in decoded  # Padding field should be skipped
    assert decoded["X"] == 0

def test_encode_buttons(simple_layout):
    codec = HIDCodec(simple_layout)
    
    # Test encoding buttons and signed value
    values = {
        "Btn1": True,
        "Btn2": True,
        "X": -10
    }
    
    encoded = codec.encode(values, validate=False)
    
    # Expected:
    # Byte 0: Btn1 (bit 0) = 1, Btn2 (bit 1) = 1, Pad (bits 2-7) = 0 -> 0x03
    # Byte 1: X (bits 8-15) = -10 (signed 8-bit) -> 0xF6
    assert encoded == b'\x03\xf6'

def test_encode_partial_values(simple_layout):
    codec = HIDCodec(simple_layout)
    
    # Test encoding with missing values (should default to 0 in the output bytes)
    values = {
        "Btn1": True,
        # Btn2 missing
        # X missing
    }
    
    encoded = codec.encode(values, validate=False)
    
    # Expected:
    # Byte 0: Btn1=1, Btn2=0 (default), Pad=0 -> 0x01
    # Byte 1: X=0 (default) -> 0x00
    assert encoded == b'\x01\x00'

def test_encode_overflow_masking(simple_layout):
    codec = HIDCodec(simple_layout)
    
    # Test that values larger than bit_size are masked
    values = {
        "Btn1": 1, # 0b11, but bit_size is 1, so should be masked to 1
        "X": 0     
    }
    
    encoded = codec.encode(values, validate=False)
    
    # Expected:
    # Byte 0: Btn1 = 3 & 1 = 1 -> 0x01
    # Byte 1: 0x00
    assert encoded == b'\x01\x00'

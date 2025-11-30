import pytest
import struct

from hid_declarative.spec.usb import (
    USBSetupPacket, HIDDescriptor, 
    USBRequestType, StandardRequestCode, HIDRequestCode, DescriptorType
)

def test_usb_setup_packet_pack():
    """
    Verifies that USBSetupPacket correctly serializes to 8 bytes (Little Endian).
    """
    packet = USBSetupPacket(
        bmRequestType=0x81,
        bRequest=0x06,
        wValue=0x2200,
        wIndex=0x0001,
        wLength=0x00FF
    )
    data = packet.pack()
    assert len(data) == 8
    # Little endian check: 0x2200 -> \x00\x22, 0x00FF -> \xFF\x00
    expected = b'\x81\x06\x00\x22\x01\x00\xFF\x00'
    assert data == expected

def test_usb_setup_packet_from_bytes():
    """
    Verifies parsing of raw bytes into a USBSetupPacket.
    """
    # 0x21, 0x09, 0x0300 (LE), 0x0002 (LE), 0x0008 (LE)
    data = b'\x21\x09\x00\x03\x02\x00\x08\x00'
    packet = USBSetupPacket.from_bytes(data)
    
    assert packet.bmRequestType == 0x21
    assert packet.bRequest == 0x09
    assert packet.wValue == 0x0300
    assert packet.wIndex == 0x0002
    assert packet.wLength == 8

def test_usb_setup_packet_from_bytes_invalid():
    """
    Verifies that incorrect byte length raises ValueError.
    """
    with pytest.raises(ValueError):
        USBSetupPacket.from_bytes(b'\x00\x00')

def test_request_report_descriptor_helper():
    """
    Verifies the helper method for GET_DESCRIPTOR (Report) requests.
    """
    packet = USBSetupPacket.request_report_descriptor(interface_num=2, length=100)
    
    # Expected: DIR_IN (0x80) | STANDARD (0x00) | INTERFACE (0x01) = 0x81
    assert packet.bmRequestType == 0x81 
    assert packet.bRequest == StandardRequestCode.GET_DESCRIPTOR
    # Expected: (DescriptorType.REPORT (0x22) << 8) | 0x00 = 0x2200
    assert packet.wValue == 0x2200
    assert packet.wIndex == 2
    assert packet.wLength == 100

def test_set_report_helper():
    """
    Verifies the helper method for SET_REPORT requests.
    """
    # Report Type 2 (Output), Report ID 5
    packet = USBSetupPacket.set_report(interface_num=0, report_type=2, report_id=5, length=64)
    
    # Expected: DIR_OUT (0x00) | CLASS (0x20) | INTERFACE (0x01) = 0x21
    assert packet.bmRequestType == 0x21
    assert packet.bRequest == HIDRequestCode.SET_REPORT
    # Expected: (2 << 8) | 5 = 0x0205
    assert packet.wValue == 0x0205
    assert packet.wIndex == 0
    assert packet.wLength == 64

def test_hid_descriptor_pack():
    """
    Verifies that HIDDescriptor packs into the standard 9-byte structure.
    """
    desc = HIDDescriptor(wDescriptorLength=123)
    data = desc.pack()
    
    assert len(data) == 9
    
    # Unpack to verify fields according to HID Spec 1.11
    # Format: <BBHBBBH
    fields = struct.unpack('<BBHBBBH', data)
    
    assert fields[0] == 9      # bLength
    assert fields[1] == 0x21   # bDescriptorType (HID Class)
    assert fields[2] == 0x0111 # bcdHID (Default)
    assert fields[3] == 0x00   # bCountryCode
    assert fields[4] == 1      # bNumDescriptors
    assert fields[5] == 0x22   # bDescriptorType (Report)
    assert fields[6] == 123    # wDescriptorLength
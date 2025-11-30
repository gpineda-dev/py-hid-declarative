import struct
from dataclasses import dataclass
from enum import IntEnum

__doc__ = """
USB HID Specification related definitions, including USB Setup Packet,
HID Descriptor structure, and relevant enums for USB requests and descriptors.

The current library focuses on HID layer and does not implement full USB stack functionality.
These definitions are provided to facilitate interaction with USB HID devices if needed.

Usually the Kernel or OS USB stack handles USB-level communication.
"""

class USBRequestType(IntEnum):
    """USB Request Type Bitmask"""

    # Direction
    DIR_OUT = 0x00  # Host -> Device
    DIR_IN  = 0x80  # Device -> Host
    
    # Type
    TYPE_STANDARD = 0x00
    TYPE_CLASS    = 0x20 # HID Specific
    TYPE_VENDOR   = 0x40
    
    # Recipient
    RECIP_DEVICE    = 0x00
    RECIP_INTERFACE = 0x01
    RECIP_ENDPOINT  = 0x02

class HIDRequestCode(IntEnum):
    """HID Class-Specific Requests (Section 7.2)"""
    GET_REPORT   = 0x01
    GET_IDLE     = 0x02
    GET_PROTOCOL = 0x03
    SET_REPORT   = 0x09
    SET_IDLE     = 0x0A
    SET_PROTOCOL = 0x0B

class StandardRequestCode(IntEnum):
    """USB Standard Requests (USB 2.0 Spec)"""
    GET_DESCRIPTOR = 0x06
    SET_DESCRIPTOR = 0x07

class DescriptorType(IntEnum):
    """USB Descriptor Types"""
    DEVICE        = 0x01
    CONFIGURATION = 0x02
    STRING        = 0x03
    INTERFACE     = 0x04
    ENDPOINT      = 0x05
    HID           = 0x21
    REPORT        = 0x22
    PHYSICAL      = 0x23

@dataclass
class USBSetupPacket:
    """
    Represents the 8 bytes of a USB control request.
    struct usb_ctrlrequest {
        __u8 bRequestType;
        __u8 bRequest;
        __u16 wValue;
        __u16 wIndex;
        __u16 wLength;
    }
    """
    bmRequestType: int
    bRequest: int
    wValue: int
    wIndex: int
    wLength: int

    def pack(self) -> bytes:
        """Serializes to binary (Little Endian)."""
        return struct.pack('<BBHHH', 
            self.bmRequestType,
            self.bRequest,
            self.wValue,
            self.wIndex,
            self.wLength
        )

    @classmethod
    def request_report_descriptor(cls, interface_num: int, length: int = 4096) -> 'USBSetupPacket':
        """Helper: Creates the standard request to retrieve the HID descriptor."""
        return cls(
            bmRequestType=USBRequestType.DIR_IN | USBRequestType.TYPE_STANDARD | USBRequestType.RECIP_INTERFACE, # 0x81
            bRequest=StandardRequestCode.GET_DESCRIPTOR, # 0x06
            wValue=(DescriptorType.REPORT << 8) | 0x00,  # Type (High) + Index (Low) -> 0x2200
            wIndex=interface_num,
            wLength=length
        )

    @classmethod
    def set_report(cls, interface_num: int, report_type: int, report_id: int, length: int) -> 'USBSetupPacket':
        """Helper: Creates the request to send an Output/Feature Report via Control Endpoint."""
        # wValue = (Report Type High) | (Report ID Low)
        # Type: 1=Input, 2=Output, 3=Feature
        return cls(
            bmRequestType=USBRequestType.DIR_OUT | USBRequestType.TYPE_CLASS | USBRequestType.RECIP_INTERFACE, # 0x21
            bRequest=HIDRequestCode.SET_REPORT, # 0x09
            wValue=(report_type << 8) | report_id,
            wIndex=interface_num,
            wLength=length
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'USBSetupPacket':
        """Parses 8 bytes into a USBSetupPacket."""
        if len(data) != 8:
            raise ValueError("USB Setup Packet must be exactly 8 bytes.")
        fields = struct.unpack('<BBHHH', data)
        return cls(*fields)
    
@dataclass
class HIDDescriptor:
    """
    The USB Header that announces the presence of the Report Descriptor.
    Ref: Device Class Definition for HID 1.11, Section 6.2.1
    """
    wDescriptorLength: int      # The size of your generated blob (Report Descriptor)
    bcdHID: int = 0x0111        # HID Version (1.11)
    bCountryCode: int = 0x00    # 0 = Not Localized
    bNumDescriptors: int = 1    # Number of associated descriptors (min 1)
    bDescriptorType: int = 0x22 # 0x22 = Report Descriptor

    def pack(self) -> bytes:
        """Generates the 9 bytes of the HID Descriptor."""
        return struct.pack('<BBHBBBH',
            9,      # bLength (Always 9 bytes)
            0x21,   # bDescriptorType (0x21 = HID Descriptor Class)
            self.bcdHID,
            self.bCountryCode,
            self.bNumDescriptors,
            self.bDescriptorType, # Type of the following descriptor (0x22 = Report)
            self.wDescriptorLength # Length of the following descriptor
        )
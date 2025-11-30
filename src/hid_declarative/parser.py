from pathlib import Path
import struct
from typing import List, Optional, Type, Union

from hid_declarative.spec.descriptor import ReportDescriptor
from hid_declarative.spec.tags import ItemTag
from .spec.items import SpecItem, ITEM_REGISTRY
from .exceptions import HIDProtocolError

class HIDParser:
    def parse(self, payload: bytes) -> ReportDescriptor:
        """
        Parses a raw HID Report Descriptor binary blob into a ReportDescriptor object.
        Args:
            payload (bytes): The raw HID Report Descriptor bytes.
        Returns:
            ReportDescriptor: The parsed report descriptor.
        Raises:
            HIDProtocolError: If the descriptor is malformed.
        """

        # Reminder of the HID Item Format:
        # +---------+----------------+------------------+
        # | Bits    | 7 6 5 4 3 2 1 0 | Description      |
        # +=========+================+==================+
        # | 7..2    | Tag            | Item Tag         |
        # | 1..0    | Size           | Data Size Code   |
        # +---------+----------------+------------------+

        report = ReportDescriptor()
        cursor = 0
        total_len = len(payload)

        while cursor < total_len:
            # 1. Read the header byte
            header = payload[cursor]
            cursor += 1

            # 2. Handle the unsupported Long Item format
            if header == 0xFE:
                raise HIDProtocolError("Long Items are not supported yet.")
            
            # 3. Decode the header
            tag_value = header & 0xFC   # Mask : 1111 1100
            size_code = header & 0x03   # Mask : 0000 0011

            
            # 4. Determine the data size
            data_size = 4 if size_code == 3 else size_code

            # Ensure we have enough bytes left
            if cursor + data_size > total_len:
                print("cursor:", cursor, "data_size:", data_size, "total_len:", total_len)
                formated_payload = None
                # if payload is a utf-8 string, print it as string, otherwise as bytes
                # Eg. if we used an upstream pipe with invalid text daa (eg. output of compile failed with printed stack trace), this will be printed as string
                if all(32 <= b <= 126 for b in payload):
                    formated_payload = payload.decode('utf-8', errors='replace')
                else:
                    formated_payload = payload
                print("formated_payload:", formated_payload)
                raise HIDProtocolError(f"Insufficient data for item payload.")
            
            # 5. Extract the data bytes
            raw_data = payload[cursor:cursor + data_size]
            cursor += data_size

            # 6. Convert data bytes to integer (Little Endian)
            parsed_value = None
            if data_size > 0:
                
                # By default : signed
                if data_size == 1: fmt = '<b'    # char
                elif data_size == 2: fmt = '<h'  # short
                elif data_size == 4: fmt = '<i'  # int
                
                # Exception for unsigned items (e.g., Usage Page)
                if tag_value in (ItemTag.USAGE_PAGE, ItemTag.USAGE,
                                 ItemTag.USAGE_MIN, ItemTag.USAGE_MAX,
                                 ItemTag.REPORT_ID, ItemTag.REPORT_SIZE, ItemTag.REPORT_COUNT):
                    if data_size == 1: fmt = '<B'    # unsigned char
                    elif data_size == 2: fmt = '<H'  # unsigned short
                    elif data_size == 4: fmt = '<I'  # unsigned int
                
                parsed_value = struct.unpack(fmt, raw_data)[0]

            # 7. Instantiate the appropriate SpecItem subclass
            item_class: Type[SpecItem] = ITEM_REGISTRY.get(tag_value)
            if item_class:
                try:
                    item = item_class(parsed_value)
                    item.validate()
                except Exception as e:
                    raise HIDProtocolError(f"Error instantiating item {item_class.__name__}: {e}")
            else:
                # Fallback to generic SpecItem if no specific class found
                # TODO: print warning about unknown item tag in logging
                item = SpecItem(tag=tag_value, data=parsed_value)
            
            report.append(item)

        return report
    

    def parse_from_file(self, path: Union[str, Path]) -> ReportDescriptor:
        """Parses a HID Report Descriptor from a binary file."""
        p = Path(path) if isinstance(path, str) else path
        raw_bytes = p.read_bytes()
        return self.parse(raw_bytes)
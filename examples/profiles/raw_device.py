import json
from typing import Dict
from hid_declarative import schema as hid_schema
from hid_declarative import spec as hid_spec
from hid_declarative.spec import tables as hid_tables
from hid_declarative import HIDProfile, HIDCompiler, ReportDescriptor, DescriptorAnalyzer, DescriptorLayout, HIDParser, HIDCodec

mouse_raw_definition = [
    hid_spec.items.UsagePageItem(hid_tables.GenericDesktop.PAGE_ID),
    hid_spec.items.UsageItem(hid_tables.GenericDesktop.GAMEPAD),
    hid_spec.items.CollectionItem(hid_spec.enums.CollectionType.APPLICATION),
        hid_spec.items.ReportIDItem(0),  # Report ID 0 (no prefix)
        hid_spec.items.UsagePageItem(hid_tables.ButtonPage.PAGE_ID),
        hid_spec.items.UsageMinItem(1),
        hid_spec.items.UsageMaxItem(3),
        hid_spec.items.LogicalMinItem(0),
        hid_spec.items.LogicalMaxItem(1),
        hid_spec.items.ReportSizeItem(1),
        hid_spec.items.ReportCountItem(3),
        hid_spec.items.InputItem(0x02),  # Data, Var, Abs -> Buttons 1-3
        # Padding (5 bits to complete the byte)
        hid_spec.items.ReportSizeItem(5),
        hid_spec.items.ReportCountItem(1),
        hid_spec.items.InputItem(0x03),  # Const -> Padding
        # X, Y, Z Axes
        hid_spec.items.UsagePageItem(hid_tables.GenericDesktop.PAGE_ID),
        hid_spec.items.UsageItem(hid_tables.GenericDesktop.X),
        hid_spec.items.UsageItem(hid_tables.GenericDesktop.Y),
        hid_spec.items.UsageItem(hid_tables.GenericDesktop.Z),
        hid_spec.items.LogicalMinItem(-127),
        hid_spec.items.LogicalMaxItem(127),
        hid_spec.items.ReportSizeItem(8),
        hid_spec.items.ReportCountItem(3),
        hid_spec.items.InputItem(0x02),  # Data, Var, Abs -> X, Y, Z Axes
    hid_spec.items.EndCollectionItem(),
    hid_spec.items.CollectionItem(hid_spec.enums.CollectionType.APPLICATION),
        hid_spec.items.ReportIDItem(1),  # Report ID 1 (prefix 0x01)
        hid_spec.items.UsagePageItem(hid_tables.GenericDesktop.PAGE_ID),
        hid_spec.items.UsageItem(hid_tables.GenericDesktop.SLIDER),
        hid_spec.items.LogicalMinItem(0),
        hid_spec.items.LogicalMaxItem(255),
        hid_spec.items.ReportSizeItem(8),
        hid_spec.items.ReportCountItem(1),
        hid_spec.items.InputItem(0x02),  # Data, Var, Abs -> Slider
    hid_spec.items.EndCollectionItem(),
]

profile = HIDProfile(
    descriptor=ReportDescriptor(mouse_raw_definition),
    name="RawDeviceMouse",
    vendor_id=0x1234,  # Example Vendor ID
    product_id=0x5678, # Example Product ID
    auto_pad=True
)

def main():
    print(f"=== HID Profile: {profile.name} ===\n")

    # Use the raw descriptor directly
    print("Using raw HID report descriptor...")
    descriptor: ReportDescriptor = profile.descriptor
    print(f"Descriptor Size: {len(descriptor)} bytes")
    print("Descriptor Bytes (hex):", descriptor.hex)

    # Parse the HID report descriptor
    print("\nParsing the HID report descriptor...")
    parser = HIDParser()
    reloaded_descriptor: ReportDescriptor = parser.parse(descriptor.bytes)

    # Analyze the descriptor to get the report layout
    print("\nAnalyzing descriptor to get report layout...")
    analyzer = DescriptorAnalyzer()
    layout: DescriptorLayout = analyzer.analyze(reloaded_descriptor)
    print(f"Report Layout Fields: {len(layout)}")
    print(json.dumps(layout.to_dict(), indent=2 ))

    # Produce the codec for encoding/decoding reports
    print("\nCreating HID codec...")
    codec = HIDCodec(layout)
    print("HID codec created successfully.")

    # Example of encoding a report (all buttons released, no movement)
    initial_report = codec.create_report(report_id=0) # Report ID 0
    print("Initial Report Data (Report ID 0):", json.dumps(initial_report.to_dict(), indent=2))
    encoded_bytes = initial_report.encode(codec)
    print("Encoded Report Bytes (Report ID 0):", encoded_bytes.hex().upper())


if __name__ == "__main__":
    main()

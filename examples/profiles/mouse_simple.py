import json
from typing import Dict
from hid_declarative import schema as hid_schema
from hid_declarative import spec as hid_spec
from hid_declarative.spec import tables as hid_tables
from hid_declarative import HIDProfile, HIDCompiler, ReportDescriptor, DescriptorAnalyzer, DescriptorLayout, HIDParser, HIDCodec

mouse_definition = hid_schema.Collection(
    usage_page= hid_tables.GenericDesktop.PAGE_ID,
    usage= hid_tables.GenericDesktop.MOUSE,
    type_id= hid_spec.CollectionType.PHYSICAL,
    children=[
        hid_schema.widgets.ButtonArray(count=3),  # 3 Buttons
        hid_schema.widgets.Padding(5),           # Padding (5 bits)
        hid_schema.widgets.Axis(hid_tables.GenericDesktop.X),  # X Axis
        hid_schema.widgets.Axis(hid_tables.GenericDesktop.Y),  # Y Axis
        hid_schema.widgets.Axis(hid_tables.GenericDesktop.WHEEL)  # Wheel
    ]
)

mouse_profile = HIDProfile(
    root=mouse_definition,
    name="SimpleMouse",
    vendor_id=0x045E,  # Example Vendor ID (Microsoft)
    product_id=0x028E, # Example Product ID
    auto_pad=True
)

def main():
    print(f"=== HID Profile: {mouse_profile.name} ===\n")

    # Compile the profile to get the HID report descriptor
    print("Compiling HID report descriptor...")
    compiler = HIDCompiler()
    descriptor: ReportDescriptor = compiler.compile(mouse_profile.root, auto_pad=mouse_profile.auto_pad)
    print(f"Descriptor Size: {len(descriptor)} bytes")
    print("Descriptor Bytes (hex):", descriptor.hex)

    # Use the compiled bytes to recreate the descriptor object from Parsing
    print("\nParsing the HID report descriptor...")
    generated_descriptor_bytes = descriptor.bytes
    parser = HIDParser()
    reloaded_descriptor: ReportDescriptor = parser.parse(generated_descriptor_bytes)


    # Optionally, analyze the descriptor to get the report layout
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
    initial_report = codec.create_report(report_id=None) # Assuming single report ID, None => default report (0)
    print("Initial Report Data:", json.dumps(initial_report.to_dict(), indent=2))
    initial_report_backup = initial_report.copy()
    encoded_bytes = initial_report.encode(codec)
    print("Encoded Report Bytes:", encoded_bytes.hex().upper())

    # Let's alter the report: Press left button, move X by +10, Y by -5
    initial_report["Button_1"] = 1  # Press left button
    initial_report["X"] = 10         # Move X by +10
    initial_report["Y"] = -5         # Move Y by -5
    print("\nModified Report Data:", json.dumps(initial_report.to_dict(), indent=2))
    modified_bytes = initial_report.encode(codec)
    print("Modified Report Bytes:", modified_bytes.hex().upper())

    # Let's move X outside the logical range to see clamping
    initial_report["X"] = 300  # Outside logical max
    try: 
        initial_report.validate()
        print("\nValidation passed.")
    except ValueError as ve:
        print(f"\nValidation error: {ve}")
        initial_report["X"] = 10 # Reset to valid value

    # Let's decode the modified bytes back to report fields
    print("\nDecoding modified report bytes...")
    decoded_report = codec.decode(modified_bytes)
    print("Decoded Report Data:", json.dumps(decoded_report.to_dict(), indent=2))

    # Let's compute the delta between two reports
    print("\nComputing delta between initial and modified reports...")
    delta_report: Dict = initial_report_backup.delta(decoded_report)
    print("Delta Report Data:", json.dumps(delta_report, indent=2))


if __name__ == "__main__":
    main()

    
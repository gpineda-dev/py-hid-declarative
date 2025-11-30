import json
from typing import Dict
from hid_declarative import schema as hid_schema
from hid_declarative import spec as hid_spec
from hid_declarative.loader import load_engine, load_profile
from hid_declarative.spec import tables as hid_tables
from hid_declarative import HIDProfile

definition = hid_schema.Collection(
    usage_page= hid_tables.GenericDesktop.PAGE_ID,
    usage= hid_tables.GenericDesktop.GAMEPAD,
    type_id= hid_spec.CollectionType.APPLICATION,
    children=[
        # --- First Report: Mouse ---
        hid_schema.nodes.ReportGroup(id=0, children=[
            hid_schema.widgets.ButtonArray(count=3),  # 3 Buttons
            hid_schema.widgets.Padding(5),           # Padding (5 bits)
            hid_schema.widgets.Axis(hid_tables.GenericDesktop.X),  # X Axis
            hid_schema.widgets.Axis(hid_tables.GenericDesktop.Y),  # Y Axis
            hid_schema.widgets.LedArray()
        ]),

        # --- Second Report: Multimedia Controls ---
        hid_schema.nodes.ReportGroup(id=1, children=[

            # No widget for this one, using ReportItem directly
            hid_schema.nodes.ReportItem(
                usage_page=hid_tables.ConsumerPage.PAGE_ID,
                usages=[hid_tables.ConsumerPage.VOLUME_INCREMENT, hid_tables.ConsumerPage.VOLUME_DECREMENT],
                size=1, count=2, logical_min=0, logical_max=1, is_relative=True
            ),

            hid_schema.widgets.MediaKeys(with_volume=False),
            hid_schema.widgets.Padding(6),

            # Add a keyboard with 6 layers
            hid_schema.widgets.KeyboardKeys(count=6)
        ])
    ]
)

myprofile = HIDProfile(
    root=definition,
    name="CompositeMultimedia",
    vendor_id=0x1234,
    product_id=0xABCD,
    auto_pad=True
)

def main():
    profile = myprofile
    print(f"=== HID Profile: {profile.name} ===\n")
    profile = load_profile(profile)
    codec, layout, _ = load_engine(profile)    

    # List the report ids
    print("Report IDs in the profile:")
    print(layout.list_report_ids())

    # Create a message on report ID 1 for volume up
    print("\nCreating a report for Report ID 1 (Multimedia)...")
    report_data = codec.create_report(report_id=1)
    report_data['Volume_Increment'] = 1
    encoded_bytes = report_data.encode(codec)
    print(f"Encoded Bytes: {encoded_bytes.hex().upper()}")

if __name__ == "__main__":
    main()


from hid_declarative import schema as hid_schema
from hid_declarative import spec as hid_spec
from hid_declarative.spec import tables as hid_tables
from hid_declarative import HIDProfile

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
# Tutorial: Create a Custom Mouse

In this tutorial, we will define a standard 3-button mouse with a scroll wheel. This is the most common HID device.

## 1. The Python Profile

Create a file named `my_mouse.py`. We use the `hid_declarative` facade to access all necessary components.

```python title="my_mouse.py"
from hid_declarative import schema as hid_schema
from hid_declarative import spec as hid_spec
from hid_declarative.spec import tables as hid_tables
from hid_declarative import HIDProfile

# 1. Define the Mouse Schema
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

# 2. Create the HID Profile
mouse_profile = HIDProfile(
    root=mouse_definition,
    name="SimpleMouse",
    vendor_id=0x045E,  # Example Vendor ID (Microsoft)
    product_id=0x028E, # Example Product ID
    auto_pad=True
)
```

## 2. Compile the Profile
Now, transform this Python definition into a raw binary HID Report Descriptor that can be fed to a USB controller (like Linux ConfigFS).

<!-- termynal -->
```bash
$ hid-declarative compile my_mouse.py:mouse_profile
Compiling profile 'SimpleMouse'...
Success! Generated 57 bytes.
05010902A10005091500250155006500750195031901290381020500250075059501810305011581257F7508093081020931810209388102C0
(Hex view. Use -o to save to file)
```



## 3. Verify
Use the `inspect` command to double-check that your layout matches your expectations (especially byte alignment).

<!-- termynal -->
```bash
$ hid-declarative inspect py://my_mouse.py:mouse_profile
=== 0. Hex inline representation (53 bytes) ===
05010902A100050915002501750195031901290381020500250075059501810305011581257F7508093081020931810209388102C0

=== 1. Logical Structure (27 items) ===
HID Report Descriptor
├── 04 UsagePage: 1 (Generic Desktop)
├── 08 Usage: GenericDesktop.MOUSE (Mouse)
└── A0 Collection (Physical)
    ├── 04 UsagePage: 9 (Button)
    ├── 14 LogicalMin: 0
    ├── 24 LogicalMax: 1
    ├── 74 ReportSize: 1
    ├── 94 ReportCount: 3
    ├── 18 UsageMin: 1 (Button_1)
    ├── 28 UsageMax: 3 (Button_3)
    ├── 80 Input: 2
    ├── 04 UsagePage: 0 (Unknown Page 0x0)
    ├── 24 LogicalMax: 0
    ├── 74 ReportSize: 5
    ├── 94 ReportCount: 1
    ├── 80 Input: 3
    ├── 04 UsagePage: 1 (Generic Desktop)
    ├── 14 LogicalMin: -127
    ├── 24 LogicalMax: 127
    ├── 74 ReportSize: 8
    ├── 08 Usage: GenericDesktop.X (X)
    ├── 80 Input: 2
    ├── 08 Usage: GenericDesktop.Y (Y)
    ├── 80 Input: 2
    ├── 08 Usage: GenericDesktop.WHEEL (Wheel)
    ├── 80 Input: 2
    └── C0 End Collection

=== REPORT ID 0 Memory Layout ===

====== Input Report (Size: 4 bytes) ======
+---------------------------------------------------------------------------------+
| Bits   | Byte | Mask | Name     | Page            | Type  |  Min | Max | Signed |
|--------+------+------+----------+-----------------+-------+------+-----+--------|
| 0..0   | 0    | 0x1  | Button_1 | Button          | input |    0 |   1 |   -    |
| 1..1   | 0    | 0x1  | Button_2 | Button          | input |    0 |   1 |   -    |
| 2..2   | 0    | 0x1  | Button_3 | Button          | input |    0 |   1 |   -    |
| 8..15  | 1    | 0xFF | X        | Generic Desktop | input | -127 | 127 |  Yes   |
| 16..23 | 2    | 0xFF | Y        | Generic Desktop | input | -127 | 127 |  Yes   |
| 24..31 | 3    | 0xFF | Wheel    | Generic Desktop | input | -127 | 127 |  Yes   |
+---------------------------------------------------------------------------------+

====== Output Report (Size: 0 bytes) ======
Empty report (No data fields)

====== Feature Report (Size: 0 bytes) ======
```

> You can see a clean table with all fields defined in the input report. The mouse has 3 buttons (bits 0-2), 5 bits of padding, and three signed 8-bit axes for X, Y, and Wheel movement.

You could use the `--json` flag to get a JSON representation of the report descriptor as well.
```json
{
  "meta": {
    "size_bytes": 57,
    "hex": "05010902A10005091500250155006500750195031901290381020500250075059501810305011581257F7508093081020931810209388102C0",
    "base64": "BQEJAqEABQkVACUBVQBlAHUBlQMZASkDgQIFACUAdQWVAYEDBQEVgSV/dQgJMIECCTGBAgk4gQLA"
  },
  "layout": {
    "reports": {
      "0": {
        "report_id": 0,
        "input": {
          "report_type": "input",
          "report_id": 0,
          "size_bytes": 4,
          "fields": [
            {
              "bit_offset": 0,
              "bit_size": 1,
              "mask": 1,
              "byte_offset": 0,
              "usage_page": 9,
              "usage_id": 1,
              "name": "Button_1",
              "logical_min": 0,
              "logical_max": 1,
              "physical_min": 0,
              "physical_max": 0,
              "is_signed": false,
              "report_type": "input",
              "report_id": 0,
              "usage_page_name": "Button"
            },
           ...
            {
              "bit_offset": 24,
              "bit_size": 8,
              "mask": 255,
              "byte_offset": 3,
              "usage_page": 1,
              "usage_id": 56,
              "name": "Wheel",
              "logical_min": -127,
              "logical_max": 127,
              "physical_min": 0,
              "physical_max": 0,
              "is_signed": true,
              "report_type": "input",
              "report_id": 0,
              "usage_page_name": "Generic Desktop"
            }
          ]
        },
        "output": {
          "report_type": "output",
          "report_id": 0,
          "size_bytes": 0,
          "fields": []
        },
        "feature": {
          "report_type": "feature",
          "report_id": 0,
          "size_bytes": 0,
          "fields": []
        }
      }
    }
  },
  "structure": [
    {
      "tag_code": 4,
      "tag_name": "UsagePage",
      "data": 1
    },
    ...
    {
      "tag_code": 192,
      "tag_name": "EndCollection",
      "data": null
    }
  ]
}
```
# Guide: Reverse Engineering a Device

This guide shows how to extract the HID Descriptor from a real USB device on Linux and understand its protocol structure.

## Prerequisites

* A Linux system with USB access.
* `hid-declarative` installed with the `hidapi` extra:
  ```bash
  pip install "hid-declarative[cli,hidapi]"
  ```
## Step 1: Identify the Device
Connect your device (e.g., a Joystick or Keyboard). Use the `list` command to find it.

<!-- termynal -->
```bash
$ sudo .venv/bin/hid-declarative list
Found 3 interfaces across devices:

📦 Dell KB216 Wired Keyboard ()
   ├── Interface 0
   │    Path: /dev/hidraw1
   │    VID:PID: 413c:2113
   │    Dump (via id): hid-declarative dump --device id://413c:2113:0
   │    Dump (via path): hid-declarative dump --device path:///dev/hidraw1
   └── Interface 1
        Path: /dev/hidraw2
        VID:PID: 413c:2113
        Dump (via id): hid-declarative dump --device id://413c:2113:1
        Dump (via path): hid-declarative dump --device path:///dev/hidraw2

📦 T.16000M (Thrustmaster)
   └── Interface 0
        Path: /dev/hidraw0
        VID:PID: 044f:b10a
        Dump (via id): hid-declarative dump --device id://044f:b10a:0
        Dump (via path): hid-declarative dump --device path:///dev/hidraw0

```

## Step 2: Dump and inspect the Descriptor
We will extract the binary HID Report Descriptor from the kernel and pipe it directly to the `inspect` command for analysis.

<!-- termynal -->
```bash
$ sudo .venv/bin/hid-declarative dump --device id://044f:b10a:0 | .venv/bin/hid-declarative inspect stdin+bin://
Resolved: T.16000M -> /dev/hidraw0

=== 0. Hex inline representation (126 bytes) ===
05010904A101050919012910150025013500450175019510810205010939150025073500463B016514750495018142810105010930150026FF3F350046FF3F6500750E95018102750281010931750E81027502810109350936150026FF00350046FF0065007508950281
020700FF000027FFFF0000090175089504B1A2C0

=== 1. Logical Structure (58 items) ===
HID Report Descriptor
├── 04 UsagePage: 1 (Generic Desktop)
├── 08 Usage: 4 (Joystick)
└── A0 Collection (Application)
    ├── 04 UsagePage: 9 (Button)
    ├── 18 UsageMin: 1 (Button_1)
    ├── 28 UsageMax: 16 (Button_16)
    ├── 14 LogicalMin: 0
    ├── 24 LogicalMax: 1
    ├── 34 PhysicalMin: 0
    ├── 44 PhysicalMax: 1
    ├── 74 ReportSize: 1
    ├── 94 ReportCount: 16
    ├── 80 Input: 2
    ├── 04 UsagePage: 1 (Generic Desktop)
    ├── 08 Usage: 57 (Hat_Switch)
    ├── 14 LogicalMin: 0
    ├── 24 LogicalMax: 7
    ├── 34 PhysicalMin: 0
    ├── 44 PhysicalMax: 315
    ├── 64 Unit: 20
    ├── 74 ReportSize: 4
    ├── 94 ReportCount: 1
    ├── 80 Input: 66
    ├── 80 Input: 1
    ├── 04 UsagePage: 1 (Generic Desktop)
    ├── 08 Usage: 48 (X)
    ├── 14 LogicalMin: 0
    ├── 24 LogicalMax: 16383
    ├── 34 PhysicalMin: 0
    ├── 44 PhysicalMax: 16383
    ├── 64 Unit: 0
    ├── 74 ReportSize: 14
    ├── 94 ReportCount: 1
    ├── 80 Input: 2
    ├── 74 ReportSize: 2
    ├── 80 Input: 1
    ├── 08 Usage: 49 (Y)
    ├── 74 ReportSize: 14
    ├── 80 Input: 2
    ├── 74 ReportSize: 2
    ├── 80 Input: 1
    ├── 08 Usage: 53 (Rz)
    ├── 08 Usage: 54 (Slider)
    ├── 14 LogicalMin: 0
    ├── 24 LogicalMax: 255
    ├── 34 PhysicalMin: 0
    ├── 44 PhysicalMax: 255
    ├── 64 Unit: 0
    ├── 74 ReportSize: 8
    ├── 94 ReportCount: 2
    ├── 80 Input: 2
    ├── 04 UsagePage: 65280 (Vendor Defined (0xFF00))
    ├── 24 LogicalMax: 65535
    ├── 08 Usage: 1 (Usage 0x01)
    ├── 74 ReportSize: 8
    ├── 94 ReportCount: 4
    ├── B0 Feature: -94
    └── C0 End Collection

=== REPORT ID 0 Memory Layout ===

====== Input Report (Size: 9 bytes) ======
+--------------------------------------------------------------------------------------+
| Bits   | Byte | Mask   | Name       | Page            | Type  | Min |   Max | Signed |
|--------+------+--------+------------+-----------------+-------+-----+-------+--------|
| 0..0   | 0    | 0x1    | Button_1   | Button          | input |   0 |     1 |   -    |
| 1..1   | 0    | 0x1    | Button_2   | Button          | input |   0 |     1 |   -    |
| 2..2   | 0    | 0x1    | Button_3   | Button          | input |   0 |     1 |   -    |
| 3..3   | 0    | 0x1    | Button_4   | Button          | input |   0 |     1 |   -    |
| 4..4   | 0    | 0x1    | Button_5   | Button          | input |   0 |     1 |   -    |
| 5..5   | 0    | 0x1    | Button_6   | Button          | input |   0 |     1 |   -    |
| 6..6   | 0    | 0x1    | Button_7   | Button          | input |   0 |     1 |   -    |
| 7..7   | 0    | 0x1    | Button_8   | Button          | input |   0 |     1 |   -    |
| 8..8   | 1    | 0x1    | Button_9   | Button          | input |   0 |     1 |   -    |
| 9..9   | 1    | 0x1    | Button_10  | Button          | input |   0 |     1 |   -    |
| 10..10 | 1    | 0x1    | Button_11  | Button          | input |   0 |     1 |   -    |
| 11..11 | 1    | 0x1    | Button_12  | Button          | input |   0 |     1 |   -    |
| 12..12 | 1    | 0x1    | Button_13  | Button          | input |   0 |     1 |   -    |
| 13..13 | 1    | 0x1    | Button_14  | Button          | input |   0 |     1 |   -    |
| 14..14 | 1    | 0x1    | Button_15  | Button          | input |   0 |     1 |   -    |
| 15..15 | 1    | 0x1    | Button_16  | Button          | input |   0 |     1 |   -    |
| 16..19 | 2    | 0xF    | Hat_Switch | Generic Desktop | input |   0 |     7 |   -    |
| 24..37 | 3    | 0x3FFF | X          | Generic Desktop | input |   0 | 16383 |   -    |
| 40..53 | 5    | 0x3FFF | Y          | Generic Desktop | input |   0 | 16383 |   -    |
| 56..63 | 7    | 0xFF   | Rz         | Generic Desktop | input |   0 |   255 |   -    |
| 64..71 | 8    | 0xFF   | Slider     | Generic Desktop | input |   0 |   255 |   -    |
+--------------------------------------------------------------------------------------+

====== Output Report (Size: 0 bytes) ======
Empty report (No data fields)

====== Feature Report (Size: 4 bytes) ======
+------------------------------------------------------------------------------------------------+
| Bits   | Byte | Mask | Name         | Page                    | Type    | Min |   Max | Signed |
|--------+------+------+--------------+-------------------------+---------+-----+-------+--------|
| 0..7   | 0    | 0xFF | Usage 0x01   | Vendor Defined (0xFF00) | feature |   0 | 65535 |   -    |
| 8..15  | 1    | 0xFF | Usage 0x01_2 | Vendor Defined (0xFF00) | feature |   0 | 65535 |   -    |
| 16..23 | 2    | 0xFF | Usage 0x01_3 | Vendor Defined (0xFF00) | feature |   0 | 65535 |   -    |
| 24..31 | 3    | 0xFF | Usage 0x01_4 | Vendor Defined (0xFF00) | feature |   0 | 65535 |   -    |
+------------------------------------------------------------------------------------------------+
```

### Understanding the Output
The `inspect` command reveals two views:   
1. **Logical Structure**: A tree representation of the HID Report Descriptor, showing usages, collections, and data fields.   
2. **Memory Layout**: The bit-level map of the data paket. Use this to write your driver.

Example output for an axis:
```console
+--------------------------------------------------------------------------------------+
| Bits   | Byte | Mask   | Name       | Page            | Type  | Min |   Max | Signed |
|--------+------+--------+------------+-----------------+-------+-----+-------+--------|
| 24..37 | 3    | 0x3FFF | X          | Generic Desktop | input |   0 | 16383 |   -    |
```

* This tells you that the X axis :
    * starts at bit 24 (byte 3)
    * spans 14 bits (mask 0x3FFF)
    * is of type `input`
    * has a logical range from 0 to 16383 (unsigned).

## Step 3: Live Monitoring
Now that you understand the structure via the descriptor, you can use the `monitor` command to see live data reports from the device as you interact with it.

<!-- termynal -->
```bash
$ sudo .venv/bin/hid-declarative live --device path:///dev/hidraw0 --target file://examples/data/dump_t16000m.bin
(py-hid-parser) gpineda@thinkpad-e15g2:~/Documents/projects/py-hid-parser$ sudo .venv/bin/hid-declarative live --device path:///dev/hidraw0 --target file://examples/data/dump_t16000m.bin 
Using direct path: /dev/hidraw0
Connected! Listening for reports... (Ctrl+C to stop)

Decoded Report: {'timestamp': 1764542487.5159943, 'data': {'Button_1': False, 'Button_2': False, 'Button_3': False, 'Button_4': False, 'Button_5': False, 'Button_6': False, 'Button_7': False, 'Button_8': False, 
'Button_9': False, 'Button_10': False, 'Button_11': False, 'Button_12': False, 'Button_13': False, 'Button_14': False, 'Button_15': False, 'Button_16': False, 'Hat_Switch': 2, 'Generic Desktop Idx': 0, 'X': 8192,
'Generic Desktop Idx_2': 0, 'Y': 8192, 'Generic Desktop Idx_3': 0, 'Rz': 128, 'Slider': 0}}

Decoded Report: {'timestamp': 1764542487.699835, 'data': {'Button_1': False, 'Button_2': False, 'Button_3': False, 'Button_4': False, 'Button_5': False, 'Button_6': False, 'Button_7': False, 'Button_8': False, 
'Button_9': False, 'Button_10': False, 'Button_11': False, 'Button_12': False, 'Button_13': False, 'Button_14': False, 'Button_15': False, 'Button_16': False, 'Hat_Switch': 15, 'Generic Desktop Idx': 0, 'X': 
8192, 'Generic Desktop Idx_2': 0, 'Y': 8192, 'Generic Desktop Idx_3': 0, 'Rz': 128, 'Slider': 0}}

Decoded Report: {'timestamp': 1764542490.2524006, 'data': {'Button_1': True, 'Button_2': False, 'Button_3': False, 'Button_4': False, 'Button_5': False, 'Button_6': False, 'Button_7': False, 'Button_8': False, 
'Button_9': False, 'Button_10': False, 'Button_11': False, 'Button_12': False, 'Button_13': False, 'Button_14': False, 'Button_15': False, 'Button_16': False, 'Hat_Switch': 15, 'Generic Desktop Idx': 0, 'X': 
8192, 'Generic Desktop Idx_2': 0, 'Y': 8192, 'Generic Desktop Idx_3': 0, 'Rz': 128, 'Slider': 0}}

Decoded Report: {'timestamp': 1764542491.9400523, 'data': {'Button_1': False, 'Button_2': False, 'Button_3': False, 'Button_4': False, 'Button_5': False, 'Button_6': False, 'Button_7': False, 'Button_8': False, 
'Button_9': False, 'Button_10': False, 'Button_11': False, 'Button_12': False, 'Button_13': False, 'Button_14': False, 'Button_15': False, 'Button_16': False, 'Hat_Switch': 15, 'Generic Desktop Idx': 0, 'X': 
8192, 'Generic Desktop Idx_2': 0, 'Y': 8192, 'Generic Desktop Idx_3': 0, 'Rz': 128, 'Slider': 0}}
```

You can see live decoded reports showing button states, hat switch position, and axis values as you manipulate the joystick.   
In the previous example, pressing Button 1 changed its value from `False` to `True` in the decoded reports and the same applied to the Hat_Switch when moved.

<!-- termynal -->
```bash
$ sudo .venv/bin/hid-declarative live --device path:///dev/hidraw0 --raw
Using direct path: /dev/hidraw0
Connected! Listening for reports... (Ctrl+C to stop)
Raw Report: {'timestamp': 1764543108.1163187, 'data': '00003f002000208d00'}
Raw Report: {'timestamp': 1764543108.1639853, 'data': '00003f00200020b100'}
Raw Report: {'timestamp': 1764543108.2120855, 'data': '00003f00200020c600'}
Raw Report: {'timestamp': 1764543108.260018, 'data': '00003f00200020cb00'}
Raw Report: {'timestamp': 1764543108.3000822, 'data': '00003f00200020a300'}
Raw Report: {'timestamp': 1764543108.3483546, 'data': '00003f002000208000'}
Raw Report: {'timestamp': 1764543109.7157779, 'data': '000000002000208000'}
```
You can also use the `--raw` flag to see the raw binary reports in hex format as they are received from the device. In this scenario, the descriptor is not used for decoding and the raw data is shown directly.

## Step 4: Save for later
If you want to work on this device later without being connected, save the binary.
```bash
$ sudo .venv/bin/hid-declarative dump --device id://044f:b10a:0 --output examples/data/dump_t16000m.bin
Resolved: T.16000M -> /dev/hidraw0
Dumped HID Report Descriptor to examples/data/dump_t16000m.bin
```

You can now inspect it offline.
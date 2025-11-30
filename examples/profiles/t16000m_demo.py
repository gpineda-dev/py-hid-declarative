from pathlib import Path
from hid_declarative.loader import load_engine
from hid_declarative.parser import HIDParser
from hid_declarative.profile import HIDProfile
from hid_declarative.runtime.analyzer import DescriptorAnalyzer
from hid_declarative.runtime.codec import HIDCodec


t16000m_profile = HIDProfile(
    name="Thrustmaster T.16000M",
    vendor_id=0x044F,  # Thrustmaster
    product_id=0xB10A, # T.16000M
    raw_descriptor=Path(__file__).parent.parent.joinpath("data", "dump_t16000m.bin").read_bytes()
)

def main() -> HIDProfile:
    print(f"=== Profile Demonstration: {t16000m_profile.name} ===\n")

    # A. Generate Engine from Profile
    print("-> Loading engine from profile...")
    codec, layout, profile = load_engine(t16000m_profile)
    
    print(f"-> Layout Fields: {len(layout)}")
    for field in layout.fields:
        if field.usage_id == 0: continue # Skip padding
        
        start = field.bit_offset
        end = start + field.bit_size - 1
        print(f"   [{start:02d}..{end:02d}] {field.name:<15} ({field.report_type})")
    print("")

    # B. Runtime (Simulation)
    print("-> Runtime Test (Decode)...")
    # Example raw input report from the joystick (Report ID 1)
    initial_report = codec.create_report(report_id=None) # Assuming single report ID, None => default report (0)
    print(f"   Initial Report Data: {initial_report.to_dict()}")

    # We simulate some actions (Buttons pressed, Axis moved)
    modified_report = initial_report.copy()
    modified_report['Button_1'] = True
    modified_report['X'] = 8000  # Mid-right
    modified_report['Y'] = 400  # Mid-up
    print(f"   Modified Report Data: {modified_report.to_dict()}")
    delta = initial_report.delta(modified_report)
    print(f"   Delta Report Data: {delta}")

    # Encoding the modified report
    encoded_bytes = modified_report.encode(codec)
    print(f"   Encoded Report Bytes: {encoded_bytes.hex().upper()}")

    # Decoding back the bytes
    decoded = codec.decode(encoded_bytes)
    print(f"   Decoded Report Data: {decoded.to_dict()}")
    

if __name__ == "__main__":
    main()



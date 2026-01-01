from hid_declarative.profile import HIDProfile
from hid_declarative.runtime.analyzer import DescriptorAnalyzer
from hid_declarative.runtime.codec import REPORT_CODEC_MAP, HIDReportCodec
from hid_declarative.runtime.layout import DescriptorLayout
from typing import Any, Dict, Tuple, Optional, Type

from hid_declarative.runtime.reports import DataReportType
from hid_declarative.spec.descriptor import ReportDescriptor

class HIDContext:

    _codec_map: Dict[Tuple[int, str], HIDReportCodec]

    descriptor_layout: DescriptorLayout
    _is_initialised: bool = False

    def __init__(self, profile: HIDProfile):
        assert isinstance(profile, HIDProfile), "profile must be an instance of HIDProfile"
        self.profile = profile
        self._codec_map = {}
        self._is_initialised = False
        self.initialize()

    @property
    def descriptor(self) -> ReportDescriptor:
        assert self.profile.has_compiled_descriptor(), "Profile does not have a compiled descriptor."
        return self.profile.descriptor

    def initialize(self):
        if self._is_initialised:
            raise RuntimeError("HIDContext is already initialized.")
        
        analyser = DescriptorAnalyzer()
        self.descriptor_layout = analyser.analyze(self.descriptor)

        for report_group in self.descriptor_layout.get_all_groups():
            codec_class: Type[HIDReportCodec] = REPORT_CODEC_MAP.get(report_group.report_type)
            if codec_class:
                key = (report_group.report_id, report_group.report_type)
                self._codec_map[key] = codec_class(report_group)

        self._is_initialised = True

    def has_multiple_report_ids(self) -> bool:
        return self.descriptor_layout.has_multiple_report_ids()

    def _get_codec(self, report_id: Optional[int], report_type: str = "input") -> HIDReportCodec:
        target_id = self.descriptor_layout.resolve_report_id(report_id)

        key = (target_id, report_type)
        codec = self._codec_map.get(key)
        if not codec:
            raise ValueError(f"No codec found for report ID {target_id} and type '{report_type}'")
        return codec
    
    def _extract_report_id(self, data: bytes) -> Tuple[Optional[int], bytes]:
        """
        Analyze the raw data to separate the report ID (if any) from the payload.
        Returns:
            report_id (int): The report ID extracted (0 if none).
            payload (bytes): The remaining data after removing the report ID byte.
        """

        if not data:
            return None, b''
        
        if self.descriptor_layout.has_multiple_report_ids():
            report_id = data[0]
            payload = data[1:]
            return report_id, payload
        
        return None, data
    
    def create_report(self, report_id: Optional[int] = None, report_type: str = "input") -> DataReportType:
        """Create an empty DataReport for the specified report ID."""
        codec = self._get_codec(report_id, report_type=report_type)
        report = codec.create_report()
        return self.attach_report(report)
    
    def attach_report(self, report: DataReportType) -> DataReportType:
        """Attaches this context to the given DataReport."""
        report._attach_context(self)
        return report
    
    def decode(self, raw_bytes: bytes, report_type: str = "input") -> 'DataReportType':
        report_id, payload = self._extract_report_id(raw_bytes)
        codec = self._get_codec(report_id, report_type=report_type)
        data = codec.decode_payload(payload)

        report = codec.create_report()
        report._values.update(data)

        return self.attach_report(report)
    
    def encode(self, data: Dict[str, Any], report_id: Optional[int] = None, report_type: str = "input", validate: bool = True) -> bytes:
        target_id = self.descriptor_layout.resolve_report_id(report_id)
        codec = self._get_codec(target_id, report_type=report_type)
        
        payload = codec.encode_payload(data, validate=validate)
        if self.descriptor_layout.has_multiple_report_ids():
            return bytes([target_id]) + payload
        
        return payload
            
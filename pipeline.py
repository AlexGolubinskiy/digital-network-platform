"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

SIGNAL PROCESSING PIPELINE

Главный конвейер обработки сигналов.

DSP -> Analysis -> Localization -> Geo -> Alarm -> SystemEvent -> EventBus
=======================================================================
"""

from __future__ import annotations
import uuid
from datetime import datetime
from models import Device, AudioData, Alarm, AlarmLocation
from config import NetworkProfile
from event_bus import SystemEvent, EventType

class SignalProcessingPipeline:
    """Центральный оркестратор вычислительного конвейера платформы."""

    def __init__(
        self,
        profile: NetworkProfile,
        dsp_engine,
        analysis_engine,
        localization_engine,
        geo_engine,
        database=None,
        event_bus=None
    ):
        self.profile = profile
        self.dsp = dsp_engine
        self.analysis = analysis_engine
        self.localization = localization_engine
        self.geo = geo_engine
        self.database = database
        self.event_bus = event_bus

    def process(self, device_a: Device, device_b: Device, signal_a, signal_b, section_length: float) -> Alarm:
        """Сквозной последовательный расчет акустических параметров утечки и ГЕО-координат дефекта."""
        audio_a = AudioData(signal=signal_a, sample_rate=self.profile.sample_rate)
        audio_b = AudioData(signal=signal_b, sample_rate=self.profile.sample_rate)

        self.dsp.bandpass(audio_a)
        self.dsp.bandpass(audio_b)

        analysis_result = self.analysis.analyze(audio_a)
        localization_result = self.localization.locate(audio_a.signal, audio_b.signal, section_length, self.profile)
        leak_point = self.geo.interpolate(device_a.coordinate, device_b.coordinate, localization_result.distance_to_leak, section_length)

        alarm = Alarm(
            alarm_id=str(uuid.uuid4()),
            device_id=device_a.device_id,
            network_type=self.profile.network_type,
            location=AlarmLocation(
                coordinate=leak_point,
                distance_from_start=localization_result.distance_to_leak,
                confidence=localization_result.confidence
            ),
            analysis=analysis_result,
            created_at=datetime.now(),
            status="active"
        )

        if self.database:
            self.database.save_alarm(alarm)

        if self.event_bus:
            event = SystemEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ALARM_CREATED,
                data={"alarm": alarm},
                timestamp=datetime.now(),
                source="Pipeline"
            )
            self.event_bus.publish(event)

        return alarm

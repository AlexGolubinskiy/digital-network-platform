"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0
SIGNAL PROCESSING PIPELINE
Центральный конвейер и оркестратор обработки аварийных сигналов.
Flow: Signal -> DSP -> Analysis -> Localization -> Geo -> Alarm -> EventBus
=======================================================================
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime
from models import Device, AudioData, Alarm, AlarmLocation
from config import NetworkProfile
from event_bus import SystemEvent, EventType

logger = logging.getLogger("DigitalNetworkPlatform.Pipeline")

class SignalProcessingPipeline:
    """
    Центральный оркестратор вычислительного конвейера платформы.
    Последовательно выполняет фильтрацию шумов, спектральный анализ,
    кросс-корреляционную локализацию дефекта и ГИС-интерполяцию.
    """
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

    def process(
        self, 
        device_a: Device, 
        device_b: Device, 
        signal_a: np.ndarray, 
        signal_b: np.ndarray, 
        section_length: float
    ) -> Alarm:
        """
        Сквозной последовательный расчет акустических параметров утечки,
        определение точных ГЕО-координат дефекта и регистрация инцидента.
        
        :param device_a: Карточка датчика А (начало участка)
        :param device_b: Карточка датчика Б (конец участка)
        :param signal_a: Вектор NumPy виброакустических данных датчика А
        :param signal_b: Вектор NumPy виброакустических данных датчика Б
        :param section_length: Физическое расстояние между датчиками по трубе (метры)
        """
        logger.info(
            f"Запуск конвейера обработки сигналов для устройств {device_a.device_id} и {device_b.device_id}"
        )

        # 1. Формирование базовых контейнеров входных сигналов с типизацией NumPy массивов
        audio_a = AudioData(signal=signal_a, sample_rate=self.profile.sample_rate)
        audio_b = AudioData(signal=signal_b, sample_rate=self.profile.sample_rate)

        # 2. Высокопроизводительная In-place фильтрация Баттерворта от гула земли и РЭБ помех
        audio_a = self.dsp.bandpass(audio_a)
        audio_b = self.dsp.bandpass(audio_b)

        # 3. Быстрое преобразование Фурье (FFT), поиск пиковой частоты и расчет уровня SNR
        analysis_result = self.analysis.analyze(audio_a)

        # 4. Вычисление точной временной задержки GCC-PHAT с субсэмпловой интерполяцией пика свища
        # и физически корректным расчетом дистанции (без багов со знаком модуля)
        localization_result = self.localization.locate(
            audio_a.signal, 
            audio_b.signal, 
            section_length, 
            self.profile
        )

        # 5. Линейная ГЕО-интерполяция метки аварии на карте города по формуле Haversine
        leak_point = self.geo.interpolate(
            device_a.coordinate, 
            device_b.coordinate, 
            localization_result.distance_to_leak, 
            section_length
        )

        # 6. Инициализация официального аварийного события платформы
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

        # 7. Запись прорыва в персистентное реляционное хранилище СУБД (при наличии подключения)
        if self.database:
            try:
                self.database.save_alarm(alarm)
                logger.info(f"Аварийное событие {alarm.alarm_id} успешно сохранено в базу данных.")
            except Exception as e:
                logger.error(f"Ошибка записи аларма в БД: {error}")

        # 8. Публикация типизированного сообщения в шину для запуска реактивной цепочки ТОиР и ИИ-аналитики
        if self.event_bus:
            event = SystemEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ALARM_CREATED,
                data={"alarm": alarm},
                timestamp=datetime.now(),
                source="SignalProcessingPipeline"
            )
            self.event_bus.publish(event)
            logger.info(f"Событие ALARM_CREATED отправлено в EventBus для аларма {alarm.alarm_id}")

        return alarm

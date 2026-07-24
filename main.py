"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

MAIN ORCHESTRATOR & SIMULATION RUNNER

Главный файл запуска и сквозного тестирования платформы.
=======================================================================
"""

from __future__ import annotations
import uuid
import logging
import numpy as np

# Импортируем инфраструктурные и конфигурационные слои
from config import init_directories, HEAT_PROFILE
from models import (
    Coordinate, 
    Device, 
    SensorType, 
    NetworkType, 
    NetworkAsset, 
    PipeMaterial,
    SystemEvent,
    EventType
)
from database import Database
from event_bus import EventBus

# Импорты по коротким именам файлов модулей
from dsp import DSPEngine
from analysis import AnalysisEngine
from localization import LocalizationEngine
from geo import GeoEngine
from pipeline import SignalProcessingPipeline
from prediction import PredictionEngine
from asset_risk import AssetRiskEngine
from digital_twin import DigitalTwinEngine
from signal_emulator import generate_leak_signal, create_signal_record

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("DigitalNetworkPlatform.Main")

# Глобальная переменная базы данных для доступа изолированного обработчика
database: Database | None = None

def handle_alarm_event(event: SystemEvent):
    """
    Промышленный именованный обработчик событий шины.
    Имеет изолированную try-except защиту от временных блокировок SQLite (database is locked).
    """
    if database is None:
        return

    alarm = event.data.get("alarm")
    if alarm is None:
        logger.warning("ALARM_CREATED without alarm object")
        return

    try:
        # Защищенная трансляция лога в историческую таблицу СУБД
        database.save_event(
            str(uuid.uuid4()),
            "ALARM_LOGGED",
            {"id": alarm.alarm_id}
        )
    except Exception as error:
        # Защита: сбой диска или блокировка СУБД не прерывают реактивную шину EventBus
        logger.exception("Failed to save alarm event to database: %s", error)

def run_system_simulation() -> dict:
    """Сквозной интеграционный тест-кейс верификации всех слоев платформы."""
    logger.info("========================================")
    logger.info("  STARTING DIGITAL NETWORK PLATFORM v1.0")
    logger.info("========================================")

    init_directories()

    global database
    database = Database()
    event_bus = EventBus()

    profile = HEAT_PROFILE
    dsp = DSPEngine(profile)
    analysis = AnalysisEngine(profile)
    localization = LocalizationEngine()
    geo = GeoEngine()
    
    prediction_engine = PredictionEngine()
    asset_risk_engine = AssetRiskEngine()
    digital_twin = DigitalTwinEngine()
    
    pipeline = SignalProcessingPipeline(
        profile=profile,
        dsp_engine=dsp,
        analysis_engine=analysis,
        localization_engine=localization,
        geo_engine=geo,
        database=database,
        event_bus=event_bus
    )

    # Стыковка подписок EventBus с отказоустойчивым обработчиком логов
    event_bus.subscribe(
        EventType.ALARM_CREATED,
        handle_alarm_event
    )
    
    logger.info("Event Bus Listeners: LINKED")

    sensor_a = Device(
        device_id="TH-001",
        name="Акустический датчик Колодец А",
        sensor_type=SensorType.ACOUSTIC,
        coordinate=Coordinate(latitude=44.720000, longitude=37.770000),
        network_type=NetworkType.HEAT,
        organization="АТЭК"
    )

    sensor_b = Device(
        device_id="TH-002",
        name="Акустический датчик Колодец Б",
        sensor_type=SensorType.ACOUSTIC,
        coordinate=Coordinate(latitude=44.722000, longitude=37.772000),
        network_type=NetworkType.HEAT,
        organization="АТЭК"
    )

    database.save_device(sensor_a)
    database.save_device(sensor_b)

    section_length = geo.distance(sensor_a.coordinate, sensor_b.coordinate)
    
    asset = NetworkAsset(
        asset_id="HEAT-001",
        name="Main Heat Line",
        length=section_length,
        installation_year=1998,
        material=PipeMaterial.STEEL,
        sensor_ids=[sensor_a.device_id, sensor_b.device_id]
    )

    digital_twin.register_asset(asset)
    database.save_asset(asset)
    logger.info("Asset registered. Length: %.2f m", section_length)

    signal_a = generate_leak_signal(duration=2.0, sample_rate=profile.sample_rate, frequency=800.0)
    signal_b = generate_leak_signal(duration=2.0, sample_rate=profile.sample_rate, frequency=800.0, noise_level=0.25)
    
    shift_samples = int(0.03 * profile.sample_rate)
    signal_b = np.roll(signal_b.copy(), shift_samples)

    logger.info("Running pipeline calculation...")
    alarm = pipeline.process(sensor_a, sensor_b, signal_a, signal_b, section_length)

    if alarm is None:
        raise RuntimeError("Pipeline did not create Alarm object")

    record = create_signal_record(
        device_id=sensor_a.device_id,
        frequency=alarm.analysis.parameters.get("dominant_frequency", 0.0),
        snr=alarm.analysis.parameters.get("snr", 0.0),
        probability=alarm.analysis.probability
    )
    database.save_signal(record)

    # Детерминированный расчет трендов для MVP
    prediction = prediction_engine.predict(record)
    risk_report = asset_risk_engine.evaluate(asset, prediction)
    
    updated = digital_twin.update_risk(risk_report)
    if not updated:
        raise RuntimeError("Digital Twin asset update failed")
    
    database.save_event(str(uuid.uuid4()), "ASSET_RISK_CALCULATED", {
        "asset_id": risk_report.asset_id,
        "risk_score": risk_report.risk_score,
        "condition": risk_report.condition.value if hasattr(risk_report.condition, "value") else risk_report.condition
    })

    gis_snapshot = digital_twin.get_snapshot()

    print("\n" + "="*65)
    print("      ИТОГОВЫЙ ОТЧЕТ СИСТЕМЫ ВЕРИФИКАЦИИ ЦИФРОВОЙ ПЛАТФОРМЫ")
    print("="*65)
    print(f"  • ID Тревоги в СУБД:       {alarm.alarm_id}")
    print(f"  • Спектральная вероятность: {alarm.analysis.probability * 100:.1f}% ({alarm.analysis.description})")
    print(f"  • Вычисленный метр течи:   {alarm.location.distance_from_start:.2f} м от колодца А")
    print(f"  • ГЕО Координаты прорыва:  {alarm.location.coordinate.latitude:.6f}, {alarm.location.coordinate.longitude:.6f}")
    print(f"  • Коэффициент уверенности: {alarm.location.confidence * 100:.1f}%")
    print(f"  • Индекс риска участка:    {risk_report.risk_score:.2f} (Статус: {risk_report.condition.value.upper()})")
    print(f"  • Предписание ТОиР:        {risk_report.recommendation}")
    print("="*65)
    
    print("\nСНИМОК ЦИФРОВОГО ДВОЙНИКА ДЛЯ GIS-КАРТЫ:")
    print(gis_snapshot)
    print("="*65 + "\n")

    logger.info("SYSTEM INTEGRATION TEST: SUCCESS. 100% OPERATIONAL.")

    return {
        "alarm": alarm,
        "prediction": prediction,
        "risk_report": risk_report,
        "digital_twin": gis_snapshot
    }

if __name__ == "__main__":
    run_system_simulation()

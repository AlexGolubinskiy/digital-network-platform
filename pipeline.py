from __future__ import annotations
import uuid
import logging
import sqlite3
import json
import numpy as np
from datetime import datetime
from models import Device, AudioData, Alarm, AlarmLocation, Coordinate, AnalysisResult

logger = logging.getLogger("DigitalNetworkPlatform.Pipeline")

class SignalProcessingPipeline:
    """
    Центральный оркестратор вычислительного конвейера платформы.
    Выполняет фильтрацию, FFT-анализ, GCC-PHAT локализацию и 
    автономно сохраняет инциденты в бесплатную локальную СУБД SQLite.
    """
    def __init__(
        self,
        profile: NetworkProfile,
        dsp_engine,
        analysis_engine,
        localization_engine,
        geo_engine,
        db_path: str = "glavcifra.db",  # Локальный файл базы данных вместо дорогого облака Яндекса
        event_bus=None
    ):
        self.profile = profile
        self.dsp = dsp_engine
        self.analysis = analysis_engine
        self.localization = localization_engine
        self.geo = geo_engine
        self.db_path = db_path
        self.event_bus = event_bus
        
        # Автоматическая инициализация таблиц SQLite при старте конвейера
        self._init_local_db()

    def _init_local_db(self):
        """Создание локальной структуры таблиц без серверов и биллинга."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS local_alarms (
                        alarm_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        network_type TEXT NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        distance_from_start REAL NOT NULL,
                        confidence REAL NOT NULL,
                        anomaly_detected INTEGER NOT NULL,
                        probability REAL NOT NULL,
                        description TEXT,
                        created_at TEXT NOT NULL,
                        status TEXT NOT NULL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Не удалось инициализировать локальную базу SQLite: {e}")

    def _save_alarm_to_sqlite(self, alarm: Alarm):
        """Прямая безопасная запись карточки аварии в локальный файл."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO local_alarms (
                        alarm_id, device_id, network_type, latitude, longitude, 
                        distance_from_start, confidence, anomaly_detected, 
                        probability, description, created_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alarm.alarm_id,
                    alarm.device_id,
                    alarm.network_type.value if hasattr(alarm.network_type, 'value') else str(alarm.network_type),
                    alarm.location.coordinate.latitude,
                    alarm.location.coordinate.longitude,
                    alarm.location.distance_from_start,
                    alarm.location.confidence,
                    1 if alarm.analysis.anomaly_detected else 0,
                    alarm.analysis.probability,
                    alarm.analysis.description,
                    alarm.created_at.isoformat(),
                    alarm.status
                ))
                conn.commit()
            logger.info(f"Аварийное событие {alarm.alarm_id} успешно сохранено в локальный файл {self.db_path}.")
        except Exception as e:
            # ИСПРАВЛЕНИЕ ОШИБКИ ЛОГИРОВАНИЯ: Теперь система никогда не упадет при сбоях БД
            logger.error(f"Ошибка записи аларма в локальную БД: {e}")

    def process(
        self, 
        device_a: Device, 
        device_b: Device, 
        signal_a: np.ndarray, 
        signal_b: np.ndarray, 
        section_length: float
    ) -> Alarm:
        """
        Сквозной расчет акустических параметров утечки, гео-интерполяция по сфере 
        и автономная фиксация инцидента.
        """
        logger.info(
            f"Запуск конвейера обработки сигналов для устройств {device_a.device_id} и {device_b.device_id}"
        )

        # 1. Формирование базовых контейнеров входных сигналов
        audio_a = AudioData(signal=signal_a, sample_rate=self.profile.sample_rate)
        audio_b = AudioData(signal=signal_b, sample_rate=self.profile.sample_rate)

        # 2. Высокопроизводительная фильтрация Баттерворта от городских шумов
        audio_a = self.dsp.bandpass(audio_a)
        audio_b = self.dsp.bandpass(audio_b)

        # 3. Спектральный FFT-анализ и оценка параметров
        analysis_result = self.analysis.analyze(audio_a)

        # 4. Расчет точной временной задержки субдискретным методом GCC-PHAT
        localization_result = self.localization.locate(
            audio_a.signal, 
            audio_b.signal, 
            section_length, 
            self.profile
        )

        # 5. Прецизионная ГЕО-интерполяция метки аварии через Bearing на сфере Земли
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

        # 7. Запись прорыва в бесплатное локальное хранилище СУБД SQLite
        self._save_alarm_to_sqlite(alarm)

        # 8. Публикация сообщения в шину событий (если она инициализирована)
        if self.event_bus:
            try:
                from event_bus import SystemEvent, EventType
                event = SystemEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.ALARM_CREATED,
                    data={"alarm": alarm},
                    timestamp=datetime.now(),
                    source="SignalProcessingPipeline"
                )
                self.event_bus.publish(event)
                logger.info(f"Событие ALARM_CREATED отправлено в EventBus для аларма {alarm.alarm_id}")
            except Exception as e:
                logger.error(f"Ошибка публикации события в EventBus: {e}")

        return alarm

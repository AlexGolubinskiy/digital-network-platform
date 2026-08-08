from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Literal, List, Tuple
from pydantic import BaseModel, Field, field_validator

# =======================================================================
# DIGITAL NETWORK PLATFORM v1.1
# DATA VALIDATION MODELS & AI INFERENCE PIPELINE
# =======================================================================

class PipelineModel(BaseModel):
    """
    Модель валидации трубопровода для ГИС-карты.
    Соответствует структуре таблицы 'network_assets' в schema.sql
    """
    id: UUID | None = None
    pipe_number: str = Field(..., description="Инвентарный/номенклатурный номер трубы в Водоканале")
    material: Literal["STEEL", "CAST_IRON", "HDPE_PLASTIC"] = Field(..., description="Материал трубы")
    diameter_mm: int = Field(..., gt=0, description="Диаметр трубы в миллиметрах")
    length_m: float = Field(..., gt=0, description="Физическая длина участка трубопровода в метрах")
    criticality_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    
    # Геометрия трубы на карте города — список точек для PostGIS LineString: [(lon1, lat1), (lon2, lat2), ...]
    coordinates: List[Tuple[float, float]] = Field(..., min_items=2, description="Массив гео-координат линии трубы")


class AcousticSensorModel(BaseModel):
    """
    Модель валидации физического акустического логгера.
    Соответствует структуре таблицы 'iot_sensors' в schema.sql
    """
    id: UUID | None = None
    device_id: str = Field(..., min_length=3, description="Уникальный заводской ID физического прибора")
    associated_pipe_id: UUID | None = None
    installation_depth_meters: float = Field(0.0, gte=0.0)
    battery_level_voltage: float = Field(..., gt=0.0, description="Контроль вольтажа батареи")
    firmware_version: str = Field(..., description="Версия прошивки логгера")
    
    # Координата установки датчика для PostGIS Point (longitude, latitude)
    location: Tuple[float, float] = Field(..., description="Координаты GPS смотрового колодца")


# -----------------------------------------------------------------------
# ИСПРАВЛЕННЫЙ ИИ-СЛОЙ ДЛЯ СНХРОНИЗАЦИИ С S3 И ЗАЩИТЫ ОТ РЭБ
# -----------------------------------------------------------------------

class TelemetrySignalInput(BaseModel):
    """
    Модель ПРИЕМА данных от датчика (Вход в ИИ-конвейер).
    ИСПРАВЛЕНИЕ: Бинарный payload заменен на строгий путь к аудиофайлу в S3/MinIO.
    """
    device_id: str = Field(..., description="ID физического логгера шума")
    recorded_at: datetime = Field(..., description="Время физической записи сигнала логгером")
    received_at: datetime = Field(default_factory=datetime.now, description="Время фактического приема сервером")
    
    # Первичные DSP-метрики, рассчитанные на граничном устройстве или предобработчике
    rms_amplitude: float = Field(..., gte=0.0, description="Энергия звука в трубе (RMS)")
    crest_factor: float = Field(..., gte=0.0, description="Пик-фактор (характер шума)")
    dominant_frequency: float = Field(..., gte=0.0, lte=22050.0, description="Главная частота свиста утечки в Гц")
    snr_value: float = Field(..., description="Соотношение сигнал/шум в децибелах")
    
    # Путь к аудиофайлу в объектном хранилище (Вместо "бинарного болота" в БД)
    audio_file_s3_path: str = Field(..., description="Ссылка на WAV-файл в S3-хранилище")
    
    # Параметры компенсации РЭБ для LSTM-модели временных рядов (Решение ошибки №2)
    is_delayed_by_uav_attack: bool = Field(False, description="Флаг задержки пакета из-за атаки БПЛА/глушения связи")
    cached_days_count: int = Field(0, gte=0, description="Дней хранения пакета в локальной памяти логгера")
    time_drift_seconds: int = Field(0, description="Смещение внутренних часов датчика относительно GPS в секундах")


class AIModelMetadata(BaseModel):
    """
    Модель для MLOps аудита ИИ-компонентов перед ФСИ.
    """
    model_id: UUID | str = Field(..., description="Идентификатор развернутой ML/DL модели")
    model_name: str = Field(..., description="Архитектура ИИ (например, CNN-Classifier)")
    model_version: str = Field(..., description="Версия весов ИИ-модели")
    inference_time_ms: float = Field(..., description="Скорость работы инференса в миллисекундах")


class AIPredictionOutput(BaseModel):
    """
    Модель ВЫХОДА ИИ-ядра. Решает противоречие таймингов (Ошибка №1).
    """
    # Фиксация режима работы конвейера ИИ
    processing_mode: Literal["BATCH_SCHEDULED", "REALTIME_EMERGENCY"] = "BATCH_SCHEDULED"
    
    # Результаты предсказаний искусственного интеллекта
    leak_detected: bool = False
    confidence_score: float = Field(..., gte=0.0, lte=1.0, description="Индекс уверенности модели (0.0 - 1.0)")
    physical_risk_score: float = Field(..., gte=0.0, lte=1.0, description="Физическая вероятность прорыва")
    final_priority_score: float = Field(..., gte=0.0, lte=1.0, description="Индекс приоритета ремонта (Риск * Ущерб)")
    priority_status: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    automated_recommendation: str = Field(..., description="Автоматическая b2b-директива для подрядчика")
    
    # Метрики высокоточной локализации дефекта (выход core_localization.py)
    calculated_distance_meters: float | None = Field(None, description="Расстояние до свища в метрах")
    confidence_interval_m: float = Field(0.5, description="Погрешность локализации в метрах")
    
    model_info: AIModelMetadata


class SignalRecord(BaseModel):
    """
    Архивная карточка инцидента и результатов предиктивного анализа ИИ.
    Полностью соответствует таблице 'predictive_maintenance_tasks' в schema.sql.
    """
    record_id: UUID = Field(default_factory=uuid4)
    asset_id: UUID = Field(..., description="ID связанного участка трубопровода")
    telemetry_packet_id: UUID | None = Field(None, description="Ссылка на пакет телеметрии")
    
    telemetry: TelemetrySignalInput = Field(..., description="Входные DSP данные")
    ai_analysis: AIPredictionOutput = Field(..., description="Результат анализа ИИ-ядра")
    
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

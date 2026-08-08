from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Literal, List, Tuple
from pydantic import BaseModel, Field, field_validator

# =======================================================================
# DIGITAL NETWORK PLATFORM v1.0
# DATA VALIDATION MODELS
# =======================================================================

class PipelineModel(BaseModel):
    """
    Модель валидации трубопровода для ГИС-карты.
    Соответствует структуре таблицы 'pipelines' в schema.sql
    """
    id: UUID | None = None
    pipe_number: str = Field(..., description="Инвентарный/номенклатурный номер трубы в Водоканале")
    material: Literal["steel", "pnd", "iron", "concrete"] = Field(..., description="Материал трубы (важно для DSP фильтров)")
    diameter_mm: int = Field(..., gt=0, description="Диаметр трубы в миллиметрах (должен быть больше нуля)")
    length_m: float = Field(..., gt=0, description="Физическая длина участка трубопровода в метрах")
    install_year: int = Field(..., gte=1900, description="Год укладки сети (фактор износа)")
    
    # Геометрия трубы на карте города — список точек LineString: [(широта1, долгота1), (широта2, долгота2), ...]
    coordinates: List[Tuple[float, float]] = Field(..., min_items=2, description="Массив гео-координат линии трубы")

    @field_validator('install_year')
    @classmethod
    def validate_year(cls, v: int) -> int:
        current_year = datetime.now().year
        if v > current_year:
            raise ValueError(f"Год укладки не может быть в будущем (максимум {current_year})")
        return v


class AcousticSensorModel(BaseModel):
    """
    Модель валидации физического акустического логгера.
    Соответствует структуре таблицы 'acoustic_sensors' в schema.sql
    """
    id: UUID | None = None
    device_id: str = Field(..., min_length=3, description="Уникальный заводской ID физического прибора")
    status: Literal["active", "maintenance", "offline"] = "active"
    battery_level: int = Field(100, gte=0, lte=100, description="Заряд батареи в процентах")
    associated_pipe_id: UUID | None = None
    
    # Координата установки датчика на карте города (широта, долгота)
    location: Tuple[float, float] = Field(..., description="Координаты GPS смотрового колодца")


class SignalRecord(BaseModel):
    """
    Архивная карточка акустического сигнала и результатов предиктивного анализа.
    Соответствует структуре таблицы 'sensor_telemetry' в schema.sql
    """
    record_id: str = Field(..., description="Уникальный UUID записи замера")
    device_id: str = Field(..., description="ID датчика, приславшего сигнал")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время фиксации сигнала")
    
    # Метрики, рассчитанные вашим приватным DSP-ядром core_analytics.py
    rms_amplitude: float = Field(..., gte=0.0, description="Энергия звука в трубе (RMS)")
    crest_factor: float = Field(..., gte=0.0, description="Пик-фактор (характер шума)")
    dominant_frequency: float = Field(..., gte=0.0, lte=22050.0, description="Главная частота свиста утечки в Гц")
    snr_db: float = Field(..., description="Соотношение сигнал/шум в децибелах")
    
    # Результат работы предиктивного искусственного интеллекта
    leak_probability: float = Field(..., gte=0.0, lte=100.0, description="Вероятность скорого появления свища (0-100%)")
    file_path: str = Field("emulated.wav", description="Путь к аудиофайлу для верификации")

    class Config:
        from_attributes = True

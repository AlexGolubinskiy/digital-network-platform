from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Literal, List, Tuple
from pydantic import BaseModel, Field, field_validator

# =======================================================================
# DIGITAL NETWORK PLATFORM v1.0
# DATA VALIDATION MODELS & AI INFERENCE PIPELINE
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


# -----------------------------------------------------------------------
# НОВЫЙ ИИ-СЛОЙ ДЛЯ СТРУКТУРИРОВАНИЯ КОНВЕЙЕРА ДАННЫХ ДЛЯ ФСИ
# -----------------------------------------------------------------------

class TelemetrySignalInput(BaseModel):
    """
    Модель ПРИЕМА сырых/первичных данных от датчика (Вход в ИИ-конвейер).
    Датчик передает физические метрики, извлеченные на контроллере.
    """
    device_id: str = Field(..., description="ID физического логгера шума")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Первичные DSP-метрики, извлеченные вашим приватным DSP-ядром
    rms_amplitude: float = Field(..., gte=0.0, description="Энергия звука в трубе (RMS)")
    crest_factor: float = Field(..., gte=0.0, description="Пик-фактор (характер шума)")
    dominant_frequency: float = Field(..., gte=0.0, lte=22050.0, description="Главная частота свиста утечки в Гц")
    snr_db: float = Field(..., description="Соотношение сигнал/шум в децибелах")
    
    # Ссылка на бинарный вектор или аудиофайл для глубокого анализа в dsp.py внутри Prediction Engine
    raw_signal_chunk: List[float] | None = Field(None, description="Вектор амплитуд сырого аудио для CNN/STFT")


class AIModelMetadata(BaseModel):
    """
    Архитектурная модель для аудита ИИ-компонентов.
    Фиксирует, какая именно модель и в какой версии приняла решение в продакшене.
    """
    model_id: UUID | str = Field(..., description="Идентификатор развернутой ML/DL модели в реестре моделей")
    model_name: Literal["Acoustic-CNN-Classifier", "Pipeline-XGBoost-Predictor", "Ensemble-Cascade"] = Field(..., description="Архитектура ИИ")
    model_version: str = Field(..., description="Версия весов ИИ-модели (например, v1.2.4-prod)")
    inference_time_ms: float = Field(..., description="Скорость работы инференса на CPU/GPU в миллисекундах")


class AIPredictionOutput(BaseModel):
    """
    Модель ВЫХОДА ИИ-ядра (Результат работы Prediction/Localization Engine).
    """
    leak_probability: float = Field(..., gte=0.0, lte=100.0, description="Вероятность скорого появления свища (0-100%)")
    anomaly_score: float = Field(..., gte=0.0, lte=1.0, description="Индекс аномальности сигнала (Unsupervised Outlier Detection)")
    
    # Метрики высокоточной локализации дефекта (выход core_localization.py)
    estimated_distance_m: float | None = Field(None, description="Расстояние до свища от датчика А в метрах")
    confidence_interval_m: float | None = Field(0.5, description="Погрешность локализации (точность, например ±0.5м)")
    
    # Ссылка на метаданные ИИ-модели, сделавшей расчет
    model_info: AIModelMetadata


class SignalRecord(BaseModel):
    """
    Архивная карточка акустического сигнала и результатов предиктивного анализа.
    Соответствует структуре таблицы 'sensor_telemetry' в schema.sql.
    Объединяет вход датчика и ответ ИИ для отображения на веб-карте.
    """
    record_id: UUID = Field(..., description="Уникальный UUID записи замера в БД")
    telemetry: TelemetrySignalInput = Field(..., description="Входящие телеметрические и DSP данные")
    ai_analysis: AIPredictionOutput = Field(..., description="Результат предиктивного анализа ИИ-ядра")
    processed_at: datetime = Field(default_factory=datetime.now, description="Время завершения ИИ-анализа на сервере")
    file_path: str = Field("stored_signals/active.wav", description="Путь к аудиофайлу в хранилище для верификации")

    class Config:
        from_attributes = True

"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

REST API LAYER (FastAPI) - SERVER PRODUCTION VERSION

Промышленный сетевой интерфейс для интеграции с течеискателями АТЭК.
=======================================================================
"""

from __future__ import annotations
import uuid
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np

# Импортируем готовые инфраструктурные модули платформы
from config import HEAT_PROFILE, init_directories
from models import Coordinate, Device, SensorType, NetworkType
from database import Database
from event_bus import EventBus
from dsp import DSPEngine
from analysis import AnalysisEngine
from localization import LocalizationEngine
from geo import GeoEngine
from pipeline import SignalProcessingPipeline

# Настраиваем логирование серверных транзакций
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("DigitalNetworkPlatform.API")

# Инициализируем FastAPI приложение
app = FastAPI(
    title="Digital Network Platform API",
    description="Промышленный REST API автоматизированного течеискания АТЭК",
    version="1.0.0"
)

# Разворачиваем рабочую структуру папок при старте веб-сервера
init_directories()

# Глобальные синглтоны ядра платформы
database = Database()
event_bus = EventBus()
profile = HEAT_PROFILE

# Сборка и оркестрация вычислительного конвейера обработки сигналов
pipeline = SignalProcessingPipeline(
    profile=profile,
    dsp_engine=DSPEngine(profile),
    analysis_engine=AnalysisEngine(profile),
    localization_engine=LocalizationEngine(),
    geo_engine=GeoEngine(),
    database=database,
    event_bus=event_bus
)

# Строгая валидация входящего JSON-пакета данных телеметрии от приборов АТЭК
class TelemetryRequest(BaseModel):
    device_id_a: str = Field(..., description="ID датчика в Колодце А")
    lat_a: float = Field(..., description="Широта Колодца А")
    lon_a: float = Field(..., description="Долгота Колодца А")
    
    device_id_b: str = Field(..., description="ID датчика в Колодце Б")
    lat_b: float = Field(..., description="Широта Колодца Б")
    lon_b: float = Field(..., description="Долгота Колодца Б")
    
    signal_a: list[float] = Field(..., description="Массив амплитуд звуковой волны датчика А")
    signal_b: list[float] = Field(..., description="Массив амплитуд звуковой волны датчика Б")

@app.get("/api/v1/health")
def health_check():
    """Диагностический эндпоинт проверки статуса доступности веб-сервера."""
    return {
        "status": "green", 
        "version": "1.0.0", 
        "network_profile": profile.name,
        "active_sensors_supported": ["acoustic", "pressure"]
    }

@app.post("/api/v1/analyze")
def analyze_telemetry(payload: TelemetryRequest):
    """
    REST API эндпоинт сквозного расчета параметров утечки теплоносителя.
    Принимает ГЕО-координаты колодцев и массивы звука, возвращает точный метр течи.
    """
    logger.info("Получен сетевой запрос на анализ от датчиков %s и %s", payload.device_id_a, payload.device_id_b)
    
    try:
        # 1. Восстанавливаем объекты устройств из прилетевших ГЕО-координат
        device_a = Device(
            device_id=payload.device_id_a,
            name=f"Колодец {payload.device_id_a}",
            sensor_type=SensorType.ACOUSTIC,
            coordinate=Coordinate(latitude=payload.lat_a, longitude=payload.lon_a),
            network_type=NetworkType.HEAT
        )
        
        device_b = Device(
            device_id=payload.device_id_b,
            name=f"Колодец {payload.device_id_b}",
            sensor_type=SensorType.ACOUSTIC,
            coordinate=Coordinate(latitude=payload.lat_b, longitude=payload.lon_b),
            network_type=NetworkType.HEAT
        )
        
        # Конвертируем JSON-списки в высокопроизводительные массивы NumPy float64
        arr_a = np.array(payload.signal_a, dtype=np.float64)
        arr_b = np.array(payload.signal_b, dtype=np.float64)
        
        # Вычисляем точную физическую длину трубы между колодцами по Haversine
        geo_tool = GeoEngine()
        section_length = geo_tool.distance(device_a.coordinate, device_b.coordinate)
        
        # 2. Запускаем последовательную обработку по нашему математическому конвейеру
        alarm = pipeline.process(device_a, device_b, arr_a, arr_b, section_length)
        
        logger.info("Обработка завершена успешно. ID Тревоги: %s", alarm.alarm_id)
        
        # 3. Формируем структурированный ответ для диспетчерского пульта АТЭК
        return {
            "success": True,
            "alarm_id": alarm.alarm_id,
            "anomaly_detected": alarm.analysis.anomaly_detected,
            "probability": float(alarm.analysis.probability),
            "leak_location": {
                "distance_from_sensor_a_meters": float(alarm.location.distance_from_start),
                "latitude": float(alarm.location.coordinate.latitude),
                "longitude": float(alarm.location.coordinate.longitude),
                "confidence": float(alarm.location.confidence)
            },
            "pipe_section": {
                "total_length_meters": float(section_length)
            }
        }
        
    except Exception as error:
        logger.error("Критический сбой при вычислении параметров утечки: %s", error)
        raise HTTPException(status_code=500, detail=f"Internal server computational error: {str(error)}")

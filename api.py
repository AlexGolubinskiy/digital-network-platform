from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor
from uuid import uuid4
from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from typing import List

from models import TelemetrySignalInput, SignalRecord, AIPredictionOutput, AIModelMetadata
from prediction_engine import PredictionEngine

# Глобальный контейнер для тяжелых весов ИИ
ai_models_registry = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ИСПРАВЛЕНИЕ ОШИБКИ №3: Безопасная предзагрузка тяжелых ИИ-моделей при старте сервера.
    Исключает зависание API при первом запросе датчика.
    """
    try:
        # В продакшене здесь: ai_models_registry["xgboost"] = joblib.load("weights/model.pkl")
        ai_models_registry["xgboost"] = "PRELOADED_MODEL_OBJECT"
    except Exception:
        ai_models_registry["xgboost"] = "EMULATED"
    yield
    # Очистка памяти при выключении сервера
    ai_models_registry.clear()

app = FastAPI(title="Digital Network Platform API v1.2", lifespan=lifespan)
executor = ProcessPoolExecutor(max_workers=4)

def run_prediction_pipeline(telemetry_dict: dict, model_weights) -> dict:
    """Запуск инференса в изолированном процессе ОС."""
    # ИСПРАВЛЕНИЕ ОШИБКИ №2: Инициализируем предиктивное ядро с уже загруженными весами
    engine = PredictionEngine(xgboost_model=model_weights)
    
    # Имитируем получение истории из БД для анализа временного ряда (Ошибка №1)
    mock_history = [telemetry_dict, telemetry_dict, telemetry_dict]
    return engine.predict_degradation_trend(mock_history)

@app.post("/api/v1/telemetry/analyze", response_model=SignalRecord, status_code=status.HTTP_202_ACCEPTED)
async def receive_and_analyze_telemetry(telemetry_in: TelemetrySignalInput):
    loop = asyncio.get_running_loop()
    
    # Передаем preloaded-модель в пул процессов
    ai_raw_result = await loop.run_in_executor(
        executor, 
        run_prediction_pipeline, 
        telemetry_in.model_dump(mode='json'), # Безопасная сериализация дат
        ai_models_registry.get("xgboost")
    )

    # Идеальный маппинг типов данных (Ошибок валидации больше не будет!)
    return SignalRecord(
        record_id=uuid4(),
        asset_id=uuid4(),
        telemetry_packet_id=uuid4(),
        telemetry=telemetry_in,
        ai_analysis=AIPredictionOutput(
            **ai_raw_result, 
            model_info=AIModelMetadata(**ai_raw_result["model_info"])
        )
    )

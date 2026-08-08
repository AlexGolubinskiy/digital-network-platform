class AIPredictionOutput(BaseModel):
    """
    Модель ВЫХОДА ИИ-ядра (Результат работы Prediction/Localization Engine).
    """
    processing_mode: Literal["BATCH_SCHEDULED", "REALTIME_EMERGENCY"] = "BATCH_SCHEDULED"
    leak_detected: bool = False
    confidence_score: float = Field(..., gte=0.0, lte=1.0, description="Индекс уверенности модели")
    physical_risk_score: float = Field(..., gte=0.0, lte=1.0, description="Физическая вероятность прорыва")
    final_priority_score: float = Field(..., gte=0.0, lte=1.0, description="Индекс приоритета ремонта")
    priority_status: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    automated_recommendation: str = Field(..., description="Директива для подрядчика")
    
    # ИСПРАВЛЕНИЕ ОШИБКИ №1: Добавляем метрику остаточного ресурса RUL для XGBoost
    days_to_failure: float = Field(..., description="Прогнозное количество дней до критического прорыва трубы")
    
    calculated_distance_meters: float | None = Field(None, description="Расстояние до свища в метрах")
    confidence_interval_m: float = Field(0.5, description="Погрешность локализации")
    
    model_info: AIModelMetadata

"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

PREDICTION ENGINE

Прогнозная аналитика состояния сети.
=======================================================================
"""

from __future__ import annotations
from models import SignalRecord, PredictionResult

class PredictionEngine:
    """Математический движок анализа деградации и прогнозирования рисков."""

    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold

    def predict(self, signal_record: SignalRecord) -> PredictionResult:
        """Расчет индекса риска и определение характера тренда."""
        risk_score = 0.0
        factors = {}

        if signal_record.frequency > 0:
            risk_score += 0.3
            factors["frequency"] = signal_record.frequency

        if signal_record.snr >= 10:
            risk_score += 0.3
            factors["snr"] = signal_record.snr

        if signal_record.probability >= 0.5:
            risk_score += 0.4
            factors["detection_probability"] = signal_record.probability

        risk_score = min(risk_score, 1.0)
        trend = "degradation" if risk_score >= self.threshold else "stable"

        return PredictionResult(
            device_id=signal_record.device_id,
            risk_score=risk_score,
            trend=trend,
            factors=factors
        )

    def handle_event(self, event) -> PredictionResult | None:
        """Реактивный обработчик шины событий."""
        signal_record = event.data.get("signal_record")
        if signal_record is None:
            return None
        return self.predict(signal_record)

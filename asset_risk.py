"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

ASSET RISK ENGINE

Оценка технического состояния участков сети.

Вход: NetworkAsset + PredictionResult
Выход: AssetRiskResult
=======================================================================
"""

from __future__ import annotations
from models import NetworkAsset, PredictionResult, AssetRiskResult, AssetCondition

class AssetRiskEngine:
    """Экспертный аналитический движок оценки износа и комплексного риска аварийности трубопроводов."""

    def evaluate(self, asset: NetworkAsset, prediction: PredictionResult) -> AssetRiskResult:
        """Комплексный расчет индекса риска с учетом возраста трубы и акустического прогноза деградации."""
        risk_score = prediction.risk_score
        factors = dict(prediction.factors)

        # Расчет фактора старения и усталости металла/пластика
        current_year = 2026
        age = current_year - asset.installation_year
        factors["asset_age"] = age

        if age > 40:
            risk_score += 0.15
        elif age > 25:
            risk_score += 0.05

        risk_score = min(risk_score, 1.0)

        # Интеллектуальная классификация текущего статуса физического состояния
        if risk_score >= 0.8:
            condition = AssetCondition.CRITICAL
            recommendation = "Emergency inspection required"
        elif risk_score >= 0.5:
            condition = AssetCondition.AGING
            recommendation = "Schedule preventive maintenance"
        else:
            condition = AssetCondition.NORMAL
            recommendation = "Continue monitoring"

        return AssetRiskResult(
            asset_id=asset.asset_id,
            risk_score=risk_score,
            condition=condition,
            factors=factors,
            recommendation=recommendation
        )

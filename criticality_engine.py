from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict
from models import NetworkAsset, AssetRiskResult, AssetCondition

class EconomicImpactLevel(Enum):
    """Уровень финансовых и социальных последствий аварии."""
    LOW = 0.1         # Пустырь, авария не влияет на бизнес
    MEDIUM = 0.3      # Второстепенный склад, простой некритичен
    HIGH = 0.6        # Магистраль к котельной цеха, возможна остановка
    CRITICAL = 1.0    # Причал порта АО 'НЛЭ', больница (убытки > 1 млн/день)

@dataclass
class PrioritizedTask:
    """Модель задачи ремонта, ранжированная по экономическому приоритету."""
    task_id: str
    asset_id: str
    asset_name: str
    physical_risk: float        # Физический риск износа (из AssetRiskEngine)
    economic_impact: float     # Коэффициент ущерба (EconomicImpactLevel)
    final_priority_score: float # Итоговый индекс важности для Мэра/Директора
    recommendation: str

class CapitalOptimizationEngine:
    """Аналитический движок оптимизации бюджетов ТОиР при дефиците средств."""
    
    def __init__(self):
        self.meta_impact_registry: Dict[str, EconomicImpactLevel] = {}

    def register_asset_criticality(self, asset_id: str, impact_level: EconomicImpactLevel):
        """Ручная или автоматическая привязка уровня важности к паспорту трубы."""
        self.meta_impact_registry[asset_id] = impact_level

    def calculate_priority(self, asset: NetworkAsset, risk_result: AssetRiskResult) -> PrioritizedTask:
        """Расчет сквозного индекса приоритета на основе физики и экономики."""
        # Получаем уровень ущерба (по умолчанию MEDIUM, если не задан)
        impact = self.meta_impact_registry.get(asset.asset_id, EconomicImpactLevel.MEDIUM)
        
        # ГРААЛЬ ИДЕИ: Перемножаем физический риск на экономический ущерб
        # Даже если износ трубы средний (0.5), но это причал НЛЭ (1.0), приоритет будет выше (0.5),
        # чем у полностью гнилой трубы (0.9) на пустыре с ущербом (0.1), где приоритет составит всего 0.09.
        final_score = risk_result.risk_score * impact.value
        
        # Формируем жесткую b2b-рекомендацию для генерального директора
        if final_score >= 0.7:
            rec = "КРИТИЧЕСКИЙ ПРИОРИТЕТ. Ремонт в течение 48 часов для предотвращения простоя активов."
        elif final_score >= 0.4:
            rec = "ВЫСОКИЙ ПРИОРИТЕТ. Включить в план финансирования на текущий месяц."
        elif final_score >= 0.15:
            rec = "СРЕДНИЙ ПРИОРИТЕТ. Плановый ремонт при наличии избытка бюджета."
        else:
            rec = "НИЗКИЙ ПРИОРИТЕТ. Перенести ремонт на следующий финансовый период."
            
        return PrioritizedTask(
            task_id=str(uuid.uuid4()),
            asset_id=asset.asset_id,
            asset_name=asset.name,
            physical_risk=risk_result.risk_score,
            economic_impact=impact.value,
            final_priority_score=final_score,
            recommendation=rec
        )

    def optimize_budget(self, tasks: List[PrioritizedTask], limit_budget_units: int) -> List[PrioritizedTask]:
        """Ранжирование всех дефектов города/порта сверху вниз по уровню угрозы бюджету."""
        # Сортируем задачи от самых экономически опасных к безопасным
        tasks.sort(key=lambda x: x.final_priority_score, reverse=True)
        # Возвращаем только топ задач, которые влезают в минимальный бюджет
        return tasks[:limit_budget_units]

"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

DIGITAL TWIN ENGINE

Цифровой двойник инженерных сетей.

Функции:
- регистрация участков сети;
- обновление риска;
- получение текущего состояния;
- подготовка данных для GIS.
=======================================================================
"""

from __future__ import annotations
from datetime import datetime
from models import NetworkAsset, AssetRiskResult

class DigitalTwinEngine:
    """Ядро цифрового двойника городской инфраструктуры ЖКХ."""

    def __init__(self):
        self.assets = {}

    def register_asset(self, asset: NetworkAsset):
        """Регистрация физического участка сети в оперативной памяти цифрового двойника."""
        self.assets[asset.asset_id] = {
            "asset": asset,
            "risk": None,
            "updated_at": None
        }

    def update_risk(self, risk_result: AssetRiskResult) -> bool:
        """Обновление динамического статуса износа, рисков аварийности и предписаний ТОиР."""
        asset_data = self.assets.get(risk_result.asset_id)
        if asset_data is None:
            return False

        asset_data["risk"] = risk_result
        asset_data["updated_at"] = datetime.now()
        return True

    def get_asset(self, asset_id: str) -> dict | None:
        """Получение полной динамической карточки участка сети."""
        return self.assets.get(asset_id)

    def get_snapshot(self) -> list[dict]:
        """Формирование комплексного сериализуемого среза состояния всей инфраструктуры города для ГИС-карты."""
        snapshot = []

        for asset_id, data in self.assets.items():
            asset = data["asset"]
            risk = data["risk"]

            item = {
                "asset_id": asset.asset_id,
                "name": asset.name,
                "length": asset.length,
                "material": asset.material.value,
                "risk_score": None,
                "condition": "unknown",
                "recommendation": None
            }

            if risk:
                item["risk_score"] = risk.risk_score
                item["condition"] = risk.condition.value
                item["recommendation"] = risk.recommendation

            snapshot.append(item)

        return snapshot

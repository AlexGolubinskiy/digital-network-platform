"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

GEO ENGINE

Географический слой платформы.

Функции:
- расчет расстояния между датчиками;
- вычисление точки аварии;
- проверка GPS координат.

Все модели находятся в models.py.
=======================================================================
"""

from __future__ import annotations
import math
from models import Coordinate

class GeoEngine:
    """Географический модуль платформы для точного анализа ГИС-координат инженерных сетей."""

    EARTH_RADIUS = 6371000

    @staticmethod
    def distance(point_a: Coordinate, point_b: Coordinate) -> float:
        """Расчет расстояния между GPS точками по формуле Haversine в метрах."""
        lat1 = math.radians(point_a.latitude)
        lat2 = math.radians(point_b.latitude)
        delta_lat = math.radians(point_b.latitude - point_a.latitude)
        delta_lon = math.radians(point_b.longitude - point_a.longitude)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return GeoEngine.EARTH_RADIUS * c

    @staticmethod
    def interpolate_point(point_a: Coordinate, point_b: Coordinate, distance_to_leak: float, section_length: float) -> Coordinate:
        """Определение точной координаты аварии между двумя датчиками с защитой ГИС-границ."""
        if section_length <= 0:
            return point_a

        ratio = distance_to_leak / section_length
        ratio = max(0.0, min(ratio, 1.0))

        latitude = point_a.latitude + (point_b.latitude - point_a.latitude) * ratio
        longitude = point_a.longitude + (point_b.longitude - point_a.longitude) * ratio
        altitude = point_a.altitude + (point_b.altitude - point_a.altitude) * ratio

        return Coordinate(latitude=latitude, longitude=longitude, altitude=altitude)

    @staticmethod
    def interpolate(point_a: Coordinate, point_b: Coordinate, distance_to_leak: float, section_length: float) -> Coordinate:
        """Метод-адаптер для обеспечения полной совместимости с логикой SignalProcessingPipeline."""
        return GeoEngine.interpolate_point(point_a, point_b, distance_to_leak, section_length)

    @staticmethod
    def validate(point: Coordinate) -> bool:
        """Проверка физической корректности GPS-координат."""
        if not (-90 <= point.latitude <= 90):
            return False
        if not (-180 <= point.longitude <= 180):
            return False
        return True

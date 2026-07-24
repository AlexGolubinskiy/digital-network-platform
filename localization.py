"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

LOCALIZATION ENGINE

GCC-PHAT акустическая локализация.

Функции:
- расчет задержки между датчиками;
- вычисление расстояния до аварии;
- подготовка результата для Pipeline.

Все модели находятся в models.py.
=======================================================================
"""

from __future__ import annotations
import numpy as np
from config import NetworkProfile
from models import LocalizationResult

class GCCPhat:
    """Алгоритм обобщенной взаимной корреляции с фазовым преобразованием (GCC-PHAT)."""

    @staticmethod
    def estimate_delay(signal_a: np.ndarray, signal_b: np.ndarray, sample_rate: int) -> float:
        """Расчет временной задержки методом GCC-PHAT с параболической субсэмпловой интерполяцией."""
        n = max(len(signal_a), len(signal_b))

        fft_a = np.fft.rfft(signal_a, n=n)
        fft_b = np.fft.rfft(signal_b, n=n)

        cross_power = fft_b * np.conj(fft_a)

        magnitude = np.abs(cross_power)
        magnitude[magnitude == 0] = 1e-12
        cross_power /= magnitude

        correlation = np.fft.irfft(cross_power, n=n)
        shift = int(np.argmax(correlation))

        left_index = (shift - 1) % n
        right_index = (shift + 1) % n

        y_left = correlation[left_index]
        y_center = correlation[shift]
        y_right = correlation[right_index]

        denominator = 2 * y_center - y_left - y_right
        correction = 0.0

        if denominator != 0:
            correction = (y_right - y_left) / (2 * denominator)

        refined_shift = shift + correction

        if refined_shift > n / 2:
            refined_shift -= n

        return float(refined_shift / sample_rate)

class LocalizationEngine:
    """Математический движок определения физического расстояния до утечки теплоносителя."""

    def locate(self, signal_a: np.ndarray, signal_b: np.ndarray, section_length: float, profile: NetworkProfile) -> LocalizationResult:
        """Расчет задержки распространения волны и ГЕО-дистанции до места прорыва."""
        delay = GCCPhat.estimate_delay(signal_a, signal_b, profile.sample_rate)
        distance = (section_length - abs(delay * profile.sound_velocity)) / 2
        
        distance = max(0.0, min(distance, section_length))

        max_delay = section_length / profile.sound_velocity
        if max_delay <= 0:
            confidence = 0.0
        else:
            confidence = 1.0 - (abs(delay) / max_delay)

        confidence = max(0.0, min(confidence, 1.0))

        return LocalizationResult(
            delay_seconds=delay,
            distance_to_leak=distance,
            valid=True,
            confidence=confidence
        )

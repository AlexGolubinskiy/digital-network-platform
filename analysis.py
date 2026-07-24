"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

ANALYSIS ENGINE

Интеллектуальный анализ акустических сигналов.
=======================================================================
"""

from __future__ import annotations
import numpy as np
from scipy.fft import fft, fftfreq
from config import NetworkProfile
from models import AudioData, AnalysisResult

class AnalysisEngine:
    """Профильно-ориентированный аналитический движок частотного спектра и оценки шумов."""

    def __init__(self, profile: NetworkProfile):
        self.profile = profile

    def calculate_spectrum(self, signal: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
        """Расчет одностороннего вещественного амплитудного спектра сигнала (FFT)."""
        size = len(signal)
        spectrum = np.abs(fft(signal))
        frequencies = fftfreq(size, 1 / sample_rate)
        positive = frequencies >= 0
        return frequencies[positive], spectrum[positive]

    @staticmethod
    def dominant_frequency(frequencies: np.ndarray, spectrum: np.ndarray) -> float:
        """Поиск частотной координаты максимального спектрального пика."""
        if len(spectrum) == 0:
            return 0.0
        index = np.argmax(spectrum)
        return float(frequencies[index])

    @staticmethod
    def signal_energy(signal: np.ndarray) -> float:
        """Расчет суммарной энергии сигнала во временной области."""
        return float(np.sum(signal ** 2))

    @staticmethod
    def calculate_snr(spectrum: np.ndarray) -> float:
        """Расчет отношения сигнал/шум (SNR) в децибелах относительно 25-го процентиля шума."""
        if len(spectrum) == 0:
            return 0.0
        signal_level = np.max(spectrum)
        noise_level = np.percentile(spectrum, 25)

        if noise_level <= 0:
            return 0.0
        return float(20 * np.log10(signal_level / noise_level))

    def calculate_probability(self, frequency: float, snr: float) -> float:
        """Математический расчет вероятности наличия дефекта на основе критериев профиля сети."""
        probability = 0.0
        if self.profile.frequency_min <= frequency <= self.profile.frequency_max:
            probability += 0.5
        if snr >= self.profile.snr_threshold:
            probability += 0.5
        return min(probability, 1.0)

    def analyze(self, audio: AudioData) -> AnalysisResult:
        """Полный сквозной анализ спектральных признаков и формирование карточки верификации."""
        frequencies, spectrum = self.calculate_spectrum(audio.signal, audio.sample_rate)
        frequency = self.dominant_frequency(frequencies, spectrum)
        energy = self.signal_energy(audio.signal)
        snr = self.calculate_snr(spectrum)
        probability = self.calculate_probability(frequency, snr)

        return AnalysisResult(
            anomaly_detected=(probability >= 0.7),
            probability=probability,
            description="Acoustic anomaly" if probability >= 0.7 else "Signal normal",
            parameters={
                "dominant_frequency": frequency,
                "energy": energy,
                "snr": snr,
                "network": self.profile.name,
                "frequency_band": [self.profile.frequency_min, self.profile.frequency_max]
            }
        )

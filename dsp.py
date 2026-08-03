from __future__ import annotations
from pathlib import Path
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.io import wavfile
from models import AudioData
from config import NetworkProfile

class DSPEngine:
    """Движок цифровой обработки сигналов на основе профилей инженерных сетей."""

    def __init__(self, profile: NetworkProfile):
        self.profile = profile

    @staticmethod
    def normalize(signal: np.ndarray) -> np.ndarray:
        """Нормализация амплитуды акустического сигнала в диапазон [-1.0, 1.0]."""
        maximum = np.max(np.abs(signal))
        if maximum == 0:
            return signal
        return signal / maximum

    def load_wav(self, file_path: str | Path) -> AudioData:
        """Загрузка WAV файла с диска, декодирование и приведение к моно-формату float64."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Аудиофайл не найден: {path}")

        sample_rate, data = wavfile.read(path)
        signal = data.astype(np.float64)

        if len(signal.shape) > 1:
            signal = signal[:, 0]

        signal = self.normalize(signal)
        duration = len(signal) / sample_rate

        return AudioData(
            signal=signal,
            sample_rate=sample_rate,
            duration=duration
        )

    def bandpass(self, audio: AudioData) -> AudioData:
        """Полосовой фильтр Баттерворта 4-го порядка с автоматической защитой Найквиста."""
        nyquist = audio.sample_rate / 2
        low = self.profile.frequency_min
        high = self.profile.frequency_max

        # Математическая защита от выхода частот среза за физический предел
        high = min(high, nyquist * 0.99)
        low = max(low, 1.0)

        if low >= high:
            raise ValueError(f"Invalid filter range: {low}-{high} Hz for sample rate {audio.sample_rate}")

        low_norm = low / nyquist
        high_norm = high / nyquist

        b, a = butter(4, [low_norm, high_norm], btype="bandpass")
        filtered = filtfilt(b, a, audio.signal)

        # Модифицируем сигнал прямо внутри существующего контейнера данных (In-place)
        audio.signal = filtered
        return audio

class GCCPhat:
    """Математическое ядро обобщенной взаимной корреляции (Generalized Cross-Correlation)."""

    @staticmethod
    def estimate_delay(signal1: np.ndarray, signal2: np.ndarray, sample_rate: int) -> float:
        """Расчет временной задержки между двумя сигналами с параболической интерполяцией субдискретного пика."""
        n = max(signal1.size, signal2.size)
        
        # Перевод сигналов в частотную область
        fft1 = np.fft.rfft(signal1, n=n)
        fft2 = np.fft.rfft(signal2, n=n)
        
        # Вычисление взаимного спектра мощности
        cross_power = fft2 * np.conj(fft1)
        magnitude = np.abs(cross_power)
        
        # Защита от деления на ноль
        magnitude[magnitude == 0] = 1e-12
        cross_power /= magnitude
        
        # Возврат во временную область (функция взаимной корреляции)
        correlation = np.fft.irfft(cross_power, n=n)
        shift = int(np.argmax(correlation))
        
        # Квадратичная (параболическая) интерполяция вершины пика для повышения точности
        left_index = (shift - 1) % n
        right_index = (shift + 1) % n
        y_left, y_center, y_right = correlation[left_index], correlation[shift], correlation[right_index]
        
        denominator = 2 * y_center - y_left - y_right
        correction = (y_right - y_left) / (2 * denominator) if denominator != 0 else 0.0
        refined_shift = shift + correction
        
        # Коррекция циклического сдвига
        if refined_shift > n / 2:
            refined_shift -= n
            
        return float(refined_shift / sample_rate)

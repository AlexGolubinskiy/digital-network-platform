"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

SIGNAL EMULATOR

Генератор тестовых сигналов утечки.

Используется только для:
- проверки Pipeline;
- нагрузочного тестирования;
- демонстрации MVP.
=======================================================================
"""

from __future__ import annotations
import uuid
import numpy as np
from datetime import datetime
from models import SignalRecord

def generate_leak_signal(duration: float, sample_rate: int, frequency: float = 800.0, noise_level: float = 0.2) -> np.ndarray:
    """Генерация искусственного акустического сигнала утечки (гармоника + белый шум)."""
    samples = int(duration * sample_rate)
    time = np.linspace(0, duration, samples)
    
    signal = np.sin(2 * np.pi * frequency * time)
    noise = np.random.normal(0, noise_level, samples)

    return signal + noise

def create_signal_record(device_id: str, frequency: float, snr: float, probability: float) -> SignalRecord:
    """Формирование фиктивной архивной карточки сигнала для тестирования предиктивных трендов."""
    return SignalRecord(
        record_id=str(uuid.uuid4()),
        device_id=device_id,
        timestamp=datetime.now(),
        frequency=frequency,
        snr=snr,
        probability=probability,
        file_path="emulated.wav"
    )

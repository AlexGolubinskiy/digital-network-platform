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

def create_signal_record(
    device_id: str, 
    rms_amplitude: float, 
    crest_factor: float, 
    dominant_frequency: float, 
    snr_db: float, 
    leak_probability: float
) -> SignalRecord:
    """
    Формирование архивной карточки сигнала для тестирования предиктивных трендов.
    Полностью синхронизировано с Pydantic-моделью SignalRecord.
    """
    return SignalRecord(
        record_id=str(uuid.uuid4()),
        device_id=device_id,
        timestamp=datetime.now(),
        rms_amplitude=rms_amplitude,
        crest_factor=crest_factor,
        dominant_frequency=dominant_frequency,
        snr_db=snr_db,
        leak_probability=leak_probability,
        file_path="emulated.wav"
    )

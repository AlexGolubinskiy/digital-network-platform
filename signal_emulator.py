"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0
SIGNAL EMULATOR
Генератор реалистичных виброакустических сигналов утечки КИИ.
Используется для сквозной валидации Pipeline, нагрузочных тестов и MVP.
=======================================================================
"""
from __future__ import annotations
import uuid
import numpy as np
from datetime import datetime
from models import SignalRecord, AudioData
from config import NetworkProfile

def generate_synchronized_leak_signals(
    section_length: float,
    leak_distance: float,
    profile: NetworkProfile,
    duration: float = 2.0,
    base_frequency: float = 650.0,
    ambient_noise_level: float = 0.25
) -> tuple[np.ndarray, np.ndarray]:
    """
    Генерация пары синхронизированных по фазе акустических сигналов (Датчик А и Б)
    с учетом времени добегания волны (TDOA) и затухания амплитуды в металле/пластике.
    
    :param section_length: Общая длина участка трубы между колодцами (метры)
    :param leak_distance: Истинное расстояние от датчика А до свища (метры)
    :param profile: Профиль сети (содержит sample_rate и sound_velocity)
    :param duration: Длительность записи сигнала в секундах
    :param base_frequency: Доминирующая частота шума струи свища (Гц)
    :param ambient_noise_level: Амплитуда фонового шума земли/городской среды
    """
    fs = profile.sample_rate
    v_sound = profile.sound_velocity
    samples = int(duration * fs)
    time_vector = np.linspace(0, duration, samples, endpoint=False)
    
    # 1. Расчет физических дистанций от свища до каждого из датчиков
    distance_to_a = leak_distance
    distance_to_b = section_length - leak_distance
    
    # 2. Вычисление точного времени задержки (в секундах) добегания звука
    time_delay_a = distance_to_a / v_sound
    time_delay_b = distance_to_b / v_sound
    
    # 3. Моделирование затухания звука в гетерогенной среде (экспоненциальный закон)
    # Коэффициент затухания зависит от структуры сети (в MVP берем усредненный 0.05)
    attenuation_a = np.exp(-0.03 * distance_to_a)
    attenuation_b = np.exp(-0.03 * distance_to_b)
    
    # 4. Генерация сдвинутых по фазе сигналов (свист струи под давлением + гармоника)
    # Датчик А
    t_a = time_vector - time_delay_a
    signal_a = attenuation_a * (np.sin(2 * np.pi * base_frequency * t_a) + 
                                0.3 * np.sin(2 * np.pi * (base_frequency * 2) * t_a))
    
    # Датчик Б
    t_b = time_vector - time_delay_b
    signal_b = attenuation_b * (np.sin(2 * np.pi * base_frequency * t_b) + 
                                0.3 * np.sin(2 * np.pi * (base_frequency * 2) * t_b))
    
    # Обрезаем возможные артефакты отрицательного времени эмуляции начала процесса
    signal_a[time_vector < time_delay_a] = 0.0
    signal_b[time_vector < time_delay_b] = 0.0
    
    # 5. Наложение независимого белого шума грунта (городские и индустриальные помехи)
    noise_a = np.random.normal(0, ambient_noise_level, samples)
    noise_b = np.random.normal(0, ambient_noise_level, samples)
    
    final_signal_a = signal_a + noise_a
    final_signal_b = signal_b + noise_b
    
    # Пиковая нормализация для соответствия контракту данных DSP-движка
    def _normalize(sig: np.ndarray) -> np.ndarray:
        max_val = np.max(np.abs(sig))
        return sig if max_val == 0 else sig / max_val

    return _normalize(final_signal_a), _normalize(final_signal_b)


def create_signal_record(device_id: str, frequency: float, snr: float, probability: float) -> SignalRecord:
    """
    Формирование архивной карточки лога сигнала телеметрии датчика.
    Полностью совместима со строгими Pydantic-моделями FastAPI и движком PredictionEngine.
    """
    return SignalRecord(
        record_id=str(uuid.uuid4()),
        device_id=device_id,
        timestamp=datetime.now(),
        frequency=round(float(frequency), 1),
        snr=round(float(snr), 2),
        probability=round(float(probability), 2),
        file_path=f"signals/emulated_{uuid.uuid4().hex[:8]}.wav",
        metadata={
            "emulated_record": True,
            "generator_version": "v1.0-synced",
            "environment_mode": "urban_industrial_noise"
        }
    )

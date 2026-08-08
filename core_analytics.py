from __future__ import annotations
import numpy as np
from scipy.signal import butter, lfilter

def _butter_bandpass(lowcut: float, highcut: float, fs: float, order: int = 5):
    """Генерация коэффициентов фильтра Баттерворта для полосовой фильтрации."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def filter_pipe_noise(data: np.ndarray, pipe_material: str, fs: float = 44100) -> np.ndarray:
    """Фильтрация акустического сигнала под конкретный материал трубы (Патентная логика)."""
    if pipe_material.lower() in ['steel', 'сталь', 'iron', 'чугун']:
        lowcut, highcut = 800.0, 2500.0
    elif pipe_material.lower() in ['pnd', 'пнд', 'plastic', 'пластик']:
        lowcut, highcut = 50.0, 450.0
    else:
        lowcut, highcut = 100.0, 1500.0
        
    b, a = _butter_bandpass(lowcut, highcut, fs, order=4)
    return lfilter(b, a, data)

def extract_signal_features(signal: np.ndarray) -> dict:
    """Извлечение математических признаков (фич) из отфильтрованного сигнала."""
    rms = np.sqrt(np.mean(signal**2))
    peak = np.max(np.abs(signal))
    crest_factor = peak / rms if rms > 0 else 0
    
    fft_vals = np.abs(np.fft.rfft(signal))
    fft_freqs = np.fft.rfftfreq(len(signal), d=1/44100)
    dom_freq = fft_freqs[np.argmax(fft_vals)]
    
    return {
        "rms": float(rms),
        "crest_factor": float(crest_factor),
        "dominant_frequency": float(dom_freq)
    }

def predict_leak_probability(historical_features: list[dict]) -> float:
    """Предиктивный расчет вероятности появления свища по временному ряду признаков."""
    if len(historical_features) < 3:
        return 0.0
        
    rms_trend = [f['rms'] for f in historical_features]
    crest_trend = [f['crest_factor'] for f in historical_features]
    rms_velocity = np.diff(rms_trend)
    
    is_rms_growing = np.all(rms_velocity > 0)
    recent_growth_rate = rms_trend[-1] / rms_trend[-3] if rms_trend[-3] > 0 else 1.0
    is_sound_stable = crest_trend[-1] < crest_trend[-3] and crest_trend[-1] < 3.5

    probability = 0.0
    if is_rms_growing:
        probability += 40.0
    if is_sound_stable:
        probability += 25.0
    if recent_growth_rate > 1.2:
        probability += min(35.0, (recent_growth_rate - 1.0) * 50)
        
    return round(float(np.clip(probability, 0.0, 100.0)), 2)

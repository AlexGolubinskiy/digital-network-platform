from __future__ import annotations
import numpy as np

def calculate_leak_distance(signal_a: np.ndarray, signal_b: np.ndarray, 
                            pipe_length: float, pipe_material: str, 
                            fs: float = 44100) -> float:
    """
    Расчет точного расстояния до свища от датчика А методом взаимной корреляции.
    Включает патентную корректировку скорости звука в зависимости от среды.
    """
    # Патентная таблица скоростей распространения волны (звука) в трубах с водой
    # Скорость зависит от жесткости материала (в пластике звук идет значительно медленнее)
    if pipe_material.lower() in ['steel', 'сталь', 'iron', 'чугун']:
        v_sound = 1250.0  # м/с в стальной трубе
    elif pipe_material.lower() in ['pnd', 'пнд', 'plastic', 'пластик']:
        v_sound = 450.0   # м/с в пластиковой трубе
    else:
        v_sound = 1000.0  # среднее значение по умолчанию
        
    # Вычисляем взаимную корреляцию двух сигналов
    correlation = np.correlate(signal_a - np.mean(signal_a), signal_b - np.mean(signal_b), mode='full')
    
    # Находим индекс максимального совпадения (пик корреляции)
    delay_samples = np.argmax(correlation) - (len(signal_a) - 1)
    
    # Переводим задержку из семплов в секунды
    time_delay = delay_samples / fs
    
    # Формула локализации утечки:
    # L_a = (Pipe_Length + (Time_Delay * V_Sound)) / 2
    distance_from_a = (pipe_length + (time_delay * v_sound)) / 2.0
    
    # Защита от выхода за границы физической трубы из-за шумов
    return round(float(np.clip(distance_from_a, 0.0, pipe_length)), 2)

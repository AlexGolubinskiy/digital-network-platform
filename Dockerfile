# Шаг 1: Используем официальный легковесный образ Python
FROM python:3.10-slim

# Шаг 2: Устанавливаем системные зависимости для компиляции SciPy/NumPy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Шаг 3: Настраиваем рабочую директорию внутри контейнера
WORKDIR /app

# Шаг 4: Обновляем pip и устанавливаем зависимости проекта
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Шаг 5: Копируем весь открытый код MVP в контейнер
COPY . .

# Шаг 6: Запускаем приложение через модуль python со строгим указанием пути к uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

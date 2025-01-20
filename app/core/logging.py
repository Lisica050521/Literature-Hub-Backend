import logging

# Создаем объект логгера
logger = logging.getLogger(__name__)

# Устанавливаем уровень логирования
logger.setLevel(logging.INFO)

# Создаем обработчик для записи логов в файл
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)

# Создаем формат для вывода логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавляем обработчик в логгер
logger.addHandler(file_handler)

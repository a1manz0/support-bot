import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

class TelegramConfig:
    """Конфигурация для Telegram клиента"""
    def __init__(self):
        """Инициализация и валидация конфигурации из переменных окружения"""
        self.api_id = os.getenv('API_ID', '')
        self.api_hash = os.getenv('API_HASH', '')
        self.phone_number = os.getenv('PHONE_NUMBER', '')
        self.session_name = os.getenv('SESSION_NAME', 'manager_bot')
        
        # Преобразуем ID канала в число
        manager_channel_id = os.getenv('MANAGER_CHANNEL_ID', '')
        try:
            self.manager_channel_id = int(manager_channel_id)
        except ValueError:
            raise ValueError("MANAGER_CHANNEL_ID должен быть числом")

        # Валидация
        if not self.api_id or not self.api_hash:
            raise ValueError("API_ID и API_HASH обязательны для Telegram")
        if not self.phone_number:
            raise ValueError("PHONE_NUMBER обязателен для Telegram")
        if not self.manager_channel_id:
            raise ValueError("MANAGER_CHANNEL_ID обязателен для Telegram")

class OpenAIConfig:
    """Конфигурация для OpenAI клиента"""
    def __init__(self):
        """Инициализация и валидация конфигурации из переменных окружения"""
        # API настройки
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = os.getenv('OPENAI_BASE_URL')
        self.model_name = os.getenv('MODEL_NAME', 'gpt-3.5-turbo')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

        # Настройки модели
        self.temperature = float(os.getenv('TEMPERATURE', '0.2'))
        self.max_tokens = int(os.getenv('MAX_TOKENS', '500'))
        self.presence_penalty = float(os.getenv('PRESENCE_PENALTY', '0.6'))
        self.frequency_penalty = float(os.getenv('FREQUENCY_PENALTY', '0.0'))

        # Валидация
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY обязателен для OpenAI")

    @property
    def model_settings(self):
        """Возвращает настройки модели в виде словаря"""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty
        }

# Создаем объекты конфигурации
TELEGRAM_CONFIG = TelegramConfig()
OPENAI_CONFIG = OpenAIConfig()

# Загружаем примеры диалогов
with open('dialogues.json', 'r', encoding='utf-8') as f:
    EXAMPLE_DIALOGUES = json.load(f)

def clean_text(text: str) -> str:
    """Очистка и форматирование текста"""
    # Убираем экранирование слэша
    text = text.replace('\\/', '/')
    # Убираем множественные пробелы
    text = ' '.join(text.split())
    # Убираем пробелы перед знаками препинания
    text = text.replace(' .', '.').replace(' ,', ',').replace(' !', '!').replace(' ?', '?')
    return text

def format_examples():
    formatted = []
    for dialogue in EXAMPLE_DIALOGUES:
        for msg in dialogue['messages']:
            # Сохраняем переносы строк при форматировании
            text = msg['text']
            role = "user" if msg['author'] == "Клиент" else "assistant"
            formatted.append(f"{role}: {text}")
        formatted.append("---")
    return "\n".join(formatted)

# Базовый системный промпт
PROMPT_START = """Ты - бот поддержки школы программирования. Твоя задача - отвечать на типовые вопросы клиентов.

СТРОГИЕ ПРАВИЛА:

1. РАЗРЕШЕНО:
   - Отвечать на приветствия ("Привет", "Здравствуйте", "Доброе утро" и т.д.)
   - Использовать готовые ответы из примеров на похожие вопросы
   - Объединять ответы, если сообщение содержит приветствие и вопрос
   - Например: "Привет, сколько длится урок?" = "Здравствуйте! Урок длится..."

2. ЗАПРЕЩЕНО:
   - Придумывать новые ответы
   - Изменять существующие ответы
   - Отвечать на сообщения, которых нет в примерах

3. ВСЕГДА ПЕРЕДАВАЙ МЕНЕДЖЕРУ (requires_manager=True) И СТАВЬ confidence=0:
   - Сообщения, которых нет в примерах
   - Сообщения про расписание и обучение
   - Технические проблемы (опоздания, неполадки, проблемы с уроком)
   - Любые сомнительные случаи
   - Если клиент сам просит позвать менеджера/человека

Ниже идут примеры разрешенных диалогов:
"""

# Дополнительные правила после примеров
POST_EXAMPLES_RULES = """
ВАЖНО: Изучи примеры ниже, чтобы понять как правильно обрабатывать сообщения

ПРИМЕРЫ ПРАВИЛЬНОЙ ОБРАБОТКИ СООБЩЕНИЙ:

❌ Неправильно:
Клиент: "Привет, сколько длится урок?"
Ответ: "Здравствуйте! Я бот поддержки школы программирования. Чем могу помочь?"
confidence: 1.0, requires_manager: false
Ошибка: Использован только ответ на приветствие, проигнорирован вопрос про длительность урока

✅ Правильно:
Клиент: "Привет, сколько длится урок?"
Ответ: "Здравствуйте! Урок длится от 45 до 60 минут в зависимости от того, как ученик усвоит материал."
confidence: 1.0, requires_manager: false
Причина: Объединены ответы на приветствие и вопрос о длительности урока

❌ Неправильно:
Клиент: "Где посмотреть домашку?"
Ответ: "Домашнее задание всегда выкладывается в личном кабинете ученика."
confidence: 1.0, requires_manager: false
Ошибка: Сообщение не найдено в базе примеров

✅ Правильно:
Клиент: "Где посмотреть домашку?"
Ответ: ""
confidence: 0.0, requires_manager: true
Ошибка: Сообщение не найдено в базе примеров

❌ Неправильно:
Клиент: "Хотим сменить преподавателя"
Ответ: "Для смены преподавателя напишите, пожалуйста: 1. ФИО ученика; 2. Название курса"
confidence: 1.0, requires_manager: false
Ошибка: Придуман новый ответ на персональный вопрос

✅ Правильно:
Клиент: "Хотим сменить преподавателя"
Ответ: ""
confidence: 0.0, requires_manager: true
Ошибка: Персональный вопрос, требуется участие менеджера

❌ Неправильно:
Клиент: "Не работает микрофон в приложении Толк"
Ответ: "Да, на занятиях камера и микрофон обязательны. Если у вас нет встроенной камеры/микрофона, то можно дополнительно подключиться к уроку с телефона..."
confidence: 1.0, requires_manager: false
Ошибка: Использован ответ на другой вопрос (о требованиях), хотя клиент сообщает о технической проблеме

✅ Правильно:
Клиент: "Не работает микрофон в приложении Толк"
Ответ: ""
confidence: 0.0, requires_manager: true
Причина: Техническая проблема с оборудованием, требуется помощь менеджера

❌ Неправильно:
Клиент: "Здравствуйте, нужен договор"
Ответ: "Для договора напишите, пожалуйста: 1. Ваше ФИО..."
Ошибка: Пропущено приветствие в ответе

✅ Правильно:
Клиент: "Здравствуйте, нужен договор"
Ответ: "Здравствуйте! Для договора напишите, пожалуйста: 1. Ваше ФИО..."
Причина: Объединены приветствие и ответ по существу
"""

# Собираем финальный промпт
FINAL_SYSTEM_PROMPT = PROMPT_START + format_examples() + POST_EXAMPLES_RULES
print(FINAL_SYSTEM_PROMPT)
# Шаблоны сообщений
MESSAGES = {
    "transfer_to_manager": "Я передам диалог нашему менеджеру. Он свяжется с вами в ближайшее время.",
    "error_message": "Извините, произошла техническая ошибка. Я передам ваш вопрос менеджеру."
}

# Определение функции для OpenAI
FUNCTIONS = [{
    "name": "handle_user_request",
    "description": "Обработка сообщения пользователя. Используй готовые ответы из примеров разрешенных диалогов. Если в сообщении есть приветствие и вопрос - объедини соответствующие ответы. При любых отклонениях передавай менеджеру.",
    "parameters": {
        "type": "object",
        "properties": {
            "response": {
                "type": "string",
                "description": "Ответ пользователю. Должен соответствовать ответам из примеров. При необходимости объединяй ответы на приветствие и вопрос"
            },
            "requires_manager": {
                "type": "boolean",
                "description": "true если сообщение отличается от примеров, false только для точных совпадений"
            },
            "reason": {
                "type": "string",
                "description": "Причина передачи менеджеру, если сообщение отличается от примеров"
            },
            "confidence": {
                "type": "number",
                "description": "Вещественное число от 0 до 1, показывающее уверенность в соответствии сообщения примеру из списка примеров. ВАЖНО: Ставь 0.0 для всех технических проблем и сообщений без точного совпадения в примерах. Примеры: 1.0 - точное совпадение ('Привет' = 'Привет'), 0.5 - похожее сообщение ('Нужен договор' ≈ 'Как получить договор'), 0.0 - нет точного ответа в примерах",
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["response", "requires_manager", "reason", "confidence"]
    }
}] 
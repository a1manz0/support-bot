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
        self.api_key = os.getenv('OPENAI_API_KEY', '')
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
    # Заменяем переносы строк
    text = text.replace('\n', '\\n')
    # Убираем множественные пробелы
    text = ' '.join(text.split())
    # Убираем пробелы перед знаками препинания
    text = text.replace(' .', '.').replace(' ,', ',').replace(' !', '!').replace(' ?', '?')
    return text

def format_examples():
    formatted = []
    for dialogue in EXAMPLE_DIALOGUES:
        for msg in dialogue['messages']:
            text = clean_text(msg['text'])
            # Меняем "Клиент" на "user" и "Менеджер" на "assistant"
            role = "user" if msg['author'] == "Клиент" else "assistant"
            formatted.append(f"{role}: {text}")
        formatted.append("---")
    return "\n".join(formatted)

# Базовый системный промпт
PROMPT_START = """Ты - бот поддержки в школе программирования для детей, созданный чтобы отвечать только на вопросы из примеров ниже.

СТРОГИЕ ПРАВИЛА:
1. Используй ответы assistant ТОЛЬКО если вопрос клиента есть в примере
2. Для ВСЕХ остальных вопросов верни requires_manager=True с пустым ответом

Ниже идут примеры разрешенных диалогов:
"""

# Дополнительные правила после примеров
POST_EXAMPLES_RULES = """

ВАЖНО: 
1. Используй ответы assistant ТОЛЬКО если вопрос клиента есть в примере
2. Для технических вопросов верни requires_manager=True с пустым ответом
3. НЕ ПРИДУМЫВАЙ НОВЫЕ ОТВЕТЫ, используй только ответы из примеров
4. При любых сомнениях верни requires_manager=True с пустым ответом
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
    "description": "Обработка запроса пользователя. Используй ТОЛЬКО готовые ответы из примеров разрешенных диалогов. При любых отклонениях передавай менеджеру.",
    "parameters": {
        "type": "object",
        "properties": {
            "response": {
                "type": "string",
                "description": "Ответ пользователю. Должен точно соответствовать одному из ответов в списке примеров"
            },
            "requires_manager": {
                "type": "boolean",
                "description": "true если вопрос отличается от примеров, false только для точных совпадений"
            },
            "reason": {
                "type": "string",
                "description": "Причина передачи менеджеру, если вопрос отличается от примеров"
            }
        },
        "required": ["response", "requires_manager", "reason"]
    }
}] 
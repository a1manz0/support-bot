import os
import json
import logging
from telethon import TelegramClient, events
from dotenv import load_dotenv
from gpt_client import GPTClient
from config import (
    FINAL_SYSTEM_PROMPT, 
    MESSAGES,
    TELEGRAM_CONFIG,
    OPENAI_CONFIG,
    FUNCTIONS
)


# Настройка логирования
print("Starting bot initialization...")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)
print("Logging configured")

# Загрузка переменных окружения
print("Loading environment variables...")
load_dotenv()


# Инициализация клиентов
print("Initializing Telegram client...")
client = TelegramClient(
    TELEGRAM_CONFIG.session_name,
    TELEGRAM_CONFIG.api_id,
    TELEGRAM_CONFIG.api_hash
)
print("Telegram client initialized")


gpt_client = GPTClient()
print("Initializing GPT client...")

# Хранение контекста диалогов
dialogue_contexts = {}

async def notify_manager(user_id: int, message: str, reason: str):
    """Уведомление менеджера о необходимости вмешательства"""
    try:
        # Получаем информацию о пользователе
        user = await client.get_entity(user_id)
        
        # Создаем ссылку на чат
        if user.username:
            chat_link = f"https://t.me/{user.username}"
        else:
            chat_link = f"tg://user?id={user_id}"
            
        manager_message = (
            f"❗️ Требуется внимание менеджера\n"
            f"👤 ID пользователя: {user_id}\n"
            f"👤 Имя: {user.first_name} {user.last_name if user.last_name else ''}\n"
            f"🔗 [Перейти в диалог с клиентом]({chat_link})\n"
            f"💬 Сообщение: {message}\n"
            f"📝 Причина: {reason}"
        )
        
        # Используем ID канала из конфига
        await client.send_message(
            TELEGRAM_CONFIG.manager_channel_id,  # Используем число из конфига
            manager_message,
            parse_mode='md',
            link_preview=False
        )
    except Exception as e:
        logger.error(f"Failed to notify manager: {str(e)}")
        # Добавим больше информации для отладки
        logger.error(f"Channel ID: {TELEGRAM_CONFIG.manager_channel_id}")
        logger.error(f"Message: {manager_message}")

@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    """Обработка входящих сообщений"""
    if event.is_private:  # Только личные сообщения
        user_id = event.sender_id
        message = event.message.text

        # Получаем или создаем контекст диалога
        if user_id not in dialogue_contexts:
            dialogue_contexts[user_id] = []

        # Добавляем сообщение в контекст
        dialogue_contexts[user_id].append({
            "is_user": True,
            "text": message
        })

        # Получаем ответ от AI
        response_data = await gpt_client.get_response(
            message, 
            dialogue_contexts[user_id]
        )
        print('requires_manager', response_data["requires_manager"])
        print('response', response_data["response"])

        # Проверяем необходимость передачи менеджеру
        if response_data["requires_manager"]:
            await event.respond(MESSAGES["transfer_to_manager"])
            await notify_manager(
                user_id,
                message,
                response_data["reason"]
            )
        else:
            # Используем HTML-форматирование для переносов строк
            formatted_response = response_data["response"].replace('\\n', '<br>')
            await event.respond(
                formatted_response,
                parse_mode='html'
            )
            
            # Добавляем ответ бота в контекст
            dialogue_contexts[user_id].append({
                "is_user": False,
                "text": response_data["response"]
            })

        # Очистка старого контекста
        if len(dialogue_contexts[user_id]) > 6:
            dialogue_contexts[user_id] = dialogue_contexts[user_id][-6:]

async def main():
    """Запуск бота"""
    try:
        print("Starting main execution...")
        print("Starting Telegram client...")
        await client.start(phone=TELEGRAM_CONFIG.phone_number)
        print("Telegram client started successfully")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        logger.error(f"Main execution error: {str(e)}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 
import os
import json
import logging
from telethon import TelegramClient, events
from openai import AsyncOpenAI
from dotenv import load_dotenv
from config import (
    FINAL_SYSTEM_PROMPT, 
    MESSAGES,
    TELEGRAM_CONFIG,
    OPENAI_CONFIG,
    FUNCTIONS
)


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()


# Инициализация клиентов
client = TelegramClient(
    TELEGRAM_CONFIG.session_name,
    TELEGRAM_CONFIG.api_id,
    TELEGRAM_CONFIG.api_hash
)



openai_client = AsyncOpenAI(
    api_key=OPENAI_CONFIG.api_key,
    base_url=OPENAI_CONFIG.base_url
)

# Хранение контекста диалогов
dialogue_contexts = {}

async def get_ai_response(message: str, context: list = None) -> dict:
    """
    Получает ответ от GPT на сообщение пользователя используя Function Calling.

    Args:
        message (str): Текст сообщения от пользователя
        context (list, optional): Список предыдущих сообщений для контекста

    Returns:
        dict: Структурированный ответ с полями:
            - response (str): Текст ответа для пользователя
            - requires_manager (bool): Нужно ли передать диалог менеджеру
            - reason (str): Причина передачи менеджеру
    """
    try:
        print('обработка ai response')
        
        # Формируем список сообщений для отправки в API
        messages = [
            {"role": "system", "content": FINAL_SYSTEM_PROMPT}
        ]
        
        # Добавляем контекст предыдущих сообщений
        if context:
            for msg in context[-5:]:
                messages.append({
                    "role": "user" if msg["is_user"] else "assistant",
                    "content": msg["text"]
                })
        
        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": message})

        # Отправляем запрос к API с указанием функции
        response = await openai_client.chat.completions.create(
            model=OPENAI_CONFIG.model_name,
            messages=messages,
            functions=FUNCTIONS,
            function_call={"name": "handle_user_request"},  # Принудительно вызываем функцию
            **OPENAI_CONFIG.model_settings
        )

        # Получаем результат вызова функции
        function_call = response.choices[0].message.function_call
        
        if function_call and function_call.name == "handle_user_request":
            # Парсим аргументы функции
            try:
                args = json.loads(function_call.arguments)
                return {
                    "response": args.get("response", ""),
                    "requires_manager": args.get("requires_manager", True),
                    "reason": args.get("reason", "")
                }
            except json.JSONDecodeError:
                logger.error(f"Failed to parse function arguments: {function_call.arguments}")
                return {
                    "response": MESSAGES["error_message"],
                    "requires_manager": True,
                    "reason": "Ошибка парсинга ответа модели"
                }
        else:
            logger.error("No function call in response")
            return {
                "response": MESSAGES["error_message"],
                "requires_manager": True,
                "reason": "Неожиданный формат ответа"
            }

    except Exception as e:
        logger.error(f"Error in get_ai_response: {str(e)}")
        return {
            "response": MESSAGES["error_message"],
            "requires_manager": True,
            "reason": f"Техническая ошибка: {str(e)}"
        }

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
        response_data = await get_ai_response(
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
            await event.respond(response_data["response"])
            
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
        await client.start(phone=TELEGRAM_CONFIG.phone_number)
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 
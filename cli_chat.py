from bot import get_ai_response
from openai import AsyncOpenAI
from config import OPENAI_CONFIG
import json
import asyncio
import tracemalloc

tracemalloc.start()

openai_client = AsyncOpenAI(
    api_key=OPENAI_CONFIG.api_key,
    base_url=OPENAI_CONFIG.base_url if OPENAI_CONFIG.base_url else None
)

async def test_chat():
    # Тестовый вопрос
    question = input("Введите вопрос: ")
    
    # Получаем ответ от бота
    response = await get_ai_response(question)
    
    print(f"\nВопрос: {question}")
    print(f"Ответ: {response}")
    
    # Проверяем, что получен непустой ответ
    assert response is not None
    assert "response" in response
    assert len(response["response"]) > 0

if __name__ == "__main__":
    asyncio.run(test_chat())
from bot import get_ai_response
from openai import AsyncOpenAI
from config import OPENAI_CONFIG
import json
import asyncio
import tracemalloc
import tiktoken

tracemalloc.start()

openai_client = AsyncOpenAI(
    api_key=OPENAI_CONFIG.api_key,
    base_url=OPENAI_CONFIG.base_url if OPENAI_CONFIG.base_url else None
)

# Хранилище контекста диалога

async def test_chat():
    dialogue_context = []
    while True:
        # Тестовый вопрос
        question = input("\nВведите вопрос (или 'exit' для выхода): ")
        
        if question.lower() == 'exit':
            break
            
        # Добавляем вопрос в контекст
        dialogue_context.append({
            "is_user": True,
            "text": question
        })
        
        # Получаем ответ от бота с учетом контекста
        response = await get_ai_response(question, dialogue_context)
        
        print(f"\nВопрос: {question}")
        print(f"Ответ: {response}")
        
        # Добавляем ответ бота в контекст
        dialogue_context.append({
            "is_user": False,
            "text": response["response"]
        })
        
        # Ограничиваем размер контекста
        if len(dialogue_context) > 6:
            dialogue_context = dialogue_context[-6:]
        
        # Проверяем, что получен непустой ответ
        assert response is not None
        assert "response" in response

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Подсчет токенов в тексте"""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Подсчет токенов в системном промпте
from config import FINAL_SYSTEM_PROMPT
tokens = count_tokens(FINAL_SYSTEM_PROMPT)
print(f"Токенов в системном промпте: {tokens}")

if __name__ == "__main__":
    asyncio.run(test_chat())
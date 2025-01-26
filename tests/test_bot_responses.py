import pytest
import asyncio
import json
import numpy as np
from bot import get_ai_response
from openai import AsyncOpenAI
from config import OPENAI_CONFIG

# Загружаем диалоги из JSON
with open('dialogues.json', 'r', encoding='utf-8') as f:
    dialogues = json.load(f)

# Формируем стандартные вопросы из диалогов
standard_questions = [
    {
        "question": dialogue["messages"][0]["text"],  # Вопрос клиента
        "expected_response": dialogue["messages"][1]["text"]  # Ответ менеджера
    }
    for dialogue in dialogues
]

# Минимальный порог схожести ответов (в процентах)
SIMILARITY_THRESHOLD = 90

# Инициализация клиента OpenAI
openai_client = AsyncOpenAI(
    api_key=OPENAI_CONFIG.api_key,
    base_url=OPENAI_CONFIG.base_url if OPENAI_CONFIG.base_url else None
)

async def get_embedding(text: str) -> list:
    """Получает embedding для текста используя OpenAI API"""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def cosine_similarity(v1: list, v2: list) -> float:
    """Вычисляет косинусное сходство между векторами"""
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    return dot_product / (norm1 * norm2) * 100  # Переводим в проценты

async def responses_are_similar(response1: str, response2: str) -> bool:
    """
    Проверяет семантическую схожесть двух ответов используя embeddings
    
    Args:
        response1: Первый ответ
        response2: Второй ответ
        
    Returns:
        bool: True если ответы достаточно похожи
    """
    # Получаем embeddings для обоих ответов
    emb1 = await get_embedding(response1)
    emb2 = await get_embedding(response2)
    
    # Вычисляем косинусное сходство
    similarity = cosine_similarity(emb1, emb2)
    
    print(f"\nСхожесть ответов: {similarity}%")
    print(f"Ответ 1: {response1}")
    print(f"Ответ 2: {response2}")
    return similarity >= SIMILARITY_THRESHOLD

# Тестовые данные
TEST_CASES = {
    "standard_questions": standard_questions,
    "crm_questions": [
        "Когда следующее занятие у Пети?",
        "Сколько у нас осталось оплаченных уроков?",
        "В какой группе учится мой ребенок?",
        "Можно узнать расписание нашей группы?"
    ],
    "personal_questions": [
        "Можно перенести завтрашнее занятие?",
        "Хотим сменить преподавателя",
        "Можно ли получить скидку?",
        "У ребенка особенности развития, как построить обучение?"
    ],
    "technical_issues": [
        "Преподаватель опаздывает на урок",
        "Не работает микрофон в приложении Толк",
        "Ребенок не успевает за группой",
        "Можно ли учиться по индивидуальной программе?"
    ],
    "incomplete_questions": [
        "Когда занятие?",
        "Где посмотреть домашку?",
        "Почему не работает?",
        "Как зайти?"
    ],
    "manager_requests": [
        "Соедините с менеджером пожалуйста",
        "Хочу поговорить с человеком",
        "Нужна консультация менеджера",
        "Позовите менеджера"
    ]
}

@pytest.mark.asyncio
class TestBotResponses:
    """Тесты ответов бота"""
    
    async def test_standard_questions(self):
        """Тест стандартных вопросов"""
        for case in TEST_CASES["standard_questions"]:
            print(f"\nТестируем вопрос: {case['question']}")
            response = await get_ai_response(case["question"])
            print(f"Получен ответ: {response}")
            
            assert response["requires_manager"] is False, \
                f"Бот передал менеджеру стандартный вопрос: {case['question']}"
            
            assert responses_are_similar(response["response"], case["expected_response"]), \
                f"Ответ не соответствует ожидаемому:\n" \
                f"Вопрос: {case['question']}\n" \
                f"Ожидалось: {case['expected_response']}\n" \
                f"Получено: {response['response']}"

    async def test_crm_questions(self):
        """Тест вопросов требующих CRM"""
        for question in TEST_CASES["crm_questions"]:
            print(f"\nТестируем вопрос: {question}")
            response = await get_ai_response(question)
            print(f"Получен ответ: {response}")
            assert response["requires_manager"] is True, f"Бот не передал менеджеру CRM вопрос: {question}"
            # assert response["response"] == "", f"Ответ должен быть пустым для вопроса: {question}"

    async def test_personal_questions(self):
        """Тест персонализированных вопросов"""
        for question in TEST_CASES["personal_questions"]:
            print(f"\nТестируем вопрос: {question}")
            response = await get_ai_response(question)
            print(f"Получен ответ: {response}")
            assert response["requires_manager"] is True, f"Бот не передал менеджеру персональный вопрос: {question}"
            #assert response["response"] == "", f"Ответ должен быть пустым для вопроса: {question}"

    async def test_technical_issues(self):
        """Тест технических проблем"""
        for question in TEST_CASES["technical_issues"]:
            print(f"\nТестируем вопрос: {question}")
            response = await get_ai_response(question)
            print(f"Получен ответ: {response}")
            assert response["requires_manager"] is True, f"Бот не передал менеджеру технический вопрос: {question}"
            # assert response["response"] == "", f"Ответ должен быть пустым для вопроса: {question}"

    async def test_incomplete_questions(self):
        """Тест неполных вопросов"""
        for question in TEST_CASES["incomplete_questions"]:
            print(f"\nТестируем вопрос: {question}")
            response = await get_ai_response(question)
            print(f"Получен ответ: {response}")
            assert response["requires_manager"] is True, f"Бот не передал менеджеру неполный вопрос: {question}"
            #assert response["response"] == "", f"Ответ должен быть пустым для вопроса: {question}"

    async def test_manager_requests(self):
        """Тест прямых запросов менеджера"""
        for question in TEST_CASES["manager_requests"]:
            print(f"\nТестируем вопрос: {question}")
            response = await get_ai_response(question)
            print(f"Получен ответ: {response}")
            assert response["requires_manager"] is True, f"Бот не передал менеджеру прямой запрос: {question}"
            #assert response["response"] == "", f"Ответ должен быть пустым для вопроса: {question}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
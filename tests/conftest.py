import os
import sys
import pytest

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Устанавливаем область видимости event loop для асинхронных фикстур
pytest.ini_options = {
    "asyncio_mode": "auto",
    "asyncio_default_fixture_loop_scope": "function"
}

@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всех тестов"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 
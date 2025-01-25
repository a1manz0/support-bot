# AI Support Bot

Telegram бот на базе GPT для автоматизации работы менеджеров.
- Отвечает на стандартные вопросы из базы знаний
- Передает нестандартные вопросы менеджеру
- Обрабатывает технические проблемы

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/a1manz0/support-bot.git
```
2. Установите зависимости:
```bash
pip install -r requirements.txt
```
3. Создайте файл .env и добавьте переменные окружения:
```
TELEGRAM_TOKEN=your_telegram_token
OPENAI_API_KEY=your_openai_key
```

## Тестирование

Проект включает автоматические тесты для проверки корректности ответов бота.

### Запуск тестов

```bash
pytest tests/ -v -s
```

3. Создать файл .env и заполнить необходимые переменные:
```
API_ID=''
API_HASH=''
PHONE_NUMBER=''
OPENAI_API_KEY=''
MANAGER_CHANNEL_ID=''
SESSION_NAME='manager_bot'
MODEL_NAME='gpt-3.5-turbo'
```

## Запуск через Docker

1. Соберите образ:
```bash
docker-compose build
```

2. Запустите контейнер:
```bash
docker-compose up -d
```

3. Просмотр логов:
```bash
docker-compose logs -f
```

4. Остановка:
```bash
docker-compose down
```

## Структура проекта

- `bot.py` - основной файл бота
- `config.py` - конфигурация и системный промпт
- `dialogues.json` - примеры диалогов для обучения

## Процесс разработки

1. Создайте новую ветку для вашей задачи:
```bash
git checkout -b feature/название-задачи
```

2. Внесите необходимые изменения и закоммитьте их:
```bash
git add .
git commit -m "Описание изменений"
```

3. Отправьте изменения в репозиторий:
```bash
git push origin feature/название-задачи
```

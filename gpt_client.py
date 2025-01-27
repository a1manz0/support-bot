import json
from openai import AsyncOpenAI
from config import OPENAI_CONFIG, FINAL_SYSTEM_PROMPT, FUNCTIONS
import tiktoken

class GPTClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=OPENAI_CONFIG.api_key,
            base_url=OPENAI_CONFIG.base_url if OPENAI_CONFIG.base_url else None
        )

    async def get_response(self, message: str, context: list = None) -> dict:
        """
        Получает ответ от GPT на сообщение пользователя.
        
        Args:
            message (str): Текст сообщения
            context (list, optional): Список предыдущих сообщений
            
        Returns:
            dict: Структурированный ответ
        """
        try:
            messages = [
                {"role": "system", "content": FINAL_SYSTEM_PROMPT}
            ]
            
            if context:
                for msg in context[-5:]:
                    messages.append({
                        "role": "user" if msg["is_user"] else "assistant",
                        "content": msg["text"]
                    })
            
            messages.append({"role": "user", "content": message})

            response = await self.client.chat.completions.create(
                model=OPENAI_CONFIG.model_name,
                messages=messages,
                functions=FUNCTIONS,
                function_call={"name": "handle_user_request"},
                **OPENAI_CONFIG.model_settings
            )

            function_call = response.choices[0].message.function_call
            result = json.loads(function_call.arguments.replace('\\/', '/'))
            
            if result['confidence'] < 0.8 and not result['requires_manager']:
                result['requires_manager'] = True
                result['reason'] = f"Низкая уверенность в ответе ({result['confidence']})"
                result['response'] = ""
            
            return result

        except Exception as e:
            return {
                "response": "Произошла ошибка при обработке запроса.",
                "requires_manager": True,
                "reason": f"Ошибка: {str(e)}",
                "confidence": 0.0
            }

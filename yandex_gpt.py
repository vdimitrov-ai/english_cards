import json
import logging
import os
from copy import deepcopy

import dotenv
import requests

# Загружаем переменные окружения
dotenv.load_dotenv()

# Проверяем наличие необходимых переменных
catalog_id = os.getenv("catalog_id")
secret_key = os.getenv("secret_key")
system_prompt = os.getenv(
    "system_prompt",
    "Вы - помощник по английскому языку. Отвечайте на вопросы пользователя о грамматике, произношении и использовании слов.",
)

# Проверка обязательных переменных
if not catalog_id or not secret_key:
    raise EnvironmentError(
        "Missing required environment variables: catalog_id and/or secret_key"
    )

logger = logging.getLogger(__name__)


def _get_response_yandex_gpt(
    original_context: list[dict], temperature=0.7, max_tokens=2000
):
    try:
        context = deepcopy(original_context)
        sp = {
            "role": "system",
            "text": system_prompt,
        }
        if context:
            context.insert(0, sp)

        prompt = {
            "modelUri": f"gpt://{catalog_id}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": str(max_tokens),
            },
            "messages": context,
        }

        logger.info(f"Sending request to YandexGPT with {len(context)} messages")
        logger.info(f"Request payload: {json.dumps(prompt, ensure_ascii=False)}")

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {secret_key}",
        }

        response = requests.post(url, headers=headers, json=prompt, timeout=30)

        # Добавляем логирование статуса ответа
        logger.info(f"YandexGPT response status: {response.status_code}")
        logger.info(
            f"YandexGPT response: {response.text[:500]}..."
        )  # Логируем первые 500 символов ответа

        if response.status_code != 200:
            logger.error(f"YandexGPT error response: {response.text}")
            return None, None

        try:
            result = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response.text}")
            return None, None

        # Проверяем структуру ответа
        if not isinstance(result, dict):
            logger.error(f"Unexpected response type: {type(result)}")
            return None, None

        if "result" not in result:
            logger.error(f"No 'result' key in response: {result}")
            return None, None

        result_data = result["result"]
        if "alternatives" not in result_data or not result_data["alternatives"]:
            logger.error(f"No alternatives in result: {result_data}")
            return None, None

        first_alternative = result_data["alternatives"][0]
        if (
            "message" not in first_alternative
            or "text" not in first_alternative["message"]
        ):
            logger.error(f"Invalid alternative format: {first_alternative}")
            return None, None

        response_text = first_alternative["message"]["text"]
        tokens = result_data.get("usage", {}).get("totalTokens", 0)

        logger.info(f"Successfully got response from YandexGPT. Tokens used: {tokens}")
        logger.info(
            f"Response text: {response_text[:100]}..."
        )  # Логируем первые 100 символов ответа

        return response_text, tokens

    except Exception as e:
        logger.error(
            f"Unexpected error in _get_response_yandex_gpt: {str(e)}", exc_info=True
        )
        return None, None


if __name__ == "__main__":
    context = [
        {
            "role": "user",
            "text": "Привет!",
        }
    ]
    result, tokens = _get_response_yandex_gpt(context)
    print(result)

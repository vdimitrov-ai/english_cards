import json
import logging
import os
from copy import deepcopy

import dotenv
import requests

dotenv.load_dotenv()

catalog_id = os.getenv("catalog_id")
secret_key = os.getenv("secret_key")
system_prompt = os.getenv("system_prompt")

logger = logging.getLogger(__name__)


def _get_response_yandex_gpt(
    original_context: list[dict], temperature=0.7, max_tokens=2000
):
    context = deepcopy(original_context)
    sp = {
        "role": "system",
        "text": f"{system_prompt}",
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
    logger.info(f"Context: {context}")

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {secret_key}",
    }

    try:
        response = requests.post(url, headers=headers, json=prompt, timeout=30)
        logger.info("Successfully got response from YandexGPT")
        result = response.text
        json_data = json.loads(result)
        return (
            json_data["result"]["alternatives"][0]["message"]["text"],
            json_data["result"]["usage"]["totalTokens"],
        )

    except requests.RequestException as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return None, context


if __name__ == "__main__":
    context = [
        {
            "role": "user",
            "text": "Привет!",
        }
    ]
    result, tokens = _get_response_yandex_gpt(context)
    print(result)

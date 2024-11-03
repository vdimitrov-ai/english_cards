import logging
import os

import dotenv
from groq import Groq

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

# Доступные модели Groq с их точными наименованиями
GROQ_MODELS = {
    "mixtral": "mixtral-8x7b-32768",  # Mixtral 8x7B
    "llama3-70b": "llama3-70b-8192",  # LLaMA-3 70B
    "gemma": "gemma-7b-it",  # Gemma 7B Instruct
    "llama3": "llama3-8b-8192",  # LLaMA-3 8B
    "gemma2": "gemma2-9b-it",  # Gemma 2 9B Instruct
}


def _get_response_groq(
    original_context: list[dict],
    temperature=0.7,
    max_tokens=2000,
    model="mixtral-8x7b-32768",
):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        messages = []
        for msg in original_context:
            messages.append(
                {
                    "role": msg["role"].replace("assistant", "system"),
                    "content": msg["text"],
                }
            )
        messages.insert(0, {"role": "system", "content": os.getenv("system_prompt")})

        logger.info(f"Context for {model}: {messages}")

        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        if chat_completion.choices:
            return chat_completion.choices[0].message.content, len(messages)
        return None, None

    except Exception as e:
        logger.error(f"Error in {model} response: {str(e)}")
        return None, None

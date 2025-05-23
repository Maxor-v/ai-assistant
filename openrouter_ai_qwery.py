import json
import logging
import aiohttp
import time
import threading
from typing import Dict, Any

# Сессии пользователей
user_sessions: Dict[str, Dict[str, Any]] = {}
session_lock = threading.Lock()

from config import (  # Импорт всех настроек
    API_KEY_OPENROUTER,
    MODEL,
    MAX_HISTORY,
    SESSION_TTL
)

TIMEOUT = aiohttp.ClientTimeout(total=1500)

# Пользовательский фильтр для исключения HTTP-логов
class NoHttpFilter(logging.Filter):
    def filter(self, record):
        # Исключаем логи, содержащие "HTTP Request"
        return "HTTP Request" not in record.getMessage()
# Настройка логгирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Добавляем фильтр к логгеру
for handler in logging.root.handlers:
    handler.addFilter(NoHttpFilter())

def process_content(content: str) -> str:
    return content.replace('<think>', '').replace('</think>', '')


def get_user_session(user_id: str) -> Dict[str, Any]:
        now = time.time()
        session = user_sessions.get(user_id)
        if not session or now - session['timestamp'] > SESSION_TTL:
            print(f"DEBUG: Creating new session for {user_id}")
            user_sessions[user_id] = {
                'history': [],
                'timestamp': now,
                'ignore': False
            }
        else:
            user_sessions[user_id]['timestamp'] = now

        return user_sessions[user_id]  # Возвращаем копию для безопасности


def trim_history(history: list) -> list:
    return history[-MAX_HISTORY:]


def load_answers_with_labels(filename: str = "prompt.txt") -> list:
    answers = []
    current_label = None
    current_content = []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                line = line.rstrip()  # Убираем пробелы справа

                if line.startswith("[") and line.endswith("]"):
                    # Сохраняем предыдущий блок
                    if current_label:
                        answers.append(current_label)
                        answers.append("\n".join(current_content))

                    # Начинаем новый блок
                    current_label = line
                    current_content = []
                else:
                    if line:  # Игнорируем пустые строки
                        current_content.append(line)

            # Добавляем последний блок
            if current_label and current_content:
                answers.append(current_label)
                answers.append("\n".join(current_content))

    except FileNotFoundError:
        print(f"⚠️ Файл {filename} не найден!")

    return answers


async def get_response(user_id: str, user_input: str) -> str:
    session = get_user_session(user_id)

    if session['ignore']:
        return "❌ Ваш аккаунт временно заблокирован для взаимодействия с ботом"

    history = session['history']

    if not history:
        allowed_answers = load_answers_with_labels()
        history.append({
            "role": "system",
            "content": f"Отвечай как опытный менеджер по продажам. Используй информацию:\n{'\n'.join(allowed_answers)}"
        })

    history.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {API_KEY_OPENROUTER}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": trim_history(history),
        "stream": True
    }

    full_response = []

    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"API Error: {response.status}, {error_text}")
                    return "⚠️ Ошибка сервиса. Попробуйте позже."

                async for chunk in response.content:
                    if chunk:
                        chunk_str = chunk.decode('utf-8').strip()
                        if chunk_str.startswith("data:"):
                            json_str = chunk_str[5:].strip()
                            if json_str == "[DONE]" or not json_str:
                                continue
                            try:
                                chunk_json = json.loads(json_str)
                                if "choices" in chunk_json:
                                    content = chunk_json["choices"][0]["delta"].get("content", "")
                                    if content:
                                        full_response.append(process_content(content))
                            except Exception as e:
                                logging.error(f"Chunk error: {e}")

                final_response = ''.join(full_response)
                history.append({"role": "assistant", "content": final_response})
                return final_response

    except Exception as e:
        logging.error(f"Connection error: {e}")
        return "⚠️ Ошибка соединения. Попробуйте снова."

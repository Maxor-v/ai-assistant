from flask import Flask, request, jsonify
import asyncio
import requests
from openrouter_ai_qwery import get_response
import logging
from config import API_KEY_WAZZUP, CHANNEL_ID
from session_manage import session_management_cli
from threading import Thread

app = Flask(__name__)

# Настройка фильтра для Werkzeug
class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return "POST /webhooks HTTP/1.1" not in record.getMessage()

logging.getLogger("werkzeug").addFilter(HealthCheckFilter())

def send_reply(phone_number: str, message_text: str) -> None:
    url = "https://api.wazzup24.com/v3/message"
    headers = {"Authorization": f"Bearer {API_KEY_WAZZUP}", "Content-Type": "application/json"}
    payload = {
        "channelId": CHANNEL_ID,
        "chatType": "whatsapp",
        "chatId": phone_number,
        "text": message_text
    }
    try:
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"Ошибка отправки: {e}")


def process_webhook(webhook_data: dict) -> None:
    if "messages" in webhook_data:
        for message in webhook_data["messages"]:
            if (message.get("type") == "text"
                    and not message.get("isEcho", False)      ):
                  #  and message.get('chatType') == 'whatsapp'):
                process_message(message)


def process_message(message: dict) -> None:
    try:
        message_text = message['text']
        chat_type = message['chatType']

        phone_number = message.get('chatId')
        print(f"Получено сообщение {chat_type} от {phone_number}: {message_text}")

        response_text = asyncio.run(get_response(phone_number, message_text))
        # Отправка ответа пользователю
        send_reply(phone_number, response_text)
        print(f"Отправлен умный ответ: {response_text}")

    except Exception as e:
        print(f"Ошибка обработки сообщения: {e}")


@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    process_webhook(request.json)
    return jsonify({"status": "ok"}), 200

def run_server():
    app.run(host='localhost', port=5000, ssl_context=('C:/OpenSSL-Win64/bin/cert.pem', 'C:/OpenSSL-Win64/bin/key.pem'), use_reloader=False)

if __name__ == '__main__':
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    session_management_cli()

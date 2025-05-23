import requests

def subscribe_to_webhooks(api_key, webhook_url):
    url = "https://api.wazzup24.com/v3/webhooks"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "webhooksUri": webhook_url,
        "subscriptions": {
            "messagesAndStatuses": True,  # Подписка на сообщения и их статусы
            "contactsAndDealsCreation": True  # Подписка на создание контактов и сделок
        }
    }

    try:
        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Вывод подробной информации об ошибке
        print(f"HTTP Error: {e}")
        print(f"Response: {response.text}")  # Вывод тела ответа для диагностики
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return None


# Пример использования
if __name__ == "__main__":
    # Замените значения на свои
    API_KEY = ""  # Ваш API-ключ
    WEBHOOK_URL = "https://"  # URL вашего вебхук-сервера

    result = subscribe_to_webhooks(API_KEY, WEBHOOK_URL)
    if result:
        print("Подписка на вебхуки успешно настроена:", result)
    else:
        print("Не удалось настроить подписку на вебхуки")

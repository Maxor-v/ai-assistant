# session_manage.py
import time
from openrouter_ai_qwery import user_sessions, session_lock

def list_sessions(verbose: bool = False) -> None:
    with session_lock:
        if not user_sessions:
            print("Активные сессии отсутствуют")
            return

        print(f"\nВсего активных сессий: {len(user_sessions)}")
        print("Текущие ключи сессий:", list(user_sessions.keys()))
        for user_id, session in user_sessions.items():
            print(f"\nID пользователя: {user_id}")
            print(f"Последняя активность: {time.ctime(session['timestamp'])}")
            print(f"Игнорируется: {'Да' if session['ignore'] else 'Нет'}")
            print(f"Сообщений в истории: {len(session['history'])}")
            if verbose:
                print("История сообщений:")
                for msg in session['history']:    #[-3:]:
                    print(f"  {msg['role']}: {msg['content'][:50]}...")

def toggle_ignore(user_id: str) -> bool:
    with session_lock:
        if user_id in user_sessions:
            user_sessions[user_id]['ignore'] = not user_sessions[user_id]['ignore']
            return True
        return False

def delete_session(user_id: str) -> bool:
    with session_lock:
        if user_id in user_sessions:
            del user_sessions[user_id]
            return True
        return False

def clear_all_sessions() -> None:
    with session_lock:
        user_sessions.clear()

def session_management_cli():
    while True:
        print("\nМенеджер сессий")
        print("1. Список сессий")
        print("2. Подробный список сессий")
        print("3. Удалить сессию")
        print("4. Удалить все сессии")
        print("5. Блокировка/разблокировка пользователя")
        print("6. Выход")

        choice = input("Выберите действие: \n\n")

        if choice == '1':
            list_sessions()
        elif choice == '2':
            list_sessions(verbose=True)
        elif choice == '3':
            user_id = input("Введите ID пользователя: ")
            if delete_session(user_id):
                print("Сессия удалена")
            else:
                print("Сессия не найдена")
        elif choice == '4':
            clear_all_sessions()
            print("Все сессии удалены")
        elif choice == '5':
            user_id = input("Введите ID пользователя: ")
            if toggle_ignore(user_id):
                print("Статус блокировки изменен")
            else:
                print("Пользователь не найден")
        elif choice == '6':
            break
        else:
            print("Неверный выбор")

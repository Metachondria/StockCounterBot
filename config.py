import json

def load_token():
    try:
        with open('token.txt', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print("Файл token.txt не найден.")
        return None

def load_users():
    try:
        with open('users.json', 'r') as file:
            data = json.load(file)
        return data["users"]
    except FileNotFoundError:
        print("Файл users.json не найден.")
        return []
    except json.JSONDecodeError:
        print("Ошибка в формате файла users.json.")
        return []

def save_users(users):
    try:
        with open('users.json', 'w') as file:
            json.dump({"users": users}, file, indent=4)
    except Exception as e:
        print(f"Ошибка при сохранении users.json: {e}")

TOKEN = load_token()
USERS = load_users()

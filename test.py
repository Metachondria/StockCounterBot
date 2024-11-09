import gspread
from google.oauth2.service_account import Credentials

# Настройка области доступа и учетных данных
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)

# Подключение к Google Sheets
client = gspread.authorize(creds)

# Открытие таблицы по имени
sheet_name = "K15_SKLAD"  # Замените на имя вашей таблицы
try:
    sheet = client.open(sheet_name).sheet1  # Используем первый лист
    print("Успешное подключение к таблице")
except gspread.exceptions.SpreadsheetNotFound:
    print(f"Таблица '{sheet_name}' не найдена. Проверьте имя таблицы и доступ.")
    exit(1)
except Exception as e:
    print(f"Ошибка подключения к таблице: {e}")
    exit(1)

# Пример чтения значения из ячейки A1
try:
    cell_value = sheet.acell('A1').value
    print(f"Значение ячейки A1: {cell_value}")
except gspread.exceptions.APIError as api_error:
    print(f"Ошибка API при чтении ячейки A1: {api_error}")
except Exception as e:
    print(f"Ошибка чтения ячейки: {e}")

# Пример записи значения в ячейку B1
try:
    sheet.update_acell('B1', "Тестовое значение")
    print("Успешное обновление ячейки B1")
except gspread.exceptions.APIError as api_error:
    print(f"Ошибка API при обновлении ячейки B1: {api_error}")
except Exception as e:
    print(f"Ошибка обновления ячейки: {e}")

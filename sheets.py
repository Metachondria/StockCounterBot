import gspread
from google.oauth2.service_account import Credentials
import logging

logger = logging.getLogger(__name__)

# Определение области действия (scope)
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Словарь для маппинга товаров на номера строк
PRODUCT_ROW_MAP = {
    "BoomBar батончики": 2,
    "BoomBar Печенья": 3,
    "Bueno": 4,
    "M&Ms": 5,
    "Дирол": 6,
    "Лейс": 7,
    "Пикник": 8,
    "Сникерс": 9,
    "Твикс": 10,
    "Холсс": 11,
    "Чебупелли": 12,
    "Чебупицца": 13,
    "Круггетсы": 14,
    "Фунчоза с овощами": 16,
    "Спагетти Карбонара": 17,
    "Паста с цыпленком": 18,
    "Котлеты с пюре": 19,
    "Борщ с телятеной": 20,
    "Грибной суп-пюре": 21,
    "Боул с цыпленком терияки": 22,
    "Люля-кебаб из цыпленка 260гр": 23,
    "Удон с курицей 250гр": 24,
    "Цыпленок в кисло-сладком соусе": 25,
    "Традиционный плов с курицей": 26,
    "Бефстроганов из говядины": 27,
    "BoomBar лимонад": 28,
    "BoomBar енергетики": 29,
    "Gorilla": 30,
    "LitEnergy": 31,
    "MonsterEnergy": 32,
    "Берн": 33,
    "Добрый 0,33": 34,
    "Липтон 0.5": 35,
    "Палпи 0.5": 36,
    "Ред Бул 0.25": 37,
    "Свят источник": 38,
    "Черноголовка": 39
}

def get_google_sheet(sheet_name):
    """Подключается к Google Таблице и возвращает объект листа."""
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open(sheet_name).sheet1
        return sheet
    except Exception as e:
        logger.error(f"Ошибка при подключении к Google Таблице: {e}")
        return None

def update_product_quantity_by_row(sheet_name, product_name, quantity):
    """Уменьшает количество товара в таблице по заданной строке в столбце C."""
    sheet = get_google_sheet(sheet_name)
    if sheet:
        row_number = PRODUCT_ROW_MAP.get(product_name)
        if row_number is None:
            logger.error(f"Товар '{product_name}' не найден в словаре PRODUCT_ROW_MAP.")
            return False, None

        try:
            # Получаем текущее количество из столбца C
            current_quantity = int(sheet.cell(row_number, 3).value)

            # Проверяем, достаточно ли товара для уменьшения
            if quantity > current_quantity:
                logger.warning(f"Недостаточно товара '{product_name}' для уменьшения. Текущий запас: {current_quantity}.")
                return False, current_quantity

            # Уменьшаем количество товара
            new_quantity = current_quantity - quantity
            sheet.update_cell(row_number, 3, new_quantity)  # Обновляем количество в столбце C
            logger.info(f"Количество товара '{product_name}' обновлено. Остаток: {new_quantity}.")
            return True, new_quantity
        except Exception as e:
            logger.error(f"Ошибка при обновлении количества товара '{product_name}': {e}")
            return False, None
    return False, None

# sheet = get_google_sheet("K15_SKLAD")
# if sheet:
#     print("Подключение к таблице установлено.")
# else:
#     print("Не удалось подключиться к таблице.")
#
# result, new_quantity = update_product_quantity_by_row("K15_SKLAD", "Фунчоза с овощами 250гр", 50)
# if result:
#     print(f"Количество обновлено успешно. Новый остаток: {new_quantity}")
# else:
#     print("Ошибка при обновлении количества.")
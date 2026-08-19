import requests
import json
from pathlib import Path

API_URL = "http://localhost:8000/api/v1/tickets/classify"
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"

TEST_CASES = [
    {"name": "1. Базовий billing (не edge)", "text": "Здравствуйте, хочу перейти з місячної підписки на річну, як це зробити?"},
    {"name": "2. Базовий bug (не edge)", "text": "При спробі завантажити відео додаток вилітає щоразу. Версія 3.2, iPhone 14."},
    {"name": "3. Агресія + тривіальна проблема", "text": "ЩО ЦЕ ЗА ДЕБІЛЬНИЙ ІНТЕРФЕЙС!!! Я НЕ МОЖУ ЗНАЙТИ КНОПКУ ЗМІНИ АВАТАРКИ!!! ВИ ЗА ЩО ГРОШІ БЕРЕТЕ???"},
    {"name": "4. Сарказм, що маскує реальну проблему", "text": "Ого, дуже дякую, що видалили мій акаунт без попередження. Просто чудово, обожнюю коли 3 роки історії зникають в один клік."},
    {"name": "5. Змішана тема: скарга на експерта + рефанд", "text": "Консультант Олена була грубою, перебивала мене весь сеанс. Хочу повернути гроші за цю сесію."},
    {"name": "6. Не англійська / змішана мова", "text": "Hi, у мене проблема з payment — гроші списались двічі за цей місяц, please help."},
    {"name": "7. Погроза судом / пресою", "text": "Це вже втретє ви списуєте гроші без дозволу. Якщо це не вирішиться сьогодні, я звертаюсь до захисту прав споживачів."},
    {"name": "8. Порожній/беззмістовний текст", "text": "... ??"},
    {"name": "9. Прихований фішинг/спам", "text": "Your account will be suspended! Click here to verify your payment info immediately: bit.ly/verify-account-now"},
    {"name": "10. Два незалежні запити", "text": "Два питання: 1) чи можна змінити email на акаунті? 2) додаток не відкриває розділ 'Історія' — просто біле вікно."},
    {"name": "11. Спокійний тон, але критична проблема", "text": "Доброго дня. З мене списали кошти за річну підписку, хоча я скасував автопродовження місяць тому. Сума немала, прошу розібратись."},
    {"name": "12. Дуже короткий тікет", "text": "Не працює."},
    {"name": "13. Позитивний фідбек", "text": "Хочу подякувати команді підтримки, дуже швидко і чемно допомогли вирішити моє питання!"}
]

def run_tests():
    print(f"Запуск тестування 13 кейсів класифікатора (API: {API_URL})...")
    
    markdown_content = "# Результати тестування Edge Cases класифікатора\n\n"
    markdown_content += "Цей файл згенеровано автоматично скриптом `backend/tests/test_classifier_cases.py`.\n\n"
    
    for i, case in enumerate(TEST_CASES, 1):
        print(f"Тестую [{i}/13]: {case['name']}...")
        try:
            response = requests.post(API_URL, json={"text": case["text"]}, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            human_review = "ТАК" if result.get("requires_human_review") else "🟢 НІ"
            reason = result.get('human_review_reason') or "N/A"
            
            markdown_content += f"### {case['name']}\n"
            markdown_content += f"**Вхідний текст:** `{case['text']}`\n\n"
            markdown_content += f"- **Категорія:** `{result.get('category')}`\n"
            markdown_content += f"- **Пріоритет:** `{result.get('priority')}`\n"
            markdown_content += f"- **Наступний крок:** `{result.get('next_step')}`\n"
            markdown_content += f"- **Потребує людини:** {human_review} (Причина: *{reason}*)\n\n"
            markdown_content += "---\n\n"
            
        except requests.exceptions.RequestException as e:
            print(f"Помилка з'єднання: {e}")
            return
            
    # Зберігаємо результати у файл
    DOCS_DIR.mkdir(exist_ok=True)
    output_file = DOCS_DIR / "test_results.md"
    output_file.write_text(markdown_content, encoding="utf-8")
    
    print(f"Тестування завершено! Результати збережено у {output_file}")

if __name__ == "__main__":
    run_tests()
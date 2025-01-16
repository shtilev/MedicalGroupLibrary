import openai
from medicalgrouplibrary.database import SessionLocal
from pydantic import BaseModel
from typing import List
from medicalgrouplibrary.unificator import add_synonym
from medicalgrouplibrary.database import AnalysisSynonym, StandardName
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY_MLAI = os.getenv("API_KEY_MLAI")

client = openai.OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key=API_KEY_MLAI
)


class Synonym(BaseModel):
    standard_name: str
    synonym: str


class SynonymsList(BaseModel):
    list_of_synonyms: List[Synonym]


def get_llm_response(text: str, prompt: str, model="gpt-4o-mini"):
    """
    Отримуємо відповідь від LLM (OpenAI) для синонімів до заданого уніфікованого імені.
    :param text: Вхідний текст (стандартне ім'я для якого шукаються синоніми).
    :param prompt: Повідомлення, яке передається в систему як частина запиту.
    :param model: Модель, яку використовуємо для запиту.
    :return: Список синонімів у вигляді словників.
    """
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        response_format=SynonymsList,
        max_tokens=16384
    )
    # Парсимо відповідь у вигляді List of dicts [{standard_name: synonym}]
    reasoning_dict = completion.choices[0].message.parsed.model_dump()
    return reasoning_dict


def create_synonyms_for_standard_name(standard_name: str):
    """
    Створює список синонімів для заданого уніфікованого імені (стандартного імені) за допомогою OpenAI API.
    Перевіряє чи синоніми вже є в базі, і додає їх, якщо їх немає.
    :param standard_name: Стандартне ім'я для якого створюються синоніми.
    :return: Список синонімів, які були додані в базу даних.
    """
    session = SessionLocal()
    added_synonyms = []  # Список для зберігання доданих синонімів
    try:
        # Формулюємо запит до OpenAI
        prompt = f"""
        Перелічіть усі можливі варіанти написання для медичного терміну: {standard_name}. Усі варіанти мають стосуватися виключно цього показника ({standard_name}) і враховувати можливі написання, які можуть зустрічатися в різних медичних документах, лабораторних результатах, аналізах тощо. 
        Включіть варіанти з такими особливостями: 
        - Різні абревіатури або скорочення (наприклад, 'HGB', 'Hb').
        - Варіанти з уточненнями (наприклад, '{standard_name} у крові', ' Тест на {standard_name}' - додавай реальні приклади з медичних аналізів і інших документів).
        - Переклади та альтернативні назви (наприклад, 'Гемоглобін', 'Hemoglobin', 'Hgb'). Орієнтуйся на назви для україньского сегменту.
        - Можливі помилки або варіації у написанні, якщо вони поширені у реальних документах.

        Не включайте значення, що належать іншим показникам навіть із подібними назвами (наприклад, 'Гемоглобін А' або 'Глікогемоглобін' не слід включати). Уніфікована назва для цього показника має залишатися незмінною в полі standard_name: {standard_name}.
        """

        response_dict = get_llm_response(standard_name, prompt)

        # Перевірка наявності синонімів у відповіді
        if "list_of_synonyms" in response_dict:
            list_of_synonyms = response_dict["list_of_synonyms"]
            for synonym_data in list_of_synonyms:
                # Перевіряємо, чи вже існує синонім для цього стандартного імені
                existing_synonym = session.query(AnalysisSynonym).join(StandardName).filter(
                    StandardName.name == standard_name,
                    AnalysisSynonym.synonym == synonym_data["synonym"]
                ).first()

                if not existing_synonym:
                    # Якщо синоніма немає, додаємо його
                    add_synonym(synonym_data["standard_name"], synonym_data["synonym"])
                    added_synonyms.append(synonym_data["synonym"])  # Додаємо до списку доданих синонімів
                else:
                    print(f"Синонім '{synonym_data['synonym']}' для '{standard_name}' вже існує.")

        return added_synonyms  # Повертаємо тільки додані синоніми
    finally:
        session.close()


# Приклад використання
if __name__ == "__main__":
    standard_name = "Гемоглобін"
    for _ in tqdm(range(10)):
        created_synonyms = create_synonyms_for_standard_name(standard_name)

import json
from medicalgrouplibrary.database import SessionLocal, AnalysisSynonym

def import_synonyms_from_json(file_path: str):
    """
    Заповнює базу даних синонімами та уніфікованими іменами з JSON-файлу.
    :param file_path: Шлях до JSON-файлу з синонімами.
    """
    session = SessionLocal()
    try:
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            synonyms_data = json.load(jsonfile)
            for entry in synonyms_data:
                standard_name = entry['standard_name']
                synonym = entry['synonym']
                # Перевіряємо, чи не існує вже цього синоніма в базі
                existing_synonym = session.query(AnalysisSynonym).filter_by(synonym=synonym).first()
                if not existing_synonym:
                    synonym_entry = AnalysisSynonym(standard_name=standard_name, synonym=synonym)
                    session.add(synonym_entry)
                    print(f"Додано синонім '{synonym}' для уніфікованого імені '{standard_name}'.")
            session.commit()
    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        session.close()


def export_synonyms_to_json(file_path: str):
    """
    Експортує всі синоніми та уніфіковані імена з бази даних у форматі JSON.
    :param file_path: Шлях до файлу для збереження даних.
    """
    session = SessionLocal()
    try:
        # Отримуємо всі записи з таблиці AnalysisSynonym
        synonyms_data = session.query(AnalysisSynonym).all()

        # Формуємо список словників для запису в JSON
        data_to_export = [{"standard_name": entry.standard_name, "synonym": entry.synonym} for entry in synonyms_data]

        # Записуємо отримані дані у файл JSON
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data_to_export, jsonfile, ensure_ascii=False, indent=4)

        print(f"Синоніми успішно експортовані в файл '{file_path}'.")

    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        session.close()


export_synonyms_to_json('../synonyms_export.json')

# import_synonyms_from_json('synonyms_file.json')

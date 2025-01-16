from rapidfuzz import process, fuzz
from medicalgrouplibrary.database import SessionLocal, AnalysisSynonym, StandardName


def add_synonym(standard_name: str, synonym: str):
    """
    Додає новий синонім до бази даних для заданого стандартного імені, якщо такого синоніма ще не існує.
    :param standard_name: Уніфіковане ім'я аналізу.
    :param synonym: Синонім для уніфікованого імені.
    """
    session = SessionLocal()

    # Перевірка на наявність стандартного імені
    standard_name_entry = session.query(StandardName).filter_by(name=standard_name).first()

    # Якщо стандартне ім'я не знайдено, створюємо його
    if not standard_name_entry:
        standard_name_entry = StandardName(name=standard_name)
        session.add(standard_name_entry)
        session.commit()

    # Перевірка на наявність синоніма
    existing_synonym = session.query(AnalysisSynonym).filter_by(standard_name_id=standard_name_entry.id, synonym=synonym).first()

    if existing_synonym:
        print(f"Синонім '{synonym}' для '{standard_name}' вже існує в базі.")
        session.close()
        return

    # Додаємо синонім
    synonym_entry = AnalysisSynonym(standard_name_id=standard_name_entry.id, synonym=synonym)
    session.add(synonym_entry)
    session.commit()
    print(f"Синонім '{synonym}' додано для '{standard_name}'.")

    session.close()

def get_unification_name(synonym: str, threshold: float = 80.0) -> str:
    """
    Повертає уніфіковане ім'я для заданого синоніму або найбільш схоже значення,
    якщо схожість перевищує заданий поріг.
    :param synonym: Синонім або можливе уніфіковане ім'я.
    :param threshold: Поріг схожості (від 0 до 100), щоб прийняти синонім.
    :return: Уніфіковане ім'я або повідомлення про відсутність.
    """
    session = SessionLocal()
    try:
        # Перевірка на точний збіг для синоніма
        synonym_entry = session.query(AnalysisSynonym).filter_by(synonym=synonym).first()
        if synonym_entry:
            return synonym_entry.standard_name.name  # Повертаємо стандартне ім'я

        # Перевірка на точний збіг для уніфікованого імені (якщо це можливе введення)
        standard_entry = session.query(StandardName).filter_by(name=synonym).first()
        if standard_entry:
            return standard_entry.name  # Повертаємо саме стандартне ім'я

        # Отримуємо всі синоніми та уніфіковані імена з бази
        all_synonyms = session.query(AnalysisSynonym.synonym).all()
        all_standard_names = session.query(StandardName.name).all()

        all_synonyms_list = [item[0] for item in all_synonyms]
        all_standard_names_list = [item[0] for item in all_standard_names]

        # Об'єднуємо списки синонімів і стандартних імен для пошуку
        combined_list = all_synonyms_list + all_standard_names_list

        # Шукаємо найбільш схожий синонім або стандартне ім'я
        match, score, _ = process.extractOne(synonym, combined_list, scorer=fuzz.ratio)

        if score >= threshold:
            # Якщо знайдено схоже значення, повертаємо тільки уніфіковане ім'я
            if match in all_synonyms_list:
                matched_entry = session.query(AnalysisSynonym).filter_by(synonym=match).first()
            else:
                matched_entry = session.query(StandardName).filter_by(name=match).first()

            return matched_entry.name if isinstance(matched_entry, StandardName) else matched_entry.standard_name.name

        # Якщо синонім не знайдено, шукаємо найбільш схожі уніфіковані імена за частинами тексту
        partial_match, partial_score, _ = process.extractOne(synonym, all_standard_names_list, scorer=fuzz.partial_ratio)

        if partial_score >= threshold:
            # Якщо знайдено схоже уніфіковане ім'я, повертаємо його
            partial_entry = session.query(StandardName).filter_by(name=partial_match).first()
            return partial_entry.name

        return f"Синонім '{synonym}' не знайдено в базі та немає подібних варіантів."
    except Exception as e:
        print(f"Помилка: {e}")
        return "Сталася помилка при пошуку уніфікованого імені."
    finally:
        session.close()


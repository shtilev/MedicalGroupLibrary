from medicalgrouplibrary.database import SessionLocal, Unit, UnitConversion, StandardName
from sqlalchemy.exc import IntegrityError


def add_unit(standard_name_id: int, unit: str, is_standard: bool = False):
    """
    Додає новий юніт до бази даних для заданого стандартного імені за його ID, якщо такого юніта ще не існує.
    :param standard_name_id: ID стандартного імені.
    :param unit: Одиниця вимірювання для аналізу.
    :param is_standard: Чи є одиниця стандартною.
    """
    session = SessionLocal()

    try:
        # Перевірка на наявність стандартного імені за ID
        standard_name_entry = session.query(StandardName).filter_by(id=standard_name_id).first()

        if not standard_name_entry:
            print(f"Стандартне ім'я з ID '{standard_name_id}' не знайдено.")
            return

        # Перевірка на наявність юніта для заданого standard_name_id
        existing_unit = session.query(Unit).filter_by(standard_name_id=standard_name_entry.id, unit=unit).first()

        if existing_unit:
            print(f"Юніт '{unit}' для стандартного імені з ID '{standard_name_id}' вже існує в базі.")
            return

        # Додаємо новий юніт
        new_unit = Unit(standard_name_id=standard_name_entry.id, unit=unit, is_standard=is_standard)
        session.add(new_unit)
        session.commit()
        print(f"Юніт '{unit}' додано для стандартного імені з ID '{standard_name_id}'.")

    except IntegrityError:
        session.rollback()
        print("Помилка: Юніт не був доданий через порушення обмежень.")
    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        session.close()


def get_units_for_standard_name(standard_name_id: int):
    """
    Отримує всі юніти для заданого стандартного імені за його ID.
    :param standard_name_id: ID стандартного імені.
    :return: Список юнітів або повідомлення про помилку.
    """
    session = SessionLocal()

    try:
        # Шукаємо StandardName за його ID
        standard_name_entry = session.query(StandardName).filter_by(id=standard_name_id).first()

        if not standard_name_entry:
            return f"Стандартне ім'я з ID '{standard_name_id}' не знайдено."

        # Отримуємо юніти для знайденого стандартного імені
        units = session.query(Unit).filter_by(standard_name_id=standard_name_entry.id).all()

        # Перетворення об'єктів на зручний формат для повернення
        units_list = [{"id": unit.id,"unit": unit.unit, "is_standard": unit.is_standard} for unit in units]

        return units_list

    except Exception as e:
        print(f"Помилка: {e}")
        return "Сталася помилка при отриманні юнітів."
    finally:
        session.close()


def get_standard_unit_for_standard_name(standard_name_id: int):
    """
    Отримує стандартний юніт для заданого стандартного імені за його ID.
    :param standard_name_id: ID стандартного імені.
    :return: Стандартний юніт або повідомлення про помилку.
    """
    session = SessionLocal()

    try:
        # Шукаємо StandardName за його ID
        standard_name_entry = session.query(StandardName).filter_by(id=standard_name_id).first()

        if not standard_name_entry:
            return f"Стандартне ім'я з ID '{standard_name_id}' не знайдено."

        # Шукаємо стандартний юніт для знайденого стандартного імені
        standard_unit = session.query(Unit).filter_by(standard_name_id=standard_name_entry.id, is_standard=True).first()

        if standard_unit:
            return {"unit": standard_unit.unit, "is_standard": standard_unit.is_standard}

        return f"Стандартний юніт для стандартного імені з ID '{standard_name_id}' не знайдено."

    except Exception as e:
        print(f"Помилка: {e}")
        return "Сталася помилка при отриманні стандартного юніта."
    finally:
        session.close()


def add_unit_conversation(from_unit_id: int, to_unit_id: int, formula: str, standard_name_id: int):
    """
    Додає конверсію між двома юнітами до бази даних.
    :param from_unit_id: ID юніта, з якого відбувається конверсія.
    :param to_unit_id: ID юніта, в який відбувається конверсія.
    :param formula: Формула для конверсії.
    :param standard_name_id: ID стандартного імені, до якого прив'язана конверсія.
    """
    session = SessionLocal()

    try:
        # Перевірка на наявність обох юнітів
        from_unit = session.query(Unit).filter_by(id=from_unit_id).first()
        to_unit = session.query(Unit).filter_by(id=to_unit_id).first()

        if not from_unit or not to_unit:
            print("Помилка: Один або обидва юніти не знайдені.")
            return

        # Перевірка на наявність конверсії
        existing_conversion = session.query(UnitConversion).filter_by(
            from_unit_id=from_unit.id, to_unit_id=to_unit.id, standard_name_id=standard_name_id).first()

        if existing_conversion:
            print(f"Конверсія між юнітами '{from_unit.unit}' і '{to_unit.unit}' вже існує для стандартного імені.")
            return

        # Додаємо нову конверсію
        new_conversion = UnitConversion(
            from_unit_id=from_unit.id,
            to_unit_id=to_unit.id,
            formula=formula,
            standard_name_id=standard_name_id
        )
        session.add(new_conversion)
        session.commit()
        print(f"Конверсія між '{from_unit.unit}' і '{to_unit.unit}' для стандартного імені додана з формулою: {formula}.")

    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        session.close()


def get_conversions_for_unit(unit: str):
    """
    Отримує всі конверсії для заданої одиниці.
    :param unit: Одиниця вимірювання.
    :return: Список конверсій у вигляді словників.
    """
    session = SessionLocal()

    try:
        unit_entry = session.query(Unit).filter_by(unit=unit).first()

        if not unit_entry:
            return f"Одиниця '{unit}' не знайдена."

        conversions = session.query(UnitConversion).filter_by(from_unit_id=unit_entry.id).all()

        # Перетворюємо об'єкти в зручні для читання словники
        conversion_list = [
            {
                "from_unit": conversion.from_unit.unit,
                "to_unit": conversion.to_unit.unit,
                "formula": conversion.formula,
                "standard_name": conversion.standard_name.name
            }
            for conversion in conversions
        ]

        return conversion_list

    except Exception as e:
        print(f"Помилка: {e}")
        return "Сталася помилка при отриманні конверсій."
    finally:
        session.close()


def convert_to_standard_unit(value: float, from_unit_id: int, standard_name_id: int):
    """
    Переводит значение из одной единицы измерения в стандартную для заданного стандартного имени.
    :param value: Значение для конверсии.
    :param from_unit_id: ID единицы измерения, из которой происходит конверсия.
    :param standard_name_id: ID стандартного имени, к которому привязана конверсия.
    :return: Словарь с конвертированным значением, названиями единиц и дополнительной информацией.
    """
    session = SessionLocal()

    try:
        # Находим стандартную единицу для заданного стандартного имени
        standard_unit = session.query(Unit).filter_by(standard_name_id=standard_name_id, is_standard=True).first()

        if not standard_unit:
            return {
                "error": f"Стандартная единица для стандартного имени с ID {standard_name_id} не найдена."
            }

        # Находим исходную единицу
        from_unit = session.query(Unit).filter_by(id=from_unit_id).first()

        if not from_unit:
            return {
                "error": f"Единица с ID {from_unit_id} не найдена."
            }

        # Если исходная единица уже является стандартной, возвращаем значение без изменений
        if from_unit_id == standard_unit.id:
            return {
                "value": value,
                "from_unit": from_unit.unit,
                "to_unit": standard_unit.unit,
                "standard_name_id": standard_name_id,
            }

        # Пытаемся найти прямую конверсию
        conversion = session.query(UnitConversion).filter_by(
            from_unit_id=from_unit_id, to_unit_id=standard_unit.id, standard_name_id=standard_name_id).first()

        if conversion:
            # Используем прямую формулу
            formula = conversion.formula.replace('x', 'value')
            context = {'value': value}
            try:
                converted_value = eval(formula, {}, context)
                return {
                    "value": converted_value,
                    "from_unit": from_unit.unit,
                    "to_unit": standard_unit.unit,
                    "standard_name_id": standard_name_id,
                }
            except Exception as e:
                return {"error": f"Ошибка выполнения формулы: {e}"}

        # Если прямая конверсия не найдена, ищем обратную
        reverse_conversion = session.query(UnitConversion).filter_by(
            from_unit_id=standard_unit.id, to_unit_id=from_unit_id, standard_name_id=standard_name_id).first()

        if reverse_conversion:
            # Инвертируем формулу для обратной конверсии
            formula = reverse_conversion.formula.replace('x', 'value')
            inverted_formula = f"value / ({formula})"  # Инвертируем формулу
            context = {'value': value}
            try:
                converted_value = eval(inverted_formula, {}, context)
                return {
                    "value": converted_value,
                    "from_unit": from_unit.unit,
                    "to_unit": standard_unit.unit,
                    "standard_name_id": standard_name_id,
                }
            except Exception as e:
                return {"error": f"Ошибка выполнения обратной формулы: {e}"}

        # Если ни прямая, ни обратная конверсия не найдены
        return {
            "error": f"Конверсия между единицей '{from_unit.unit}' и стандартной единицей '{standard_unit.unit}' не найдена."
        }

    except Exception as e:
        print(f"Ошибка: {e}")
        return {"error": "Произошла ошибка во время выполнения конверсии."}
    finally:
        session.close()


def calculate_conversion(value: float, from_unit: str, to_unit: str, standard_name_id: int):
    """
    Виконує конверсію значення між будь-якими двома одиницями вимірювання.
    :param value: Початкове значення для конверсії.
    :param from_unit: Одиниця вимірювання, з якої відбувається конверсія.
    :param to_unit: Одиниця вимірювання, до якої потрібно конвертувати.
    :param standard_name_id: ID стандартного імені.
    :return: Конвертоване значення або повідомлення про помилку.
    """
    session = SessionLocal()

    try:
        # Отримуємо всі одиниці вимірювання для стандартного імені
        units = session.query(Unit).filter_by(standard_name_id=standard_name_id).all()
        if not units:
            return {"error": "Одиниці вимірювання для заданого стандартного імені не знайдені."}

        # Створюємо граф конверсій
        conversions = session.query(UnitConversion).filter_by(standard_name_id=standard_name_id).all()
        graph = {}
        for conversion in conversions:
            if conversion.from_unit_id not in graph:
                graph[conversion.from_unit_id] = []
            graph[conversion.from_unit_id].append((conversion.to_unit_id, conversion.formula))

        # Знаходимо ID одиниць from_unit і to_unit
        from_unit_entry = session.query(Unit).filter_by(unit=from_unit, standard_name_id=standard_name_id).first()
        to_unit_entry = session.query(Unit).filter_by(unit=to_unit, standard_name_id=standard_name_id).first()

        if not from_unit_entry or not to_unit_entry:
            return {"error": f"Одна або обидві одиниці ('{from_unit}', '{to_unit}') не знайдені."}

        from_unit_id = from_unit_entry.id
        to_unit_id = to_unit_entry.id

        # BFS для пошуку шляху між одиницями
        from collections import deque

        queue = deque([(from_unit_id, value, [])])  # (current_unit_id, current_value, path)
        visited = set()

        while queue:
            current_unit_id, current_value, path = queue.popleft()

            if current_unit_id == to_unit_id:
                return {
                    "value": current_value,
                    "path": path,
                    "from_unit": from_unit,
                    "to_unit": to_unit,
                }

            if current_unit_id in visited:
                continue

            visited.add(current_unit_id)

            for neighbor_unit_id, formula in graph.get(current_unit_id, []):
                # Обчислюємо нове значення
                context = {'value': current_value}
                try:
                    new_value = eval(formula.replace('x', 'value'), {}, context)
                except Exception as e:
                    return {"error": f"Помилка в обчисленні формули '{formula}': {e}"}

                # Додаємо сусіда в чергу
                queue.append((neighbor_unit_id, new_value, path + [(current_unit_id, neighbor_unit_id, formula)]))

        return {"error": f"Шлях між одиницями '{from_unit}' і '{to_unit}' не знайдено."}

    except Exception as e:
        print(f"Помилка: {e}")
        return {"error": "Сталася помилка при виконанні конверсії."}
    finally:
        session.close()

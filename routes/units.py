from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import filter_op
from medicalgrouplibrary.units import *
from medicalgrouplibrary.database import SessionLocal, Unit, UnitConversion, StandardName
from medicalgrouplibrary.units import add_unit, add_unit_conversation
from fastapi.templating import Jinja2Templates


# Ініціалізація роутера
router = APIRouter()

# Шаблони Jinja2
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/units", response_class=HTMLResponse)
async def get_all_standard_names(request: Request, filter_letter: str = None, db: Session = Depends(get_db)):
    # Отримання стандартних імен з можливістю фільтрації
    standard_names_query = db.query(StandardName)

    if filter_letter:
        # Фільтрація за першою літерою назви
        standard_names_query = standard_names_query.filter(StandardName.name.ilike(f"{filter_letter}%"))

    standard_names = standard_names_query.all()

    return templates.TemplateResponse("units.html", {
        "request": request,
        "standard_names": standard_names,
        "filter_letter": filter_letter,
    })


@router.get("/units/{standard_name_id}", response_class=HTMLResponse)
async def get_units(request: Request, standard_name_id: int, db: Session = Depends(get_db)):
    standard_name = db.query(StandardName).filter_by(id=standard_name_id).first()

    if not standard_name:
        raise HTTPException(status_code=404, detail="Стандартне ім'я не знайдено.")

    units = get_units_for_standard_name(standard_name_id)

    return templates.TemplateResponse("units_list.html", {
        "request": request,
        "standard_name": standard_name,
        "units": units
    })



@router.get("/add_unit/{standard_name_id}", response_class=HTMLResponse)
async def show_add_unit_form(request: Request, standard_name_id: int, db: Session = Depends(get_db)):
    # Отримуємо стандартне ім'я
    standard_name = db.query(StandardName).filter_by(id=standard_name_id).first()

    # Перевіряємо, чи стандартне ім'я існує
    if not standard_name:
        raise HTTPException(status_code=404, detail="Стандартне ім'я не знайдено.")

    # Повертаємо шаблон з передачею standard_name_id
    return templates.TemplateResponse("add_unit.html", {
        "request": request,
        "standard_name_id": standard_name_id,
        "standard_name": standard_name
    })


@router.post("/add_unit", response_class=HTMLResponse)
async def add_unit_route(request: Request, standard_name_id: int = Form(...), unit: str = Form(...),is_standard: bool = Form(False)):

    # Перевірка, чи є значення для unit
    if not unit:
        raise HTTPException(status_code=400, detail="Поле 'unit' є обов'язковим.")

    # Викликаємо функцію add_unit для додавання нового юніта
    add_unit(standard_name_id=standard_name_id, unit=unit, is_standard=is_standard)

    # Після додавання перенаправляємо на список юнітів
    return RedirectResponse(f"/units/{standard_name_id}", status_code=302)


@router.get("/conversions", response_class=HTMLResponse)
async def get_standard_names(request: Request, filter_letter: str = None, db: Session = Depends(get_db)):
    # Отримуємо стандартні імена з можливістю фільтрації
    standard_names_query = db.query(StandardName)

    if filter_letter:
        # Фільтрація за першою літерою назви
        standard_names_query = standard_names_query.filter(StandardName.name.ilike(f"{filter_letter}%"))

    standard_names = standard_names_query.all()

    return templates.TemplateResponse("conversions.html", {
        "request": request,
        "standard_names": standard_names,
        "filter_letter": filter_letter,
    })


@router.get("/conversions/{standard_name_id}", response_class=HTMLResponse)
async def get_conversions_for_standard_name(request: Request, standard_name_id: int, db: Session = Depends(get_db)):
    standard_name = db.query(StandardName).filter_by(id=standard_name_id).first()
    if not standard_name:
        raise HTTPException(status_code=404, detail="Стандартне ім'я не знайдено.")

    # Отримуємо всі конверсії для цього стандартного імені
    conversions = db.query(UnitConversion).filter_by(standard_name_id=standard_name_id).all()

    return templates.TemplateResponse("conversions_list.html", {
        "request": request,
        "standard_name": standard_name,
        "conversions": conversions
    })


# Роут для додавання конверсії між юнітами
@router.get("/add_conversion/{standard_name_id}", response_class=HTMLResponse)
async def show_add_conversion_form(request: Request, standard_name_id: int, db: Session = Depends(get_db)):
    standard_name = db.query(StandardName).filter_by(id=standard_name_id).first()
    if not standard_name:
        raise HTTPException(status_code=404, detail="Стандартне ім'я не знайдено.")
    units = db.query(Unit).filter_by(standard_name_id=standard_name_id).all()
    return templates.TemplateResponse("add_conversion.html", {"request": request, "standard_name_id": standard_name_id, "standard_name": standard_name, "units": units})



@router.post("/add_conversion", response_class=HTMLResponse)
async def add_conversion_route(request: Request, from_unit_id: int = Form(...), to_unit_id: int = Form(...),
                               formula: str = Form(...), standard_name_id: int = Form(...), db: Session = Depends(get_db)):
    # Додаємо конверсію
    add_unit_conversation(from_unit_id, to_unit_id, formula, standard_name_id)
    return RedirectResponse(f"/conversions/{standard_name_id}", status_code=302)



# Роут для перегляду всіх конверсій для стандартного імені
@router.get("/conversions/{standard_name_id}", response_class=HTMLResponse)
async def get_conversions_for_standard_name(request: Request, standard_name_id: int, db: Session = Depends(get_db)):
    conversions = db.query(UnitConversion).filter_by(standard_name_id=standard_name_id).all()
    return templates.TemplateResponse("conversions.html", {"request": request, "standard_name_id": standard_name_id, "conversions": conversions})



@router.get("/test_conversion/{standard_name_id}", response_class=HTMLResponse)
async def show_test_conversion_form(request: Request, standard_name_id: int, db: Session = Depends(get_db)):
    # Отримуємо стандартне ім'я та всі його юніти
    standard_name = db.query(StandardName).filter_by(id=standard_name_id).first()
    if not standard_name:
        raise HTTPException(status_code=404, detail="Стандартне ім'я не знайдено.")
    units = db.query(Unit).filter_by(standard_name_id=standard_name_id).all()
    return templates.TemplateResponse("test_conversion.html", {
        "request": request,
        "standard_name_id": standard_name_id,
        "standard_name": standard_name,
        "units": units
    })


@router.post("/test_conversion", response_class=HTMLResponse)
async def test_conversion_route(request: Request, value: float = Form(...), from_unit_id: int = Form(...),
                                standard_name_id: int = Form(...), db: Session = Depends(get_db)):
    # Виконуємо конверсію
    result = convert_to_standard_unit(value=value, from_unit_id=from_unit_id, standard_name_id=standard_name_id)

    # Повертаємо результат на ту саму сторінку
    standard_name = db.query(StandardName).filter_by(id=standard_name_id).first()
    if not standard_name:
        raise HTTPException(status_code=404, detail="Стандартне ім'я не знайдено.")
    units = db.query(Unit).filter_by(standard_name_id=standard_name_id).all()

    return templates.TemplateResponse("test_conversion.html", {
        "request": request,
        "standard_name_id": standard_name_id,
        "standard_name": standard_name,
        "units": units,
        "result": result,
        "input_value": value
    })



@router.post("/delete_unit/{unit_id}", response_class=HTMLResponse)
async def delete_unit_route(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = db.query(Unit).filter_by(id=unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Юніт не знайдено.")

    db.delete(unit)
    db.commit()

    return RedirectResponse(f"/units/{unit.standard_name_id}", status_code=302)


@router.post("/delete_conversion/{conversion_id}", response_class=HTMLResponse)
async def delete_conversion_route(request: Request, conversion_id: int, db: Session = Depends(get_db)):
    conversion = db.query(UnitConversion).filter_by(id=conversion_id).first()
    if not conversion:
        raise HTTPException(status_code=404, detail="Конверсію не знайдено.")

    db.delete(conversion)
    db.commit()

    return RedirectResponse(f"/conversions/{conversion.standard_name_id}", status_code=302)


@router.get("/calculator", response_class=HTMLResponse)
async def show_calculator_page(request: Request, filter_letter: str = None, db: Session = Depends(get_db)):
    # Отримуємо всі стандартні імена
    standard_names_query = db.query(StandardName)

    if filter_letter:
        # Фільтрація за першою літерою назви
        standard_names_query = standard_names_query.filter(StandardName.name.ilike(f"{filter_letter}%"))

    standard_names = standard_names_query.all()
    return templates.TemplateResponse("calculator.html", {"request": request, "standard_names": standard_names,
                                                          "filter_letter": filter_letter})


# Роут для відображення форми конверсії для вибраного стандартного імені
@router.get("/calculator_result/{standard_name_id}", response_class=HTMLResponse)
async def show_conversion_form(request: Request, standard_name_id: int, db: Session = Depends(get_db)):

    # Получаем стандартное имя по id
    standard_name = db.query(StandardName).filter_by(id=standard_name_id).first()
    if not standard_name:
        raise HTTPException(status_code=404, detail="Стандартное имя не найдено.")

    # Получаем единицы измерения для этого стандартного имени
    units = db.query(Unit).filter_by(standard_name_id=standard_name_id).all()

    # Отправляем форму с доступными единицами
    return templates.TemplateResponse("calculator_result.html", {
        "request": request,
        "standard_name_id": standard_name_id,
        "standard_name": standard_name,
        "units": units
    })

# Роут для выполнения конверсии после отправки формы
@router.post("/calculator_result_submit", response_class=HTMLResponse)
async def calculate_conversion(request: Request, value: float = Form(...), from_unit_id: int = Form(...),
                               to_unit_id: int = Form(...), standard_name_id: int = Form(...), db: Session = Depends(get_db)):
    # Виконуємо конверсію
    result = convert_to_standard_unit(value=value, from_unit_id=from_unit_id, standard_name_id=standard_name_id)

    # Отримуємо стандартне ім'я та юніти для відображення на сторінці
    standard_name = db.query(StandardName).filter_by(id=standard_name_id).first()
    if not standard_name:
        raise HTTPException(status_code=404, detail="Стандартное ім'я не знайдено.")
    units = db.query(Unit).filter_by(standard_name_id=standard_name_id).all()

    return templates.TemplateResponse("calculator_result.html", {
        "request": request,
        "standard_name_id": standard_name_id,
        "standard_name": standard_name,
        "units": units,
        "result": result,
        "input_value": value
    })

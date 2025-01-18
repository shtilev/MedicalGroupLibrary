from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from medicalgrouplibrary.database import SessionLocal, StandardName, AnalysisSynonym
from medicalgrouplibrary.unificator import add_synonym

# Ініціалізація роутера
router = APIRouter()

# Шаблоны Jinja2
templates = Jinja2Templates(directory="templates")

# Функція для отримання сесії бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
async def read_unification_names(request: Request, db: Session = Depends(get_db)):
    # Отримання унікальних стандартних імен
    standard_names = db.query(StandardName).all()
    return templates.TemplateResponse("index.html", {"request": request, "standard_names": standard_names})


@router.get("/unification_names/", response_class=HTMLResponse)
async def read_unification_names(request: Request, filter_letter: str = None, db: Session = Depends(get_db)):
    # Отримання унікальних стандартних імен
    standard_names_query = db.query(StandardName)

    if filter_letter:
        # Фільтрація за першою літерою назви
        standard_names_query = standard_names_query.filter(StandardName.name.ilike(f"{filter_letter}%"))

    standard_names = standard_names_query.all()

    return templates.TemplateResponse("unification_names.html", {
        "request": request,
        "standard_names": standard_names,
        "filter_letter": filter_letter,
    })



@router.get("/synonyms/{standard_name_id}", response_class=HTMLResponse)
async def read_synonyms_by_name(request: Request, standard_name_id: int, db: Session = Depends(get_db)):
    # Находим стандартное имя по ID
    standard_name = db.query(StandardName).filter(StandardName.id == standard_name_id).first()
    if standard_name:
        synonyms = db.query(AnalysisSynonym).join(StandardName).filter(StandardName.id == standard_name_id).all()
        return templates.TemplateResponse("synonyms.html", {
            "request": request,
            "standard_name": standard_name,
            "synonyms": synonyms
        })
    return {"message": "Стандартне ім'я не знайдено"}


@router.post("/add", response_class=HTMLResponse)
async def add_synonym_route(request: Request, standard_name: str = Form(...), synonym: str = Form(...),
                             db: Session = Depends(get_db)):
    """
    Додає новий синонім, використовуючи функцію add_synonym.
    """
    # Викликаємо функцію для додавання синоніма
    add_synonym(standard_name, synonym)

    # Перенаправляємо на сторінку з синонімами для конкретного стандартного імені
    return RedirectResponse(f"/synonyms/{standard_name}", status_code=302)


@router.post("/add_synonym/{standard_name_id}", response_class=HTMLResponse)
async def add_synonym_route(standard_name_id: int, synonym: str = Form(...), db: Session = Depends(get_db)):
    """
    Додає новий синонім для вказаного стандартного імені.
    """
    # Отримуємо стандартне ім'я з бази по ID
    standard_entry = db.query(StandardName).filter_by(id=standard_name_id).first()
    if not standard_entry:
        raise HTTPException(status_code=404, detail="Стандартне ім'я не знайдено.")

    # Додаємо новий синонім
    new_synonym = AnalysisSynonym(synonym=synonym, standard_name_id=standard_entry.id)
    db.add(new_synonym)
    db.commit()

    # Перенаправляємо на сторінку з синонімами для цього стандартного імені
    return RedirectResponse(f"/synonyms/{standard_name_id}", status_code=302)



@router.post("/delete/{synonym_id}", response_class=HTMLResponse)
async def delete_synonym(synonym_id: int, db: Session = Depends(get_db)):
    # Видалення синоніма
    entry = db.query(AnalysisSynonym).filter_by(id=synonym_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Синонім не знайдено.")

    standard_name = entry.standard_name.name  # Отримуємо стандартне ім'я, пов'язане з синонімом

    db.delete(entry)
    db.commit()

    return RedirectResponse(f"/unification_names", status_code=302)


@router.post("/rename_standard_name/{standard_name_id}")
async def rename_standard_name(standard_name_id: int, new_standard_name: str = Form(...),
                               db: Session = Depends(get_db)):
    # Находим стандартное имя по ID
    standard_name = db.query(StandardName).filter(StandardName.id == standard_name_id).first()

    if standard_name:
        # Обновляем имя
        standard_name.name = new_standard_name
        db.commit()
        db.refresh(standard_name)

    # Перенаправляем обратно на страницу с синонимами
    return {"message": "Ім'я успішно змінено!"}

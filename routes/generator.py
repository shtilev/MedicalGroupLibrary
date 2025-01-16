from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from medicalgrouplibrary.database import SessionLocal, AnalysisSynonym
from tqdm import tqdm
from pydantic import BaseModel
from medicalgrouplibrary.data_creator import create_synonyms_for_standard_name
from medicalgrouplibrary.database import StandardName
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

# Ініціалізація роутера
router = APIRouter()


# Функція для отримання сесії бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Шаблони Jinja2
templates = Jinja2Templates(directory="templates")


@router.get("/generator", response_class=HTMLResponse)
async def import_export_page(request: Request, db: Session = Depends(get_db)):
    # Отримуємо всі уніфіковані назви
    unified_names = db.query(StandardName).all()
    unified_names_list = [name.name for name in unified_names]
    return templates.TemplateResponse("generator.html", {"request": request, "unified_names": unified_names_list, "message": None})



class SynonymRequest(BaseModel):
    standard_name: str
    request_count: int


@router.post("/generate_synonyms", response_class=HTMLResponse)
async def generate_synonyms(request: Request,
                            standard_name: str = Form(...),
                            request_count: int = Form(...),
                            db: Session = Depends(get_db)):
    try:
        # Перевіряємо кількість запитів
        if request_count <= 0:
            raise HTTPException(status_code=400, detail="Кількість запитів має бути більше нуля.")

        # Перевіряємо чи існує стандартне ім'я в таблиці StandardName
        existing_standard_name = db.query(StandardName).filter_by(name=standard_name).first()
        if not existing_standard_name:
            # Якщо не знайдено, створюємо нове уніфіковане ім'я
            pass  # Створення нового уніфікованого імені

        result = []
        # Генерація синонімів за допомогою LLM
        for _ in tqdm(range(request_count)):
            created_synonyms = create_synonyms_for_standard_name(standard_name)
            result.append(created_synonyms)
        message = f"Синоніми для '{standard_name}' успішно згенеровані. Було додано: {', '.join([', '.join(item) for item in result])}"

        # message = f"Синоніми для '{standard_name}' успішно згенеровані. Було додано:\n{str(result)}"
        return templates.TemplateResponse("generator.html",
                                          {"request": request,
                                           "message": message,
                                           "unified_names": [item.name for item in db.query(StandardName).distinct(AnalysisSynonym.standard_name).all()]})

    except Exception as e:
        message = f"Помилка при генерації синонімів: {e}"
        return templates.TemplateResponse("generator.html",
                                          {"request": request,
                                           "message": message,
                                           "unified_names": [item.name for item in db.query(StandardName).distinct(
                                               AnalysisSynonym.standard_name).all()]})

from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from medicalgrouplibrary.database import SessionLocal, AnalysisSynonym, StandardName
import tempfile
import json
from sqlalchemy.orm import Session

# Ініціалізація роутера
router = APIRouter()

# Шаблони Jinja2
templates = Jinja2Templates(directory="templates")

# Функція для отримання сесії бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/import_export", response_class=HTMLResponse)
async def import_export_page(request: Request, db: Session = Depends(get_db)):
    # Отримуємо усі стандартні імена для випадаючого списку
    standard_names = db.query(StandardName).all()
    return templates.TemplateResponse("import_export.html", {"request": request, "standard_names": standard_names})


# Маршрут для імпорту синонімів з JSON
@router.post("/import", response_class=HTMLResponse)
async def import_synonyms(request: Request, file: UploadFile = File(...), standard_name: str = Form(None), db: Session = Depends(get_db)):
    try:
        # Читаємо вміст файлу
        file_content = await file.read()
        synonyms_data = json.loads(file_content.decode("utf-8"))

        for entry in synonyms_data:
            if standard_name and entry['standard_name'] != standard_name:
                continue  # Пропускаємо записи, якщо не співпадає стандартне ім'я

            existing_synonym = db.query(AnalysisSynonym).filter_by(synonym=entry['synonym']).first()
            if not existing_synonym:
                synonym_entry = AnalysisSynonym(standard_name=entry['standard_name'], synonym=entry['synonym'])
                db.add(synonym_entry)

        db.commit()
        return templates.TemplateResponse("import_export.html", {"request": request, "message": "Синоніми успішно імпортовані."})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("import_export.html", {"request": request, "message": f"Помилка імпорту: {e}"})


@router.get("/export", response_class=FileResponse)
async def export_synonyms(request: Request, standard_name: str = None, db: Session = Depends(get_db)):
    try:
        if standard_name:
            synonyms_data = db.query(AnalysisSynonym).join(StandardName).filter(StandardName.name == standard_name).all()
        else:
            synonyms_data = db.query(AnalysisSynonym).all()

        data_to_export = [{"standard_name": entry.standard_name.name, "synonym": entry.synonym} for entry in synonyms_data]

        # Створюємо тимчасовий файл
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', newline='') as tmpfile:
            # Записуємо дані JSON у файл
            json.dump(data_to_export, tmpfile, ensure_ascii=False, indent=4)
            tmpfile.seek(0)
            # Повертання файлу як відповіді
            return FileResponse(tmpfile.name, media_type='application/json', filename="synonyms_export.json")

    except Exception as e:
        return templates.TemplateResponse("import_export.html", {"request": request, "message": f"Помилка експорту: {e}"})

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from medicalgrouplibrary.database import SessionLocal
from medicalgrouplibrary.unificator import get_unification_name

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


@router.get("/test_unificator/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("test_unificator.html", {"request": request})


@router.post("/test_unificator/", response_class=HTMLResponse)
async def process_unification_name(
        request: Request,
        synonym: str = Form(...),
        threshold: float = Form(...),
        db: Session = Depends(get_db),
):
    try:
        # Перевірка порогу схожості, якщо потрібно
        if not (0 <= threshold <= 100):
            raise HTTPException(status_code=400, detail="Поріг повинен бути між 0 і 100.")

        # Отримання результату функції уніфікації
        result = get_unification_name(synonym, threshold)

        # Повертаємо результат у шаблон
        return templates.TemplateResponse(
            "test_unificator.html",
            {"request": request, "result": result}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

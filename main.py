from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.synonyms import router as synonyms_router
from routes.data_transfer import router as data_transfer_router
from routes.generator import router as generator
from medicalgrouplibrary.database import init_db
from routes.test_unificator import router as unificator_router
from routes.units import router as units_router

# Инициализация приложения FastAPI
app = FastAPI()

# Створення БД локально
init_db()


# Подключение маршрутов
app.include_router(synonyms_router)
app.include_router(data_transfer_router)
app.include_router(generator)
app.include_router(unificator_router)
app.include_router(units_router)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Запуск FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Ініціалізація бази даних
DATABASE_URL = "sqlite:///db/ukr-analysis.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Модель таблиці стандартних імен
class StandardName(Base):
    __tablename__ = "standard_names"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Зв'язок з таблицею синонімів
    synonyms = relationship("AnalysisSynonym", back_populates="standard_name")

# Модель таблиці синонімів
class AnalysisSynonym(Base):
    __tablename__ = "analysis_synonyms"
    id = Column(Integer, primary_key=True, index=True)
    standard_name_id = Column(Integer, ForeignKey("standard_names.id"), nullable=False)
    synonym = Column(String, nullable=False)

    # Зв'язок з таблицею стандартних імен
    standard_name = relationship("StandardName", back_populates="synonyms")

    # Додаємо унікальне обмеження для пари (standard_name_id, synonym)
    __table_args__ = (
        UniqueConstraint("standard_name_id", "synonym", name="unique_standard_name_synonym_constraint"),
    )


def init_db():
    Base.metadata.create_all(bind=engine)


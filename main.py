from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey, Enum, UUID
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import Session
from enum import Enum as PyEnum
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import ARRAY


# Define database connection
DATABASE_URL = "postgresql+psycopg2://test:root@localhost:5432/exams"

# Initialize SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Enum types for SQLAlchemy
class QuestionType(PyEnum):
    MCQ = "MCQ"
    ShortAnswer = "Short Answer"
    LongAnswer = "Long Answer"
    TrueFalse = "True/False"
    Essay = "Essay"

class DifficultyLevel(PyEnum):
    Easy = "Easy"
    Medium = "Medium"
    Hard = "Hard"

# SQLAlchemy Models
class Exam(Base):
    __tablename__ = "Exam"

    exam_id = Column(UUID, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    grade_level = Column(Integer, nullable=True)
    instruction = Column(Text, nullable=True)


class Section(Base):
    __tablename__ = "Section"

    section_id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(UUID, ForeignKey("Exam.exam_id"), nullable=False)
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    referenced_text = Column(Text, nullable=True)
    weightage = Column(Integer, nullable=False)

class Question(Base):
    __tablename__ = "Question"

    question_id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("Section.section_id"), nullable=False)
    question_text = Column(Text, nullable=False)
    hint = Column(String, nullable=True)
    type = Column(Enum(QuestionType), nullable=False)
    marks = Column(Integer, nullable=False)
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False)
    options = Column(ARRAY(Text), nullable=True)
    correct_answer = Column(ARRAY(Text), nullable=True)
    tags = Column(ARRAY(Text), nullable=True)
    skills = Column(ARRAY(Text), nullable=True)
    figure_url = Column(Text, nullable=True)

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# Pydantic models for response
class ExamBase(BaseModel):
    title: str
    subject: str
    grade_level: Optional[int] = None
    instruction: Optional[str] = None

class QuestionResponse(BaseModel):
    question_id: int
    section_id: int
    question_text: str
    type: str
    marks: int
    difficulty_level: str
    options: Optional[List[str]]
    correct_answer: Optional[List[str]]
    tags: Optional[List[str]]
    skills: Optional[List[str]]
    figure_url: str

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


class SectionResponse(BaseModel):
    section_id: int
    exam_id: UUID
    title: str
    subtitle: str
    description: Optional[str]
    referenced_text: Optional[str]
    weightage: int
    questions: List[QuestionResponse] = []

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


class ExamResponse(BaseModel):
    exam_id: UUID
    title: str
    subject: str
    grade_level: Optional[int]
    instruction: Optional[str]
    sections: List[SectionResponse] = []

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True

# FastAPI app
app = FastAPI()

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Querying endpoint for exams
@app.get("/exams", response_model=List[ExamResponse])
def get_exams(db: Session = Depends(get_db), title: Optional[str] = None):
    query = db.query(Exam)
    if title:
        query = query.filter(Exam.title.ilike(f"%{title}%"))
    exams = query.all()
    return exams

# Run the app
# To run the app, use the following command in the terminal:
# uvicorn main:app --reload

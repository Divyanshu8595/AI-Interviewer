from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
DATABASE_URL = "sqlite:///./local_interviewer.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
class User(Base):
    __tablename__='users'; id=Column(Integer,primary_key=True); email=Column(String,unique=True,index=True); password_hash=Column(String); voice_preference=Column(String,default='female')
class Resume(Base):
    __tablename__='resumes'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=True); filename=Column(String); raw_text=Column(Text); structured=Column(JSON); created_at=Column(DateTime,server_default=func.now())
class Interview(Base):
    __tablename__='interviews'; id=Column(Integer,primary_key=True); resume_id=Column(Integer,ForeignKey('resumes.id')); company=Column(String); role=Column(String); difficulty=Column(String); memory=Column(JSON,default={}); created_at=Column(DateTime,server_default=func.now())
class Question(Base):
    __tablename__='questions'; id=Column(Integer,primary_key=True); interview_id=Column(Integer,ForeignKey('interviews.id')); category=Column(String); text=Column(Text)
class Answer(Base):
    __tablename__='answers'; id=Column(Integer,primary_key=True); question_id=Column(Integer,ForeignKey('questions.id')); transcript=Column(Text); evaluation=Column(JSON); score=Column(Float)
class Report(Base):
    __tablename__='reports'; id=Column(Integer,primary_key=True); interview_id=Column(Integer,ForeignKey('interviews.id')); content=Column(JSON); overall_score=Column(Float)
def init_db(): Base.metadata.create_all(bind=engine)
def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()

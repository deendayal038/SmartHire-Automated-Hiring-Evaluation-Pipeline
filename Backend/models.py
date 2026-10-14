from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class UserModel(Base):
    __tablename__="users"

    id=Column(Integer,primary_key=True,index=True,autoincrement=True)
    username=Column(String,unique=True,index=True, nullable=False)
    password=Column(String,nullable=False)
    role=Column(String,nullable=False)

class JobDescriptionModel(Base):
    __tablename__="job_descriptions"

    id=Column(String,primary_key=True,index=True)
    title=Column(String,nullable=False)
    must_have=Column(JSON,nullable=False)
    nice_to_have=Column(JSON,default=[])
    experience_years=Column(Integer,default=0)
    education=Column(String,nullable=True)
    location=Column(String,nullable=True)
    weights=Column(JSON,nullable=False)
    pass_threshold=Column(Float,default=70.0)
    confidence_cutoff=Column(Float,default=0.6)
    summary=Column(Text,nullable=True)

    #relationships
    questions=relationship("QuestionModel",back_populates="job_description",cascade="all, delete-orphan")
    candidates=relationship("CandidateModel",back_populates="job_description")

class QuestionModel(Base):
    __tablename__="questions"

    id=Column(String,primary_key=True, index=True)
    jd_id=Column(String, ForeignKey("job_descriptions.id"), nullable=False)
    text=Column(Text,nullable=False)
    reference_answer=Column(Text,nullable=False)
    rubric=Column(JSON,nullable=False)

    #relationships
    job_description=relationship("JobDescriptionModel",back_populates="questions")
    candidate_answers=relationship("CandidateAnswerModel",back_populates="question")

class CandidateModel(Base):
    __tablename__="candidates"

    id=Column(String,primary_key=True,index=True)
    user=Column(String,unique=True,index=True, nullable=False)
    name=Column(String,nullable=False)
    email=Column(String,nullable=False)
    applied_jd=Column(String, ForeignKey("job_descriptions.id"),nullable=False)
    experience_years=Column(Integer,default=0)
    education=Column(String,nullable=True)
    location=Column(String,nullable=True)
    profile_type=Column(String,nullable=True)
    resume=Column(Text,nullable=False)

    resume_score=Column(Float,nullable=True)
    resume_gaps=Column(JSON,nullable=True)
    matched_skills=Column(JSON,nullable=True)
    qa_score=Column(Float,nullable=True)
    combined_score=Column(Float,nullable=True)
    decision_band=Column(String,nullable=True)

    discrepancy_flags=Column(Boolean,default=False)
    discrepancy_reason=Column(String,nullable=True)
    anti_cheat_flags=Column(JSON,nullable=True)

    assigned_interviewer=Column(String,nullable=True)
    interview_date=Column(String,nullable=True)
    interview_status=Column(String,default="PENDING")
    interview_notes=Column(Text,nullable=True)

    #relationships
    job_description=relationship("JobDescriptionModel",back_populates="candidates")
    answers=relationship("CandidateAnswerModel",back_populates="candidate",cascade="all,delete-orphan")

class CandidateAnswerModel(Base):
    __tablename__="candidate_answers"

    id=Column(Integer,primary_key=True,index=True,autoincrement=True)
    candidate_id=Column(String,ForeignKey("candidates.id"))
    question_id=Column(String,ForeignKey("questions.id"))
    answer_text=Column(Text)
    score=Column(Float,nullable=True)
    justification=Column(Text,nullable=True)
    Confidence=Column(Float,nullable=True)
    rubric_hits=Column(JSON,nullable=True)

    #relationships
    candidate=relationship("CandidateModel",back_populates="answers")
    question=relationship("QuestionModel",back_populates="candidate_answers")

class AuditLogModel(Base):
    __tablename__="audit_logs"

    id=Column(Integer,primary_key=True,index=True,autoincrement=True)
    candidate_id=Column(String)
    action=Column(String)
    details=Column(Text)
    timestamp=Column(DateTime,default=datetime.utcnow)
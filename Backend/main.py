from models import CandidateModel,JobDescriptionModel,UserModel,CandidateAnswerModel,AuditLogModel,QuestionModel
from contextlib import asynccontextmanager
from pydantic import BaseModel
from datetime import datetime
from typing import Optional,List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine,SessionLocal,Base,get_db
from seeder import seed_database
from auth import (
    LoginRequest,
    TokenResponse,
    create_access_token,
    get_current_user,
    require_role
)
from pipeline import (
    screen_candidate_resume,
    grade_candidate_answer,
    compute_decision_and_flags,
    run_full_pipeline
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] initializing in-Memory SQLite schema...")
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        print("[STARTUP] seeding initial dataset from Input_Data.json...")
        seed_database(db)

    yield

    print("[SHUTDOWN] SmartHire backend shutting down...")

app=FastAPI(
    title="SmartHire API",
    description="Automated Hiring & Evaluation Pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status":"ok","service":"SmartHire API"}

@app.get("/api/jds")
def get_job_descriptions(db: Session=Depends(get_db)):
    jobs=db.query(JobDescriptionModel).all()
    return jobs

@app.get("/api/candidates")
def get_candidates(db:Session=Depends(get_db)):
    candidates=db.query(CandidateModel).all()
    return candidates

@app.post("/api/login",response_model=TokenResponse)
def login(request:LoginRequest,db:Session=Depends(get_db)):
    user=db.query(UserModel).filter(UserModel.username==request.username).first()

    if not user or user.password!=request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token_payload={"sub":user.username,"role":user.role}
    access_token=create_access_token(data=token_payload)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )

@app.get("/api/auth/me")
def get_current_user_profile(current_user: UserModel=Depends(get_current_user)):
    return {"username":current_user.username,"role":current_user.role}

@app.get("/api/admin/dashboard-access")
def test_admin_access(current_user:UserModel=Depends(require_role(["admin"]))):
    return {"message":f"Access granted to Admin {current_user.username}","role":current_user.role}

@app.get("/api/candidate/portal-access")
def test_candidate_access(current_user:UserModel=Depends(require_role(["candidate"]))):
    return {"message":f"Access granted to Candidate {current_user.username}","role":current_user.role}

@app.get("/api/interviewer/queue-access")
def test_interviewer_access(current_user:UserModel=Depends(require_role(["interviewer"]))):
    return {"message":f"Access granted to Interviewer {current_user.username}","role":current_user.role}

class AssignInterviewerRequest(BaseModel):
    interviewer_username:str
    interview_date:Optional[str]=None

class AnswerSubmissionItem(BaseModel):
    question_id:str
    answer_text:str

class SubmitTestResponse(BaseModel):
    answers:List[AnswerSubmissionItem]
    tab_switches:int=0
    copy_pastes:int=0

class InterviewerNotesRequest(BaseModel):
    interview_status:str
    interview_notes:str

@app.get("/api/admin/candidates")
def admin_get_all_candidates(
    decision_band:Optional[str]=None,
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["admin"]))
):
    query=db.query(CandidateModel)
    if decision_band:
        query=query.filter(CandidateModel.decision_band==decision_band.upper())

    return query.all()

@app.post("/api/admin/candidates/{candidate_id}/screen-resume")
def admin_screen_resume(
    candidate_id:str,
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["admin"]))
):
    try:
        result=screen_candidate_resume(candidate_id,db)
        return {"status":"success","result":result}

    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e))

@app.post("/api/admin/candidates/{candidate_id}/evaluate-full")
def admin_evaluate_full_candidate(
    candidate_id:str,
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["admin"]))
):
    try:
        candidate=run_full_pipeline(candidate_id,db)
        return {
            "status": "success",
            "candidate_id": candidate.id,
            "resume_score": candidate.resume_score,
            "qa_score": candidate.qa_score,
            "combined_score": candidate.combined_score,
            "decision_band": candidate.decision_band,
            "discrepancy_flags": candidate.discrepancy_flags,
            "discrepancy_reason": candidate.discrepancy_reason,
        }
    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e))

@app.put("/api/admin/candidates/{candidate_id}/assign-interviewer")
def admin_assign_interviewer(
    candidate_id:str,
    request:AssignInterviewerRequest,
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["admin"]))
):
    candidate=db.query(CandidateModel).filter(CandidateModel.id==candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404,detail="Candidate not found")

    candidate.assigned_interviewer=request.interviewer_username
    if request.interview_date:
        candidate.interview_date=request.interview_date
    candidate.interview_status="SCHEDULED"
    db.commit()

    return {
        "status": "success",
        "message": f"Candidate {candidate_id} assigned to {request.interviewer_username}",
    }

@app.get("/api/candidate/test")
def candidate_get_test_questions(
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["candidate"]))
):
    candidate=db.query(CandidateModel).filter(CandidateModel.user==current_user.username).first()
    if not candidate:
        raise HTTPException(status_code=404,detail="candidate profile not found")
    questions=db.query(QuestionModel).filter(QuestionModel.jd_id==candidate.applied_jd).all()
    masked_questions=[{"id":q.id,"text":q.text} for q in questions]

    return {
        "candidate_id":candidate.id,
        "applied_jd":candidate.applied_jd,
        "questions":masked_questions,
    }

@app.post("/api/candidate/submit-test")
def candidate_submit_test(
    submission:SubmitTestResponse,
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["candidate"]))
):
    candidate = db.query(CandidateModel).filter(CandidateModel.user == current_user.username).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    db.query(CandidateAnswerModel).filter(CandidateAnswerModel.candidate_id==candidate.id).delete()

    for item in submission.answers:
        answer_record=CandidateAnswerModel(
            candidate_id=candidate.id,
            question_id=item.question_id,
            answer_text=item.answer_text,
        )
        db.add(answer_record)

        candidate.anti_cheat_flags={
            "tab_switches":submission.tab_switches,
            "copy_pastes":submission.copy_pastes,
        }
        db.commit()

        grade_candidate_answer(candidate.id,db)
        compute_decision_and_flags(candidate.id,db)

        return {
        "status": "success",
        "message": "Assessment submitted and evaluated successfully.",
        }

@app.get("/api/candidate/my-status")
def candidate_get_status(
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["candidate"]))
):
    candidate=db.query(CandidateModel).filter(CandidateModel.user==current_user.username).first()
    if not candidate:
        raise HTTPException(status_code=404,detail="candidate profile not found")

    return {
        "candidate_id":candidate.id,
        "name":candidate.name,
        "applied_jd":candidate.applied_jd,
        "status":candidate.interview_status,
        "decision_band":candidate.decision_band,
        "interview_date":candidate.interview_date,
    }

@app.get("/api/interviewer/my-candidates")
def interviewer_get_assigned_candidates(
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["interviewer"]))
):
    candidates=db.query(CandidateModel).filter(CandidateModel.assigned_interviewer==current_user.username).all()
    return candidates

@app.put("/api/interviewer/candidates/{candidate_id}/notes")
def interviewer_update_notes(
    candidate_id:str,
    request:InterviewerNotesRequest,
    db:Session=Depends(get_db),
    current_user:UserModel=Depends(require_role(["interviewer"]))
):
    candidate=db.query(CandidateModel).filter(CandidateModel.id==candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404,detail="candidate not found or not assigned to you.")

    candidate.interview_status=request.interview_status

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    new_entry = f"[{timestamp} by {current_user.username}]: {request.interview_notes}"
    if candidate.interview_notes:
        candidate.interview_notes+=f"\n\n{new_entry}"
    else:
        candidate.interview_notes=new_entry

    db.commit()

    return {
        "status": "success",
        "message": f"Interview notes updated for candidate {candidate_id}",
    }
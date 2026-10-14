from datetime import datetime
from sqlalchemy.orm import Session
import json
from models import (
    CandidateAnswerModel,
    CandidateModel,
    UserModel,
    QuestionModel,
    JobDescriptionModel,
    AuditLogModel
)
from ai_engine import evaluate_answer,evaluate_resume

def screen_candidate_resume(candidate_id:str,db:Session)-> dict:
    candidate=db.query(CandidateModel).filter(CandidateModel.id==candidate_id).first()
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found.")
    jd=db.query(JobDescriptionModel).filter(JobDescriptionModel.id==candidate.applied_jd).first()
    if not jd:
        raise ValueError(f"Job Description {candidate.applied_jd} not found.")
    jd_data={
        "title":jd.title,
        "must_have":jd.must_have,
        "nice_to_have":jd.nice_to_have,
        "experience_years":jd.experience_years,
        "summary":jd.summary,
    }
    ai_result=evaluate_resume(resume_text=candidate.resume,jd_data=jd_data)

    candidate.resume_score=round(float(ai_result.get("score",0.0)),2)
    candidate.resume_gaps=ai_result.get("gaps",[])
    candidate.matched_skills=ai_result.get("matched_skills",[])

    log = AuditLogModel(
        candidate_id=candidate.id,
        action="RESUME_EVALUATION",
        details=json.dumps({
            "resume_score": candidate.resume_score,
            "confidence": ai_result.get("confidence", 1.0),
            "reasoning": ai_result.get("reasoning", ""),
        }),
    )
    db.add(log)
    db.commit()

    return ai_result

def grade_candidate_answer(candidate_id:str,db:Session)->float:
    candidate=db.query(CandidateModel).filter(CandidateModel.id==candidate_id).first()
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found.")
    answers=db.query(CandidateAnswerModel).filter(CandidateAnswerModel.candidate_id==candidate_id).all()
    if not answers:
        candidate.qa_score=0.0
        db.commit()
        return 0.0

    total_points_earned=0.0
    max_possible_points=len(answers)*5.0

    for ans in answers:
        question=db.query(QuestionModel).filter(QuestionModel.id==ans.question_id).first()
        if not question:
            continue

        grading_result=evaluate_answer(
            question_text=question.text,
            reference_answer=question.reference_answer,
            rubric=question.rubric,
            candidate_answer=ans.answer_text,
        )

        ans.score=round(float(grading_result.get("score",0.0)),2)
        ans.rubric_hits=grading_result.get("rubric_hits",[])
        ans.justification=grading_result.get("justification","")
        total_points_earned+=ans.score

    normalized_qa_score=round((total_points_earned/max_possible_points)*100,2)
    candidate.qa_score=normalized_qa_score
    db.commit()

    return normalized_qa_score

def compute_decision_and_flags(candidate_id:str,db:Session)-> CandidateModel:
    candidate=db.query(CandidateModel).filter(CandidateModel.id==candidate_id).first()
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found.")
    jd=db.query(JobDescriptionModel).filter(JobDescriptionModel.id==candidate.applied_jd).first()
    if not jd:
        raise ValueError(f"Job Description {candidate.applied_jd} not found.")

    resume_score=candidate.resume_score or 0.0
    qa_score=candidate.qa_score or 0.0

    weights=jd.weights or {"resume":0.6,"qa":0.4}
    w_resume=float(weights.get("resume",0.6))
    w_qa=float(weights.get("qa",0.4))

    final_score=round((w_resume*resume_score)+(w_qa*qa_score),2)
    candidate.combined_score=final_score

    discrepancy_reasons=[]

    if resume_score>=70.0 and qa_score<45.0:
        discrepancy_reasons.append("High resume score but poor technical Q&A demonstration (Overclaiming flag).")

    if candidate.anti_cheat_flags:
        switches=candidate.anti_cheat_flags.get("tab_switches",0)
        pastes=candidate.anti_cheat_flags.get("copy_pastes",0)

        if switches>=3 or pastes>=3:
            discrepancy_reasons.append(f"Suspicious test telemetry: {switches} tab switches, {pastes} copy-pastes.")

    if discrepancy_reasons:
        candidate.discrepancy_flags=True
        candidate.discrepancy_reason=" | ".join(discrepancy_reasons)
    else:
        candidate.discrepancy_flags=False
        candidate.discrepancy_reason=None

    pass_bar=float(jd.pass_threshold)

    if final_score>=pass_bar and not candidate.discrepancy_flags:
        candidate.decision_band="PASS"

    elif final_score>=(pass_bar-10.0) or candidate.discrepancy_flags:
        candidate.decision_band="HOLD"

    else:
        candidate.decision_band="REJECT"

    log=AuditLogModel(
        candidate_id=candidate.id,
        action="DECISION_BANDING_COMPLETED",
        details=json.dumps({
            "combined_score": candidate.combined_score,
            "decision_band": candidate.decision_band,
            "discrepancy_flags": candidate.discrepancy_flags,
            "discrepancy_reason": candidate.discrepancy_reason,
        }),
    )
    db.add(log)
    db.commit()

    return candidate

def run_full_pipeline(candidate_id:str,db:Session)->CandidateModel:
    screen_candidate_resume(candidate_id,db)
    grade_candidate_answer(candidate_id,db)
    return compute_decision_and_flags(candidate_id,db)
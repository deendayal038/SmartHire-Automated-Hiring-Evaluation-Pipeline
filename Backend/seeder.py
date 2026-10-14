import json
from pathlib import Path
from sqlalchemy.orm import Session
from database import SessionLocal,Base,engine
from models import UserModel,JobDescriptionModel,QuestionModel,CandidateModel

def seed_database(db: Session)-> None:
    if db.query(UserModel).first():
        print("[SEEDER] Database already contains records. Skipping seed.")
        return

    json_path=Path(__file__).resolve().parent/"Input_Data.json"

    if not json_path.exists():
        raise FileNotFoundError(
            f"[SEEDER ERROR] Could not find Input_Data.json at path: {json_path}. "
            "Please ensure Input_Data.json is placed inside the SmartHire/Backend folder."
        )

    print(f"[SEEDER] Loading dataset from: {json_path}")
    with open(json_path,"r",encoding="utf-8") as file:
        data=json.load(file)

    try:
        users_data=data.get("users",[])
        for u in users_data:
            user=UserModel(
                username=u["username"],
                role=u["role"],
                password=u["password"],
            )
            db.add(user)
        print(f"[SEEDER] Staged {len(users_data)} users.")

        jd_data=data.get("job_descriptions",[])
        for jd in jd_data:
            job=JobDescriptionModel(
                id=jd["id"],
                title=jd["title"],
                must_have=jd["must_have"],
                nice_to_have=jd["nice_to_have"],
                experience_years=jd["experience_years"],
                education=jd["education"],
                location=jd["location"],
                weights=jd["weights"],
                pass_threshold=jd["pass_threshold"],
                confidence_cutoff=jd["confidence_cutoff"],
                summary=jd["summary"],
            )
            db.add(job)
        print(f"[SEEDER] staged {len(jd_data)} job descriptions.")

        q_data=data.get("questions",[])
        for q in q_data:
            question=QuestionModel(
                id=q["id"],
                jd_id=q["jd_id"],
                text=q["text"],
                reference_answer=q["reference_answer"],
                rubric=q["rubric"],
            )
            db.add(question)
        print(f"[SEEDER] staged {len(q_data)} assessment questions.")

        cand_data=data.get("candidates",[])
        for c in cand_data:
            candidate=CandidateModel(
                id=c["id"],
                user=c["user"],
                name=c["name"],
                email=c["email"],
                applied_jd=c["applied_jd"],
                experience_years=c["experience_years"],
                education=c["education"],
                location=c["location"],
                profile_type=c["profile_type"],
                resume=c["resume"],
            )
            db.add(candidate)
        print(f"[SEEDER] staged {len(cand_data)} candidates.")

        db.commit()
        print("[SEEDER] database seeding successfully completed.")

    except Exception as e:
        db.rollback()
        print(f"[SEEDER] failed to seed database:{e}")
        raise e

if __name__=="__main__":
    print("[SEEDER] Running standalone database verification...")
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        seed_database(session)

        u_count=session.query(UserModel).count()
        jd_count=session.query(JobDescriptionModel).count()
        q_count=session.query(QuestionModel).count()
        c_count=session.query(CandidateModel).count()

        print("\n--- IN-MEMORY DATABASE SUMMARY ---")
        print(f"Users seeded:            {u_count} (Expected: 14)")
        print(f"Job Descriptions seeded: {jd_count} (Expected: 3)")
        print(f"Questions seeded:        {q_count} (Expected: 18)")
        print(f"Candidates seeded:       {c_count} (Expected: 10)")
        print("----------------------------------\n")
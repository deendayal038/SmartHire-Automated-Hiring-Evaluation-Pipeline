import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("[WARNING] GEMINI_API_KEY not found in environment. AI evaluations will use deterministic fallbacks.")
    client=None
else:
    client=genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME="gemini-3.5-flash-lite"

def _clean_and_parse_json(raw_text:str)->dict:
    cleaned=raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned=cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned=cleaned[3:]
    if cleaned.endswith("```"):
        cleaned=cleaned[:-3]
    return json.loads(cleaned.strip())

def _call_gemini_json(prompt:str,max_retries:int=1)->dict:
    if not client:
        raise ValueError("Gemini client is not initialized. Please set GEMINI_API_KEY.")

    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1,
    )

    last_error=None

    for attempt in range(max_retries+1):
        try:
            response=client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config,
            )
            return _clean_and_parse_json(response.text)

        except Exception as e:
            last_error=e
            print(f"[AI ENGINE] JSON parse/API attempt {attempt + 1} failed: {e}")

    raise RuntimeError(f"Failed to obtain valid JSON from Gemini after retry: {last_error}")

def evaluate_resume(resume_text:str,jd_data:dict)->dict:

    prompt = f"""
You are an expert technical hiring evaluator. Evaluate the candidate's resume against the Job Description strictly.
JOB DESCRIPTION:
- Title: {jd_data.get('title')}
- Must-Have Skills: {json.dumps(jd_data.get('must_have', []))}
- Nice-To-Have Skills: {json.dumps(jd_data.get('nice_to_have', []))}
- Required Experience: {jd_data.get('experience_years')} years
- Summary: {jd_data.get('summary')}
CANDIDATE RESUME:
\"\"\"{resume_text}\"\"\"
EVALUATION RULES:
1. Heavily penalize missing Must-Have skills. If a must-have skill is missing, score must not exceed 70.
2. Award bonus points for Nice-To-Have skills up to 100.
3. Detect overclaiming: If candidate claims dozens of complex enterprise tools with very little experience, lower the confidence score.
4. Output MUST be a valid JSON object matching this exact schema:
{{
  "score": <float between 0.0 and 100.0>,
  "matched_skills": [<list of matched skills found in resume>],
  "gaps": [<list of missing must-have or critical skills>],
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<concise 2-sentence explanation of the score>"
}}
"""
    try:
        return _call_gemini_json(prompt)
    except Exception as e:
        print(f"[AI ENGINE] Fallback triggered for resume evaluation: {e}")

        return {
            "score": 50.0,
            "matched_skills": [],
            "gaps": ["Evaluation fallback triggered"],
            "confidence": 0.5,
            "reasoning": "Automated fallback evaluation due to API error.",
            "fallback": True,
        }

def evaluate_answer(
        question_text:str,
        reference_answer:str,
        rubric:dict,
        candidate_answer:str
)-> dict:
    
    prompt = f"""
You are an objective technical interviewer grading a candidate's answer.
QUESTION:
{question_text}
REFERENCE ANSWER:
{reference_answer}
SCORING RUBRIC:
- Full Credit (5 Points Criteria): {json.dumps(rubric.get('score_5', []))}
- Partial Credit (3 Points Criteria): {json.dumps(rubric.get('score_3', []))}
- Zero Credit (0 Points Criteria): {json.dumps(rubric.get('score_0', []))}
CANDIDATE'S SUBMITTED ANSWER:
\"\"\"{candidate_answer}\"\"\"
GRADING RULES:
1. Score from 0.0 to 5.0 strictly based on rubric criteria satisfied.
2. Identify which specific rubric bullet points the candidate hit.
3. Provide a clear justification (this will be kept internal for hiring managers).
4. Output MUST be a valid JSON object matching this exact schema:
{{
  "score": <float between 0.0 and 5.0>,
  "rubric_hits": [<list of strings of specific rubric bullet points satisfied>],
  "justification": "<concise justification explaining why this score was awarded>"
}}
"""

    try:
        return _call_gemini_json(prompt)
    except Exception as e:
        print(f"[AI ENGINE] Fallback triggered for Q&A evaluation: {e}")
        
        return {
            "score": 0.0,
            "rubric_hits": [],
            "justification": "Automated fallback evaluation due to API error.",
            "fallback": True,
        }
# SmartHire: Automated Hiring & Evaluation Pipeline

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-AI-8E75B2?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![JWT](https://img.shields.io/badge/Auth-JWT-000000?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Uvicorn](https://img.shields.io/badge/Server-Uvicorn-4051B5)](https://www.uvicorn.org/)
[![License](https://img.shields.io/badge/License-Add_a_license-lightgrey)](#license)

SmartHire is a role-based automated technical hiring pipeline built with
**FastAPI, SQLAlchemy, and Google Gemini AI**. It supports resume
screening, timed technical assessments, rubric-based answer grading,
discrepancy detection, interviewer feedback, and decision banding
(`PASS`, `HOLD`, or `REJECT`).

> **Note:** SmartHire is an evaluation-support tool. AI scores and
> automated flags should be reviewed by qualified hiring staff and
> should not be treated as the sole basis for an employment decision.

------------------------------------------------------------------------

## Table of Contents

-   [Overview](#overview)
-   [Key Features](#key-features)
-   [Tech Stack](#tech-stack)
-   [System Workflow](#system-workflow)
-   [Project Structure](#project-structure)
-   [Prerequisites](#prerequisites)
-   [Quickstart](#quickstart)
    -   [1. Clone the Repository](#1-clone-the-repository)
    -   [2. Create a Virtual
        Environment](#2-create-a-virtual-environment)
    -   [3. Install Dependencies](#3-install-dependencies)
    -   [4. Configure Environment
        Variables](#4-configure-environment-variables)
    -   [5. Run the Backend](#5-run-the-backend)
-   [Benchmark Users](#benchmark-users)
-   [API Reference](#api-reference)
    -   [Authentication](#authentication)
    -   [Admin Endpoints](#admin-endpoints)
    -   [Candidate Endpoints](#candidate-endpoints)
    -   [Interviewer Endpoints](#interviewer-endpoints)
-   [Evaluation Logic](#evaluation-logic)
-   [Security and Data Handling](#security-and-data-handling)
-   [Configuration Notes](#configuration-notes)
-   [Troubleshooting](#troubleshooting)
-   [Future Improvements](#future-improvements)
-   [Contributing](#contributing)
-   [License](#license)

------------------------------------------------------------------------

## Overview

SmartHire organizes technical hiring into a consistent pipeline:

1.  An administrator reviews candidates and triggers resume screening.
2.  Candidates complete a technical assessment in the candidate portal.
3.  The AI engine evaluates answers against reference answers and
    structured rubrics.
4.  The pipeline combines resume and assessment scores, then checks for
    discrepancies and suspicious assessment telemetry.
5.  Administrators review results and assign candidates to interviewers.
6.  Interviewers record timestamped feedback for their assigned
    candidates.

The repository includes a benchmark dataset in `Backend/Input_Data.json`
for local testing.

## Key Features

### Role-Based Access Control (RBAC)

JWT-secured routes separate access for three personas:

-   **Admin / Hiring Manager:** View the candidate pipeline, run AI
    screening and full evaluations, and assign interviewers.
-   **Candidate:** Retrieve assessment questions, submit answers and
    client telemetry, and view application status.
-   **Interviewer:** View the assigned candidate queue and add
    timestamped interview notes.

### AI-Powered Resume Screening

-   Compares candidate resume information with a job description.
-   Produces a score on a 0--100 scale.
-   Identifies matched skills and potential skill gaps.
-   Uses structured JSON output for downstream processing.

### Rubric-Based Technical Assessment

-   Grades candidate answers against reference answers and defined
    rubrics.
-   Uses a 0--5 scoring scale for each answer.
-   Keeps reference answers and grading rubrics hidden from
    candidate-facing responses.
-   Uses JSON response formatting, retry handling, and fallback behavior
    in the AI integration.

### Weighted Decision Banding

-   Combines resume and technical assessment scores using configurable
    weights.
-   Assigns a decision band: `PASS`, `HOLD`, or `REJECT`.
-   Flags large differences between strong resume claims and weaker
    technical demonstrations for human review.

### Anti-Cheat Telemetry

-   Accepts assessment telemetry such as tab-switch and copy/paste event
    counts.
-   Flags patterns that may warrant review.
-   Telemetry is an indicator for review, not proof of misconduct.

### Audit Trail

-   Records pipeline actions in append-only audit logs to support
    traceability.
-   Supports timestamped interviewer feedback.

### In-Memory Database

-   Uses SQLite with SQLAlchemy and `StaticPool` for a shared in-memory
    database connection pattern.
-   The database is ephemeral: data is normally lost when the
    application process stops or restarts.

## Tech Stack

  -------------------------------------------------------------------------------------------------
  Technology                                                    Purpose
  ------------------------------------------------------------- -----------------------------------
  [Python](https://www.python.org/)                             Backend programming language

  [FastAPI](https://fastapi.tiangolo.com/)                      REST API framework and automatic
                                                                OpenAPI documentation

  [SQLAlchemy](https://www.sqlalchemy.org/)                     ORM and relational data access

  [SQLite](https://www.sqlite.org/)                             In-memory relational database for
                                                                local/demo use

  [Pydantic v2](https://docs.pydantic.dev/)                     Request validation, response
                                                                schemas, and DTOs

  [PyJWT](https://pyjwt.readthedocs.io/)                        JWT encoding and verification

  [Google GenAI SDK](https://ai.google.dev/gemini-api/docs)     Gemini model integration

  [Uvicorn](https://www.uvicorn.org/)                           ASGI server

  [python-dotenv](https://github.com/theskumar/python-dotenv)   Environment variable loading

  [Git](https://git-scm.com/)                                   Version control
  -------------------------------------------------------------------------------------------------

## System Workflow

``` text
                    +----------------------+
                    | Admin / Hiring Team  |
                    +----------+-----------+
                               |
                               v
+-------------+       +--------+---------+       +------------------+
| Candidate   +------>| FastAPI Backend  +------>| SQLAlchemy /     |
| Portal      |       | JWT + RBAC       |       | SQLite Database  |
+-------------+       +--------+---------+       +------------------+
                               |
                    +----------+-----------+
                    |                      |
                    v                      v
           +----------------+      +-------------------+
           | Gemini AI      |      | Evaluation        |
           | Resume + Q&A   |      | Pipeline          |
           +----------------+      +---------+---------+
                                             |
                                  +----------+----------+
                                  | Score + Flags +     |
                                  | PASS/HOLD/REJECT    |
                                  +----------+----------+
                                             |
                                             v
                                  +---------------------+
                                  | Interviewer Portal  |
                                  | Notes and feedback  |
                                  +---------------------+
```

## Project Structure

``` text
SmartHire/
├── Backend/
│   ├── database.py       # In-memory SQLite engine and StaticPool setup
│   ├── models.py         # SQLAlchemy relational models
│   ├── seeder.py         # Seeds benchmark data from Input_Data.json
│   ├── auth.py           # JWT utilities and RBAC dependencies
│   ├── ai_engine.py      # Gemini prompts, JSON handling, and AI evaluation
│   ├── pipeline.py       # Weighted scoring, discrepancy checks, decision banding
│   ├── main.py           # FastAPI application and role-protected endpoints
│   └── Input_Data.json   # Benchmark users, job descriptions, and questions
├── Frontend/             # Admin, Candidate, and Interviewer portal interfaces
├── .gitignore
└── README.md
```

The backend filenames above describe the intended responsibilities.
Refer to the source files for the exact implementation and current
behavior.

## Prerequisites

-   Python **3.10 or higher**
-   Git
-   A Google Gemini API key with access to the configured model
-   A terminal such as PowerShell, Command Prompt, or a Unix shell

## Quickstart

### 1. Clone the Repository

Replace the placeholder URL with the actual repository URL.

``` bash
git clone https://github.com/your-username/smarthire-pipeline.git
cd smarthire-pipeline/Backend
```

### 2. Create a Virtual Environment

**Windows --- PowerShell or Command Prompt**

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, use Command Prompt:

``` bat
venv\Scripts\activate.bat
```

**macOS / Linux**

``` bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

``` bash
python -m pip install --upgrade pip
pip install fastapi "uvicorn[standard]" pydantic sqlalchemy pyjwt python-dotenv google-genai
```

If the repository contains a `requirements.txt`, you can install the
pinned project dependencies instead:

``` bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the `Backend/` directory:

``` env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

Keep `.env` private and ensure it is excluded by `.gitignore`. Never
commit API keys, JWT signing secrets, or other credentials.

### 5. Run the Backend

From the `Backend/` directory, run:

``` bash
uvicorn main:app --reload --port 8000
```

When the server starts, open:

-   **API base URL:** http://127.0.0.1:8000
-   **Swagger UI:** http://127.0.0.1:8000/docs
-   **ReDoc:** http://127.0.0.1:8000/redoc

The database and benchmark seeding behavior depend on the application's
startup implementation. With an in-memory database, stopping or
restarting the process generally clears runtime data.

## Benchmark Users

The project description specifies 14 seeded benchmark users. The
following credentials are the documented examples; check
`Input_Data.json` and the seeder for the complete list.

  -----------------------------------------------------------------------
  Username          Role              Default Password  Purpose
  ----------------- ----------------- ----------------- -----------------
  `admin1`          Admin             `admin123`        Hiring manager
                                                        with evaluation
                                                        access

  `admin2`          Admin             `admin123`        Additional admin
                                                        test account

  `candidate1`      Candidate         `cand123`         Strong frontend
                                                        benchmark
                                                        candidate
                                                        (`cand-1`)

  `candidate2`      Candidate         `cand123`         Candidate missing
                                                        a must-have
                                                        TypeScript skill
                                                        (`cand-2`)

  `candidate7`      Candidate         `cand123`         Overclaiming
                                                        junior candidate
                                                        (`cand-7`)

  `candidate10`     Candidate         `cand123`         Data science
                                                        background
                                                        applying for a
                                                        backend role
                                                        (`cand-10`)

  `interviewer1`    Interviewer       `int123`          Interviewer with
                                                        an assigned queue
                                                        and notes

  `interviewer2`    Interviewer       `int123`          Additional
                                                        interviewer test
                                                        account
  -----------------------------------------------------------------------

> **Security warning:** These are demo credentials only.

## API Reference

All endpoints below are relative to `http://127.0.0.1:8000`. Protected
endpoints require a valid bearer token unless otherwise configured by
the application.

### Authentication

  -----------------------------------------------------------------------
  Method                  Endpoint                Description
  ----------------------- ----------------------- -----------------------
  `POST`                  `/api/login`            Authenticate a user and
                                                  return a signed JWT
                                                  containing role
                                                  information

  `GET`                   `/api/auth/me`          Validate the bearer
                                                  token and return the
                                                  logged-in profile
  -----------------------------------------------------------------------

After login, include the token in protected requests:

``` http
Authorization: Bearer <your_access_token>
```

### Admin Endpoints

Admin-only operations for candidate screening and pipeline management.

  -------------------------------------------------------------------------------------------------
  Method                  Endpoint                                          Description
  ----------------------- ------------------------------------------------- -----------------------
  `GET`                   `/api/admin/candidates`                           List candidates;
                                                                            supports
                                                                            `?decision_band=HOLD`

  `POST`                  `/api/admin/candidates/{id}/screen-resume`        Run AI resume screening
                                                                            for a candidate

  `POST`                  `/api/admin/candidates/{id}/evaluate-full`        Run the full evaluation
                                                                            pipeline

  `PUT`                   `/api/admin/candidates/{id}/assign-interviewer`   Assign a candidate to
                                                                            an interviewer
  -------------------------------------------------------------------------------------------------

### Candidate Endpoints

Candidate-facing routes should return only information appropriate for
the candidate. Gold answers and internal grading rubrics must remain
masked.

  ------------------------------------------------------------------------------
  Method                  Endpoint                       Description
  ----------------------- ------------------------------ -----------------------
  `GET`                   `/api/candidate/test`          Fetch technical
                                                         assessment questions

  `POST`                  `/api/candidate/submit-test`   Submit answers and
                                                         client-side anti-cheat
                                                         telemetry

  `GET`                   `/api/candidate/my-status`     View application status
                                                         and decision band
  ------------------------------------------------------------------------------

### Interviewer Endpoints

Interviewer routes are intended to limit access to candidates assigned
to the logged-in interviewer.

  ------------------------------------------------------------------------------------------
  Method                  Endpoint                                   Description
  ----------------------- ------------------------------------------ -----------------------
  `GET`                   `/api/interviewer/my-candidates`           List candidates
                                                                     assigned to the current
                                                                     interviewer

  `PUT`                   `/api/interviewer/candidates/{id}/notes`   Update interview status
                                                                     and append timestamped
                                                                     notes
  ------------------------------------------------------------------------------------------

For exact request fields, response schemas, and authentication behavior,
use the generated API documentation at `/docs`.

## Evaluation Logic

### 1. Resume Screening

The AI engine compares the candidate's resume information with the job
description and returns a structured result that includes a score,
matched skills, and potential gaps.

-   **Output score:** 0--100
-   **Purpose:** Summarize how closely the candidate profile matches the
    role
-   **Caution:** Resume text can be incomplete or misleading; verify
    important claims during assessment and interviews

### 2. Technical Answer Grading

Answers are evaluated against reference answers and a structured rubric.

-   **Output score:** 0--5 per answer
-   **Evaluation approach:** Rubric-based grading with structured JSON
    output
-   **Information hiding:** Reference answers and grading rubrics should
    not be returned to candidate-facing endpoints

### 3. Weighted Composite Score

The pipeline combines resume and technical scores using configured
weights:

``` python
composite_score = (
    weights["resume"] * resume_score
    + weights["qa"] * qa_score
)
```

The exact normalization and weight values should be verified in
`pipeline.py`. Ensure both score components use compatible scales before
combining them.

### 4. Discrepancy Detection

A large gap between resume claims and demonstrated technical performance
can trigger a review flag. This is intended to highlight cases for human
investigation, not to automatically establish dishonesty.

### 5. Anti-Cheat Signals

Tab-switch and copy/paste counts can be used to identify assessment
sessions that deserve additional review. Browser-side telemetry can be
incomplete or manipulated, and legitimate behavior can also trigger
these signals. Do not treat telemetry alone as conclusive evidence.

### 6. Decision Bands

The pipeline categorizes candidates into three decision bands:

-   **`PASS`** --- Meets the configured criteria for progressing.
-   **`HOLD`** --- Needs additional review or clarification.
-   **`REJECT`** --- Does not meet the configured criteria for
    progressing.

The thresholds and exact rules are implementation-specific. Check
`pipeline.py` before interpreting a result or changing production
policy.

## Security and Data Handling

SmartHire includes role checks, JWT authentication, candidate-facing
data masking, and audit logging. Before production use, review the
following:

-   Replace demo credentials and implement secure password hashing.
-   Store JWT signing secrets and API keys in a secret manager or
    environment variables.
-   Set token expiration and validate issuer/audience where appropriate.
-   Use persistent storage rather than in-memory SQLite if data must
    survive restarts.
-   Add rate limiting, request-size limits, secure CORS settings, and
    HTTPS at deployment.
-   Confirm that candidates cannot access other candidates' records or
    internal evaluation details.
-   Restrict and audit access to resumes, assessment answers, and
    interview notes.
-   Define retention and deletion policies for candidate personal data.
-   Validate and sanitize incoming data; do not rely on client telemetry
    as a trusted security boundary.
-   Require human review of consequential hiring decisions and provide a
    way to correct inaccurate candidate information.
-   Avoid sending unnecessary personal information to external AI
    services, and review the provider's data-handling terms.

## Configuration Notes

-   **Gemini model:** The project description references Gemini 2.5
    Flash. Confirm the model identifier configured in `ai_engine.py` and
    update it according to the model access available to your API key.
-   **JSON responses:** Structured JSON output helps downstream
    validation but does not eliminate the need to validate model
    responses with Pydantic or equivalent checks.
-   **Retries and fallbacks:** Review retry limits, timeout behavior,
    and fallback results in `ai_engine.py`.
-   **Database lifetime:** `sqlite:///:memory:` is suitable for local
    demos and tests, but it is not persistent storage.
-   **Concurrency:** `StaticPool` shares a connection for in-memory
    SQLite use. Verify session handling and concurrency behavior for
    your deployment setup.

## Troubleshooting

### `GEMINI_API_KEY` is missing

-   Confirm `.env` is located in `Backend/`.
-   Confirm the key name is exactly `GEMINI_API_KEY`.
-   Ensure the application loads environment variables before
    initializing the AI client.
-   Restart Uvicorn after changing environment variables.

### `SECRET_KEY` is missing

-   Confirm `.env` is located in `Backend/`.
-   Confirm the key name is exactly `SECRET_KEY`.
-   Ensure the application loads environment variables before
    initializing the AI client.
-   Restart Uvicorn after changing environment variables.

### The API starts, but benchmark users are missing

-   Check the startup and seeding logic in `main.py` and `seeder.py`.
-   Confirm `Input_Data.json` exists at the path expected by the seeder.
-   Review the terminal output for JSON parsing or database
    initialization errors.

### Authentication returns `401` or `403`

-   Log in again and use the returned token in the
    `Authorization: Bearer <token>` header.
-   Check whether the route requires a particular role.
-   Verify JWT configuration and token expiration.

### AI output cannot be parsed

-   Confirm the configured Gemini model supports the response format
    used by the SDK.
-   Check the raw error logs without exposing API keys or candidate
    personal data.
-   Validate returned fields and types; use bounded retries and safe
    fallback behavior.

### Candidate data disappears after restart

This is expected with an in-memory SQLite database. Use a persistent
database for any environment that requires data retention.

## Future Improvements

Potential next steps for the project include:

-   Add a persistent PostgreSQL database and database migrations.
-   Add automated unit and integration tests for role permissions,
    scoring, and data masking.
-   Add a frontend setup guide and screenshots for each portal.
-   Add structured logging, monitoring, and request correlation IDs.
-   Add configurable scoring weights and decision thresholds with
    versioned audit records.
-   Add a human-review workflow for discrepancy and anti-cheat flags.
-   Add CI checks for formatting, linting, tests, and dependency
    vulnerabilities.
-   Add deployment instructions and a production configuration
    checklist.

## 👨‍💻 Author
Deendayal Nishad
Electronics & Telecommunication Engineering Student | Aspiring Backend & AI Systems Engineer

GitHub: @deendayal038
## ⭐ Support & Feedback
If this architecture helped you understand distributed microservices pairing Spring Boot, Redis, Scikit-Learn, ChromaDB, and Agentic AI, please consider giving the repository a Star!

## 📄 License

This project is provided for educational, portfolio, and hackathon purposes. Add a `LICENSE` file if you plan to distribute the project publicly.

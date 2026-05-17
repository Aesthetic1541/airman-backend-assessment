# Skynet Flight Operations API

Backend technical assessment for AIRMAN Aeronautics Pvt. Ltd.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT Authentication
- RBAC
- Pytest

## Features

- Aircraft readiness management
- Sortie workflow management
- Training progress approval
- Role-based access control
- Audit logging
- Defect tracking
- Base-scoped access

## Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Known Issue

Dependency compatibility issues occurred due to Python 3.13/3.14 environment conflicts on Windows during final setup. The project structure, routes, services, schemas, business rules, and database models were completed, but final runtime verification remained incomplete at submission time.

## AI Usage

AI tools were used for:
- architecture guidance
- debugging assistance
- FastAPI scaffolding
- dependency troubleshooting

All generated code was manually reviewed and organized.

## Submission Notes

The backend architecture, RBAC rules, service layer, schemas, audit logging, and business workflows were implemented according to the AIRMAN assessment requirements.

Due to dependency compatibility conflicts with Python 3.13/3.14 on Windows during final environment setup, complete runtime verification could not be finalized before submission.

The project structure and business logic implementation remain intact and reviewable.
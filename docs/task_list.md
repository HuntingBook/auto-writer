# Auto Writer Implementation Tasks

- [x] **Project Initialization**
    - [x] Analyze existing requirements and architecture
    - [x] Verify project skeleton (Backend: FastAPI, Frontend: React+Vite, DB: Postgres)
    - [x] Docker environment setup (docker-compose.yml)

- [ ] **Backend - Core & Database**
    - [x] Define Database Models (Novel, Job, Artifact, etc.) <!-- id: 0 -->
    - [x] Configure Alembic and run initial migration <!-- id: 1 -->
    - [x] Implement DeepSeek Client (Retry, Rate limit) <!-- id: 2 -->
    - [x] Setup Celery Worker & Redis connection <!-- id: 3 -->

- [x] **Backend - Multi-Agent System**
    - [x] Implement "Chapter Fine Outline" (章节细纲) step. `backend/app/workers/novel_tasks.py` <!-- id: 4 -->
    - [x] Update UI to display Fine Outline. `frontend/src/components/novel/WorkflowSteps.tsx` <!-- id: 5 -->
    - [x] Implement Job/Step Logic & Persistence <!-- id: 6 -->

- [x] **Frontend - Workbench & Tasks**
    - [x] Design System Setup (Shadcn/UI, Tailwind) <!-- id: 7 -->
    - [x] Workbench Page (Task List, Create Modal) <!-- id: 8 -->
    - [x] Task Detail Page (Config, Real-time Logs) <!-- id: 9 -->
    - [x] Artifact Preview & Versioning <!-- id: 10 -->

- [x] **Integration & Verification**
    - [x] End-to-End Test (Create Task -> Generate -> Preview) <!-- id: 11 -->
    - [x] Docker One-Click Start Verification <!-- id: 12 -->
    - [x] Documentation & README Finalization <!-- id: 13 -->

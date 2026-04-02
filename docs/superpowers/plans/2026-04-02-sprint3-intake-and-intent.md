# Sprint 3: Task Intake & Intent Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan.

**Goal:** Enable planners to submit audio tasks (with file upload), auto-generate structured AudioIntentSpec with confidence scoring, show task status in real-time via SSE.

**Architecture:** Extends existing modular monolith. Adds intent/ module (spec generation + confidence), file upload via tus-compatible chunked upload, SSE endpoint for real-time status, task detail page with timeline, and task create page with form + upload.

**Tech Stack:** FastAPI, SQLAlchemy, Celery, tus (tusd or custom chunked upload), SSE (sse-starlette), Next.js 16, Ant Design 6, tus-js-client

---

## Task 1: Intent Generation Module (Backend)

Create the intent generation service that converts a submitted Task into an AudioIntentSpec using rule engine + mapping dictionary.

**Files:**
- Create: `server/app/modules/intent/service.py`
- Create: `server/app/modules/intent/router.py`
- Modify: `server/app/main.py` — register intent router

## Task 2: File Upload Endpoint (Backend)

Add chunked file upload endpoint for video/animation assets, storing to MinIO.

**Files:**
- Create: `server/app/modules/task/upload.py`
- Modify: `server/app/modules/task/router.py` — add upload endpoint

## Task 3: SSE Real-time Push (Backend)

Add Server-Sent Events endpoint for task status changes.

**Files:**
- Create: `server/app/modules/task/sse.py`
- Modify: `server/app/main.py` — register SSE route

## Task 4: Task Create Page (Frontend)

Full task creation form with file upload, tags, and submission.

**Files:**
- Create: `web/src/app/tasks/create/page.tsx`
- Modify: `web/src/lib/types.ts` — add IntentSpec type
- Modify: `web/src/lib/hooks.ts` — add task mutation hooks

## Task 5: Task Detail Page (Frontend)

Task detail page with status timeline and spec display.

**Files:**
- Create: `web/src/app/tasks/[taskId]/page.tsx`
- Create: `web/src/components/TaskTimeline.tsx`

## Task 6: Tests + Integration Verification

Test intent generation, upload, SSE, and full flow.

**Files:**
- Create: `server/tests/test_intent.py`
- Create: `server/tests/test_upload.py`

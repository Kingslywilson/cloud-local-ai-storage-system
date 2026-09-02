# System Architecture — Gradious AI-Enhanced Cloud File Storage Platform

---

## High-Level System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND LAYER                                │
│  Vanilla HTML5 / Modern CSS Design System / JavaScript (ES6 Modules)   │
│                                                                        │
│  [Dashboard]  [All Files]  [Upload]  [Folders]  [Shares]  [Activity]   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTP/HTTPS (REST API + JWT Bearer)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           BACKEND LAYER                                │
│                     FastAPI Application Server                         │
│                                                                        │
│  ├── Routers: /auth, /files, /folders, /activity                       │
│  ├── Security: JWT Authorization, bcrypt password hashing              │
│  ├── File Manager: Sanitization, Storage, Downloads, Shares            │
│  └── AI Service: Gemini 3.6 Flash Multimodal Analysis                  │
└──────────────────┬────────────────────────────────┬────────────────────┘
                   │                                │
                   ▼ SQL (PyMySQL)                  ▼ HTTPS API Call
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│          DATABASE LAYER              │  │        EXTERNAL AI           │
│           MySQL Server               │  │    Google Gemini API         │
│  - users        - files              │  │    (gemini-3.6-flash)        │
│  - folders      - file_shares        │  └──────────────────────────────┘
│  - ai_analysis  - activity_logs      │
└──────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend Layer
- Multi-page responsive web layout with CSS Variables and Glassmorphism styling.
- Central API abstraction (`api.js`) handles JWT Bearer headers, error handling, and session management.
- Dynamic toast notification system and interactive modal popups for File Sharing, File Rename, File Move, and Folder Creation.

### 2. Backend Layer (FastAPI)
- Modular router architecture (`auth.py`, `files.py`, `folders.py`).
- Security middleware enforcing user isolation on all endpoints.
- Path traversal prevention for file uploads and file renames.
- Secure, unpredictable UUID share tokens (`uuid4().hex`) for public and user-restricted file sharing.
- Resilient Gemini AI Integration (`ai_analysis.py`): text extraction from PDF, DOCX, TXT, CSV, JSON, MD, Code, and direct multimodal processing for images, audio, and video files.

### 3. Database Schema (MySQL)
- `users`: User registration data and bcrypt hashed passwords.
- `folders`: Hierarchical user folder organization.
- `files`: File metadata, original and unique disk filenames, byte size, MIME types.
- `file_shares`: Secure share tokens, public/user-specific access, recipient email verification.
- `ai_analysis`: Extracted summaries, descriptions, smart tags, and content insights.
- `activity_logs`: Full audit history for actions (UPLOAD, DOWNLOAD, VIEW, DELETE, RENAME, MOVE, SHARE, LOGIN, LOGOUT, FOLDER operations).

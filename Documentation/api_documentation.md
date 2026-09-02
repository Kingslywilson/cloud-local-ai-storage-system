# API Specification — Gradious Cloud Storage Platform

All API endpoints are hosted under `http://127.0.0.1:8000`.
Protected endpoints require a `Authorization: Bearer <JWT_TOKEN>` header.

---

## 1. Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/auth/register` | Register new user account | No |
| `POST` | `/auth/login` | Authenticate user & get JWT token | No |
| `POST` | `/auth/logout` | Invalidate current session & log activity | Yes |
| `GET` | `/auth/me` | Fetch logged in user profile | Yes |

---

## 2. File Management Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/files/` | List all files for current user (optional `?q=search`) | Yes |
| `POST` | `/files/upload` | Upload file & trigger Generative AI analysis | Yes |
| `GET` | `/files/{id}/download` | Download file (owner or authorized recipient) | Yes |
| `GET` | `/files/{id}/ai-analysis` | Fetch AI summary, description, tags, insights | Yes |
| `PUT` | `/files/{id}/rename` | Rename file (validated & sanitized) | Yes |
| `PUT` | `/files/{id}/move` | Move file into specified folder | Yes |
| `DELETE` | `/files/{id}` | Delete file, AI data, and share links | Yes |
| `GET` | `/files/storage` | Fetch total capacity & category byte breakdown | Yes |

---

## 3. Folder Management Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/folders/` | List user folders | Yes |
| `POST` | `/folders/` | Create new folder | Yes |
| `PUT` | `/folders/{id}/rename` | Rename folder | Yes |
| `DELETE` | `/folders/{id}` | Delete folder (unassigns files to root) | Yes |
| `GET` | `/files/folder/{id}` | View files inside folder | Yes |

---

## 4. File Sharing Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/files/{id}/share` | Generate secure random share token | Yes |
| `GET` | `/files/share/{token}` | Access & download shared file by token | Conditional |
| `DELETE` | `/files/share/{token}` | Revoke active share token | Yes |
| `GET` | `/files/my-shares` | List all shares created by current user | Yes |
| `GET` | `/files/shared-with-me` | List all files shared specifically with user | Yes |

---

## 5. Activity & Audit Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/activity` | List user's action history ordered by newest first | Yes |

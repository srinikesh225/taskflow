# TaskFlow

A small, complete full-stack task manager: a **FastAPI** backend with JWT auth,
SQLAlchemy models, and a tested REST API, plus a **React (Vite)** frontend. Each
user signs up, logs in, and manages their own private tasks.

```
React (Vite, :5173)  ──/api proxy──▶  FastAPI (:8000)  ──▶  SQLite
        UI                               auth · tasks          taskflow.db
```

## Features

- **Authentication** — register / login with JWT (OAuth2 password flow), bcrypt
  password hashing.
- **Tasks** — create, list, filter by status, update (partial), delete. Every
  task is scoped to its owner.
- **Security** — per-owner access control, login rate limiting, constant-time
  login (no user enumeration), security headers, restricted CORS.
- **Observability** — structured request logging with a per-request id.
- **Tests** — 26 backend tests (pytest) covering auth, CRUD, isolation, security.

## Project layout

```
taskflow/
├── TODO.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py            # app factory, middleware, routers, lifespan
│   │   ├── config.py          # env-driven settings
│   │   ├── database.py        # engine, session, Base, get_db
│   │   ├── models.py          # User, Task (SQLAlchemy 2.0)
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── security.py        # bcrypt hashing + JWT
│   │   ├── deps.py            # get_current_user
│   │   ├── ratelimit.py       # in-memory login rate limiter
│   │   ├── logging_config.py  # logging + request-id & security-headers middleware
│   │   └── routers/
│   │       ├── auth.py        # /api/auth/register|login|me
│   │       └── tasks.py       # /api/tasks CRUD
│   └── tests/                 # pytest suite
└── frontend/
    ├── package.json
    ├── vite.config.js         # dev proxy /api -> :8000
    └── src/
        ├── api.js             # fetch wrapper + token storage
        ├── App.jsx
        └── components/        # Login, TaskBoard, TaskForm, TaskItem
```

## Getting started

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # then edit SECRET_KEY

uvicorn app.main:app --reload
```

- API root: <http://localhost:8000>
- Interactive docs (Swagger): <http://localhost:8000/docs>
- Health check: <http://localhost:8000/api/health>

The SQLite database (`taskflow.db`) and tables are created automatically on
startup.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The dev server proxies `/api` to the backend, so
run both at once.

## API reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | – | Liveness check |
| POST | `/api/auth/register` | – | Create an account |
| POST | `/api/auth/login` | – | Get a JWT (form: `username`, `password`) |
| GET | `/api/auth/me` | ✓ | Current user |
| GET | `/api/tasks` | ✓ | List own tasks (`?status=`, `?limit=`, `?offset=`) |
| POST | `/api/tasks` | ✓ | Create a task |
| GET | `/api/tasks/{id}` | ✓ | Get one own task |
| PATCH | `/api/tasks/{id}` | ✓ | Partial update |
| DELETE | `/api/tasks/{id}` | ✓ | Delete |

Task `status`: `todo` · `in_progress` · `done`. Task `priority`: `low` ·
`medium` · `high`.

### Example

```bash
# register
curl -X POST localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}'

# login -> token
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login \
  -d 'username=me@example.com&password=password123' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# create a task
curl -X POST localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Ship the README","priority":"high"}'
```

## Running the tests

```bash
cd backend
.venv\Scripts\python -m pytest        # 26 tests
```

The suite uses an isolated in-memory SQLite database per test (via a `get_db`
dependency override), so it never touches your dev database.

## Security notes

Implemented in this project:

- **Password hashing** with bcrypt (72-byte bound enforced); hashes never leave
  the server.
- **JWT** signed HS256; decode pins the algorithm (blocks `alg=none` confusion);
  60-minute expiry.
- **Access control**: task routes are owner-scoped and return `404` (not `403`)
  for other users' ids, avoiding existence leaks.
- **Login rate limiting**: 10 failed attempts / minute / IP → `429`.
- **No user enumeration**: identical error + constant-time verify whether or not
  the email exists.
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy` (+ HSTS in production).
- **CORS** restricted to configured origins.
- **Startup guard**: refuses to boot in production with the default `SECRET_KEY`.

Before deploying to production:

- Set a strong `SECRET_KEY` and `ENVIRONMENT=production`.
- Serve over HTTPS (enables HSTS) behind a reverse proxy.
- The rate limiter is in-memory (single process); back it with Redis if you run
  multiple workers.
- The frontend stores the JWT in `localStorage` for simplicity; for stricter XSS
  posture, move to httpOnly cookies with CSRF protection.
- Swap `create_all` for Alembic migrations.

## Tech stack

FastAPI · SQLAlchemy 2.0 · Pydantic v2 · PyJWT · bcrypt · pytest ·
React 18 · Vite 5.

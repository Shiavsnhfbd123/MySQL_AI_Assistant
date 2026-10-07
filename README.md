# QueryPilot — MySQL AI Assistant

A full-stack, schema-aware MySQL assistant that turns informal English into a structured SQL plan. The AI only proposes a plan; the FastAPI backend independently parses, validates, risk-classifies, confirms, and executes it through a restricted MySQL account.

For the exact Windows startup order and troubleshooting commands, begin with
`START_PROJECT_GUIDE.md`.

## Architecture

```text
React + TypeScript
        │ natural-language instruction / immutable plan_id
        ▼
FastAPI ──► current schema ──► Ollama / Qwen2.5 3B
   │                              │
   └── SQLGlot validation ◄── structured JSON plan
        │
        ├── risk + read-only policy + confirmation
        └── restricted MySQL application user
```

Ollama runs locally and needs no API key. MySQL credentials and the optional OpenRouter fallback key are read only by the backend from `backend/.env`, which is ignored by Git.

## Prerequisites

- Python 3.11+
- Node.js 20+
- MySQL 8+
- Ollama for Windows
- NVIDIA driver 551.61+ for NVIDIA acceleration

## 1. Create the restricted MySQL account

Use the interactive repair utility after configuring `backend/.env`. It hides the administrator password, reads the application password from `backend/.env`, and never stores or prints the administrator password:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python setup_database.py
```

Use this utility when the UI reports `authentication_failed` or MySQL error 1045.

The application account is scoped to `mysql_ai_lab` and does not receive server-administration or user-management privileges.

## 2. Install Ollama and Qwen2.5 3B

Install Ollama for Windows from `https://ollama.com/download/windows`, then open a new PowerShell window:

```powershell
ollama --version
ollama pull qwen2.5:3b
```

If Ollama is installed as the portable build, start its local server from the project root instead:

```powershell
.\scripts\start_ollama.ps1
```

The script checks `OLLAMA_EXE`, the normal Windows installation directory, and the portable development installation in that order. It binds Ollama to loopback only and enables Flash Attention. Leave that terminal open, then run `ollama pull qwen2.5:3b` (or the matching portable executable) once.

Ollama runs its local API at `http://127.0.0.1:11434`. On supported NVIDIA hardware it selects CUDA automatically. This project requests all model layers on the GPU with `OLLAMA_NUM_GPU=-1`, uses a 4096-token context to fit comfortably on 4 GB VRAM, and keeps the loaded model warm for ten minutes.

Verify actual GPU use after making one query:

```powershell
.\scripts\verify_ollama_gpu.ps1
```

In `ollama ps`, `100% GPU` means full GPU loading. A CPU/GPU percentage means partial offload. `nvidia-smi` should also show Ollama and increased VRAM usage.

## 3. Configure and run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` locally:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_GPU=-1
OLLAMA_KEEP_ALIVE=10m
MYSQL_PASSWORD=the_password_used_in_mysql_setup
```

No AI API key is required. To use the existing OpenRouter fallback instead, set `AI_PROVIDER=openrouter` and provide `OPENROUTER_API_KEY` only in this backend file.

Then start the API:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On Windows, you can also start it from the project root with
`.\scripts\start_backend.ps1`. Both forms avoid the generated `uvicorn.exe`
launcher, which may be blocked by Windows Application Control.

API docs are available at `http://127.0.0.1:8000/docs`.

## 4. Configure and run the frontend

In a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://127.0.0.1:5173`. `VITE_API_BASE_URL` is public configuration; never put private keys in a `VITE_*` variable.

## Hosting and deployment

The production image is platform-neutral and can be deployed anywhere that accepts a Dockerfile, including Render, Railway, Fly.io, Cloud Run, Azure Container Apps, AWS App Runner, DigitalOcean, and similar services.

Choose the deployment mode that matches the platform:

| Platform capability | AI configuration | Database configuration |
|---|---|---|
| General PaaS without GPU | `AI_PROVIDER=openrouter` | Managed MySQL using `MYSQL_URL` |
| PaaS plus private GPU service | `AI_PROVIDER=ollama` and private `OLLAMA_BASE_URL` | Managed MySQL using `MYSQL_URL` |
| Docker host with NVIDIA GPU | `compose.yaml` plus `compose.gpu.yaml` | Included MySQL container or managed MySQL |

The application image does not try to run Ollama inside the web-service container. This keeps it deployable on CPU-only platforms and lets Ollama run as a persistent GPU service where models are not lost during web-service restarts.

For Ollama, the backend must be able to reach a persistent Ollama server. `localhost` works only when Ollama and FastAPI run on the same machine. The Compose configuration uses `host.docker.internal` to reach Ollama running on the Windows host. On a remote platform, deploy Ollama separately on a GPU machine and set `OLLAMA_BASE_URL` to its private, authenticated network address, or switch the hosted deployment to OpenRouter.

The Docker image performs a multi-stage build:

1. Builds the React frontend with Node.
2. Installs only the Python runtime and backend requirements.
3. Copies the compiled frontend into the final image.
4. Serves the frontend and API from one public origin through FastAPI.

The container listens on the hosting provider's `PORT` variable and exposes `/api/health/live` as a lightweight liveness endpoint. Run one application instance unless the in-memory pending-plan and history stores are replaced by Redis or another shared store.

### Test the production deployment locally

```powershell
Copy-Item compose.env.example .env
# Edit .env and replace every placeholder.
docker compose up --build
```

Open `http://localhost:8000`. The Compose database is kept in the named `mysql-data` volume.

On a Linux Docker host with the NVIDIA Container Toolkit, run the complete Qwen GPU stack with:

```bash
docker compose -f compose.yaml -f compose.gpu.yaml up --build
```

The GPU override starts Ollama privately, persists its model files, pulls `qwen2.5:3b`, and waits for the model before starting the application. Ollama is not published on a host port.

### Deploy the Dockerfile with a managed MySQL database

Create a web service from the repository's root `Dockerfile`, then configure:

```env
APP_ENV=production
SERVE_FRONTEND=true
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://your-private-ollama-host:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_GPU=-1
MYSQL_HOST=your-managed-mysql-host
MYSQL_PORT=3306
MYSQL_DATABASE=mysql_ai_lab
MYSQL_USER=mysql_ai_assistant
MYSQL_PASSWORD=your_app_user_password
MYSQL_SSL_DISABLED=false
MYSQL_SSL_VERIFY_CERT=false
CORS_ORIGINS=https://your-public-domain.example
```

Alternatively, replace the individual `MYSQL_*` connection values with the URL supplied by the managed provider:

```env
MYSQL_URL=mysql://user:percent_encoded_password@host:3306/database
```

Passwords containing `@`, `:`, `/`, `#`, or `%` must be URL-encoded. Keep `MYSQL_URL`, `OLLAMA_API_KEY`, and `OPENROUTER_API_KEY` in the platform's encrypted secret manager, never in the repository.

If the private Ollama gateway requires bearer authentication, set `OLLAMA_API_KEY`. The backend sends it only in the server-to-server `Authorization` header; it is never returned to the frontend.

Do not set a fixed `PORT` when the platform supplies one automatically. Use `/api/health/live` for the platform health-check path. Add `MYSQL_SSL_CA` and enable certificate verification when your database provider supplies a CA certificate path.

### Separate frontend and backend hosting

The default production image is recommended because it avoids cross-origin and runtime API URL problems. If deploying the frontend separately, set this frontend build-time variable:

```env
VITE_API_BASE_URL=https://api.your-domain.example
```

Then set the backend runtime variable to the exact frontend origins, separated by commas:

```env
CORS_ORIGINS=https://your-domain.example,https://www.your-domain.example
```

Never use wildcard production CORS with credentials, and never place `OPENROUTER_API_KEY` or database credentials in a `VITE_*` variable.

## Tests and production builds

```powershell
cd backend
pytest -q

cd ..\frontend
npm run build
```

The automated backend suite mocks external AI calls and database connections, so it does not spend API credits or modify a database.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Database and AI configuration status |
| `GET` | `/api/schema` | Tables, columns, keys, and data types |
| `GET` | `/api/tables` | Table names |
| `GET` | `/api/tables/{table}` | One table's metadata |
| `GET` | `/api/history` | In-process execution audit history |
| `POST` | `/api/query/plan` | Generate and validate a SQL plan |
| `POST` | `/api/query/execute` | Execute an immutable pending plan |
| `POST` | `/api/query/cancel` | Cancel a pending plan |

Pending plans and query history are intentionally in-memory for this local application. They reset when FastAPI restarts and should be moved to a durable store before multi-instance deployment.

## Security controls

- One parsed MySQL statement per plan
- Placeholder count validation and bound parameters
- Blocked user, privilege, server, file, plugin, and database-management commands
- Blocked cross-database and MySQL system-schema access
- Backend-owned operation and risk classification
- Confirmation for high and critical risk operations
- Backend-enforced read-only mode
- Immutable, expiring, single-use `plan_id`
- Result payload limit and explicit transaction commit/rollback
- Restricted CORS origins for local development

If an API key was ever committed, pasted, logged, or hardcoded in source code, revoke it at the provider and create a new one before using this project.
#

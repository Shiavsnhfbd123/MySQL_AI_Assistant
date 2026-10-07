# QueryPilot — Complete Project Start Guide

Use this guide to start MySQL, Ollama with `qwen2.5:3b`, the FastAPI backend,
and the React frontend on Windows. Keep each service in its own PowerShell
window while using the application.

Project directory:

```text
D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant
```

## One-time setup

### 1. Check MySQL

```powershell
Get-Service MySQL80
```

The status should be `Running`. If it is stopped:

```powershell
Start-Service MySQL80
```

Configure or repair the restricted application account:

```powershell
cd "D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant\backend"
.\.venv\Scripts\Activate.ps1
python setup_database.py
```

At `MySQL administrator [root]:`, press Enter to use `root`. Type the MySQL
administrator password at the hidden prompt and press Enter. Do not put that
administrator password in the project.

Wait for:

```text
Success: database and restricted application account are ready.
```

### 2. Install backend dependencies if needed

```powershell
cd "D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Do not recreate `.venv` when it already exists and works.

### 3. Install frontend dependencies if needed

```powershell
cd "D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant\frontend"
npm install
```

### 4. Download Qwen2.5 3B if needed

Start Ollama using the first daily-start step below. In another PowerShell
window run:

```powershell
cd "D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant"
.\scripts\pull_ollama_model.ps1
```

The model is already downloaded on the current laptop, so this is normally
needed only after reinstalling Ollama or deleting its model directory.

## Daily startup — use this order

### Terminal 1: Start Ollama

```powershell
cd "D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant"
.\scripts\start_ollama.ps1
```

Leave the terminal open. Wait until Ollama reports that it is listening on
`127.0.0.1:11434`.

### Terminal 2: Start the backend

```powershell
cd "D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant"
.\scripts\start_backend.ps1
```

Leave the terminal open. Wait for:

```text
Uvicorn running on http://127.0.0.1:8000
```

The script uses `python -m uvicorn`, avoiding the `uvicorn.exe` launcher that
Windows Application Control blocks on this laptop.

### Terminal 3: Start the frontend

```powershell
cd "D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant"
.\scripts\start_frontend.ps1
```

Leave the terminal open, then open:

```text
http://127.0.0.1:5173
```

## Verify everything

Check Ollama:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/version
```

Check the backend, database, model and GPU status:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected important values:

```text
status        : ok
database      : connected
ai_provider   : ollama
ai_model      : qwen2.5:3b
ai_connected  : True
```

Run the full GPU check:

```powershell
cd "D:\Shivansh\Shivansh Coding\MySQL_AI_Assistant"
.\scripts\verify_ollama_gpu.ps1
```

After the model has answered a request, `ollama ps` should show `100% GPU`.
The health response can show a blank accelerator before the model has been
loaded; that is normal.

## Test the application

Enter this in QueryPilot:

```text
Show students older than 20
```

Review the generated SQL and parameter list. Execute it only after checking
that the proposed operation is correct.

The first request can be slower because Ollama must load the model into GPU
memory. Warm requests on this laptop normally take about 3–6 seconds. The
model unloads after ten minutes of inactivity unless `OLLAMA_KEEP_ALIVE` is
increased.

## Stop the project

Press `Ctrl+C` once in each service terminal. Recommended order:

1. Frontend
2. Backend
3. Ollama

MySQL can remain running as a normal Windows service.

## Common problems

### `uvicorn.exe` blocked by Application Control

Use the project script or the Python module command:

```powershell
.\scripts\start_backend.ps1
```

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Database offline or error 1045

Run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python setup_database.py
```

### Ollama unavailable

Confirm Terminal 1 is still open, then check:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/version
```

### Model missing

Start Ollama and run:

```powershell
.\scripts\pull_ollama_model.ps1
```

### Port already in use

Another copy of the service is probably running. Return to its terminal and
press `Ctrl+C` before starting it again.

## Hosting on another platform

The production `Dockerfile` serves the frontend and backend together and uses
the hosting provider's dynamic `PORT`. Use a managed MySQL connection through
`MYSQL_URL`.

- CPU-only hosting: use `AI_PROVIDER=openrouter`.
- Hosting with a private GPU service: use `AI_PROVIDER=ollama` and set the
  private `OLLAMA_BASE_URL`.
- NVIDIA Docker host: run `compose.yaml` together with `compose.gpu.yaml`.

Never upload `backend/.env` or put database passwords, Ollama tokens, or API
keys in frontend `VITE_*` variables. See the main `README.md` for full hosting
environment variables and Docker commands.

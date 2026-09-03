# PostgreSQL Setup — Step by Step (Windows)

This project uses PostgreSQL through Django settings in `backend/config/settings/base.py`. Connection details come from your root `.env` file (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).

---

## Option A — Easiest: PostgreSQL via Docker (recommended)

You do **not** need to install PostgreSQL on Windows. Docker Compose starts it for you.

### Step 1: Install Docker Desktop

1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
2. Install and start Docker Desktop (whale icon in the system tray should be running).

### Step 2: Configure environment

1. Open the project folder: `c:\SNMADMDCP`
2. Copy the example env file (if you have not already):

```powershell
cd c:\SNMADMDCP
copy .env.example .env
```

3. Edit `.env` and set **database for Docker**:

```env
DB_NAME=snmadmdcp
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
```

Important: inside Docker Compose, the hostname is `db` (the service name), **not** `localhost`.

### Step 3: Start the stack

```powershell
cd c:\SNMADMDCP
docker compose up --build
```

Wait until you see the backend running. On first start it will:

- Create the PostgreSQL database `snmadmdcp`
- Run `migrate`
- Run `seed_demo` (demo users and sample data)

### Step 4: Open the app

| What        | URL |
|-------------|-----|
| Frontend    | http://localhost:5173 |
| API         | http://localhost:8000/api/v1/ |
| Swagger     | http://localhost:8000/api/schema/swagger/ |

Login: `admin` / `admin123`

### Step 5: Verify PostgreSQL (optional)

```powershell
docker compose exec db psql -U postgres -d snmadmdcp -c "\dt"
```

You should see Django tables (`accounts_user`, `devices_device`, etc.).

---

## Option B — Local PostgreSQL on Windows (no Docker for DB)

Use this if you installed PostgreSQL directly (e.g. from [postgresql.org](https://www.postgresql.org/download/windows/) or via pgAdmin installer).

### Step 1: Install PostgreSQL

1. Download the Windows installer from https://www.postgresql.org/download/windows/
2. During setup, note:
   - **Port**: usually `5432`
   - **Superuser password**: e.g. `postgres` (choose your own; remember it)
3. Optionally install **pgAdmin 4** (GUI) with the installer.

### Step 2: Create the database

**Using pgAdmin:**

1. Open pgAdmin → connect to `PostgreSQL 16` (or your version).
2. Right-click **Databases** → **Create** → **Database**
3. Name: `snmadmdcp`
4. Owner: `postgres` → Save

**Using SQL Shell (psql):**

```sql
CREATE DATABASE snmadmdcp;
```

Or in PowerShell (if `psql` is on PATH):

```powershell
psql -U postgres -c "CREATE DATABASE snmadmdcp;"
```

### Step 3: Configure `.env` for local Postgres

Edit `c:\SNMADMDCP\.env`:

```env
DB_NAME=snmadmdcp
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

Replace `YOUR_POSTGRES_PASSWORD` with the password you set during PostgreSQL installation.

### Step 4: Install Redis (required for WebSockets and Celery)

- **Docker only Redis:** `docker run -d -p 6379:6379 redis:7-alpine`
- Or install [Memurai](https://www.memurai.com/) / Redis for Windows.

### Step 5: Python backend setup

```powershell
cd c:\SNMADMDCP\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 6: Connect Django to PostgreSQL (migrate)

```powershell
cd c:\SNMADMDCP\backend
$env:DJANGO_SETTINGS_MODULE="config.settings.dev"
python manage.py migrate
python manage.py seed_demo
```

If connection works, you will see migrations applying with no errors.

**Test connection only:**

```powershell
python manage.py dbshell
```

You should get a `snmadmdcp=#` prompt. Type `\q` to quit.

### Step 7: Run backend services (3 terminals)

**Terminal 1 — API + WebSocket:**

```powershell
cd c:\SNMADMDCP\backend
.\venv\Scripts\Activate.ps1
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Terminal 2 — Celery worker:**

```powershell
cd c:\SNMADMDCP\backend
.\venv\Scripts\Activate.ps1
celery -A config worker -l info
```

**Terminal 3 — Celery beat (scheduled tasks):**

```powershell
cd c:\SNMADMDCP\backend
.\venv\Scripts\Activate.ps1
celery -A config beat -l info
```

### Step 8: Run frontend

```powershell
cd c:\SNMADMDCP\frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `password authentication failed for user "postgres"` | Wrong `DB_PASSWORD` in `.env`; reset in pgAdmin or reinstall. |
| `could not connect to server: Connection refused` | PostgreSQL service not running. Start **postgresql-x64-16** in Windows Services, or use Docker. |
| `database "snmadmdcp" does not exist` | Run `CREATE DATABASE snmadmdcp;` (Step 2 Option B). |
| Django uses `DB_HOST=db` on Windows locally | Change to `DB_HOST=localhost` when not using Docker Compose. |
| Port 5432 already in use | Another Postgres instance or Docker is using it; stop one or change `DB_PORT`. |

---

## How Django reads these settings

In `backend/config/settings/base.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "snmadmdcp"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
```

Django loads variables from the `.env` file in the project root via `python-dotenv`.

---

## Quick reference: `.env` by scenario

| Scenario | `DB_HOST` | `REDIS_URL` |
|----------|-----------|-------------|
| Full Docker Compose | `db` | `redis://redis:6379/0` |
| Local Postgres + local Redis | `localhost` | `redis://localhost:6379/0` |
| Local Postgres + Docker Redis only | `localhost` | `redis://localhost:6379/0` |

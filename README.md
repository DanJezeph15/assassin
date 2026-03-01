# Airbnb Games

Party games website for playing with friends at Airbnb stays. See [CLAUDE.md](CLAUDE.md) for game rules and details.

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## First Time Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install
```

## Running the App

Start both servers in separate terminals:

### Backend (port 8000)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### Frontend (port 5173)

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

The frontend proxies `/api` requests to the backend automatically.

# Wedding Studio Frontend

React + TypeScript + Vite + Tailwind + shadcn/ui SPA.

## Run

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 — the dev server proxies `/api/*` to the FastAPI backend on port 8000, so start the API first:

```bash
cd ../backend && source .venv/bin/activate && uvicorn api.main:app --port 8000 --reload
```

## Stack

- React 18 + TypeScript (strict)
- Vite (build + dev server)
- Tailwind CSS v4 + shadcn/ui (New York style)
- lucide-react (icons)

More additions in subsequent Phase 4 prompts.

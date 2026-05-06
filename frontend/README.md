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

## Generating API types

TypeScript types are generated from the FastAPI OpenAPI schema:

```bash
# Backend must be running on port 8000
cd ../backend && source .venv/bin/activate
uvicorn api.main:app --port 8000 &

cd ../frontend
npm run gen-api
```

The generated file at `src/lib/api-types.ts` is committed to git.
Re-run `npm run gen-api` whenever backend schemas change.

Use generated types like:

```ts
import type { components } from '@/lib/api-types'

type Wedding = components['schemas']['WeddingPublic']
type Guest = components['schemas']['GuestPublic']
```

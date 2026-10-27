# BrandLens – AI Brand‑Governance Platform

## Overview
BrandLens is a lightweight **brand‑governance platform** built for the Inkloom AI Hackathon (Team Double Trouble). It provides:
- A **FastAPI** backend with endpoints for authentication, knowledge‑base, workflow, insights and disclosure.
- A **single‑page web UI** (`BrandLens.html`) written in vanilla HTML + JavaScript that lets users create draft content, run rule‑based brand reviews, and manage approvals.
- **Rule‑based checks** (no external AI) that flag claims, terminology, pricing, tone, accessibility and visual‑consistency issues.
- Role‑based UI (Creator, Reviewer, Manager, Admin) with audit logs and version history.

## Repository Layout
```
BrandLens/
├─ BrandLens.html            # Front‑end UI (no framework)
├─ backend/                 # FastAPI server
│   ├─ app/
│   │   ├─ main.py           # FastAPI entry point, router inclusion
│   │   ├─ api/              # knowledge_base, workflow, insights, disclosure
│   │   ├─ core/             # Config & security helpers
│   │   └─ db/               # SQLite DB (brandlens.db)
│   └─ requirements.txt      # Python dependencies
├─ frontend/                # Vite/React scaffold (optional, not required for demo)
│   ├─ package.json
│   └─ src/…               
├─ migrations/               # DB migration scripts (if any)
└─ .env.example            # Example env vars (LLM_PROVIDER, SUPABASE_URL…)
```

## How to Run Locally
1. **Create a virtual environment and install Python dependencies**
   ```powershell
   cd C:\Programming\Projects\BrandLens
   python -m venv venv
   .\venv\Scripts\Activate.ps1   # PowerShell (or `venv\Scripts\activate.bat` for cmd)
   python -m pip install -r backend\requirements.txt
   ```
2. **Start the FastAPI server**
   ```powershell
   python -m uvicorn backend.app.main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`.
3. **Open the UI**
   Open `C:\Programming\Projects\BrandLens\BrandLens.html` in a browser. The UI talks directly to the locally running server.
4. **(Optional) Run the React/Vite front‑end**
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   Then open the Vite dev URL (usually `http://localhost:5173`).

## Core Features Implemented
- **Authentication** using demo JWT tokens (`DEMO_USERS`).
- **Rule engine** that automatically analyses text for prohibited claims, outdated pricing, tone, accessibility, and visual palette compliance.
- **Interactive review** – users can accept suggested fixes, dismiss findings with a reason, and add comments.
- **Audit log & version history** for each document.
- **Governance insights dashboard** summarising flag counts per clause.
- **Editable knowledge base** (approved terminology, facts, colour palette).

## Technology Stack
- **Backend:** Python 3.13, FastAPI, Uvicorn, SQLite, Pydantic, JWT.
- **Frontend:** Plain HTML, CSS (custom properties for dark mode), vanilla JavaScript.
- **Optional UI scaffold:** Vite + React (present in `frontend/` but not required for the core demo).
- **Package management:** `pip` for Python, `npm` for the optional React UI.

## Deployment Options (for judges)
- **Backend:** Deploy to a free cloud provider such as **Render**, **Railway**, or **Fly.io** using the provided `Dockerfile` (you can generate one via `uvicorn` or the provider’s auto‑detect).
- **Frontend:** The static `BrandLens.html` can be hosted on **GitHub Pages**, **Netlify**, or **Vercel** (just point the service to the repository root or the `frontend/` build output if you prefer the React version).
- **Combined deployment:** Services like Render allow you to host both the FastAPI service and static files in a single project.

## Submission Checklist for Round 2
1. **Working project link** – Deploy the backend (e.g., Render) and host the static HTML (e.g., GitHub Pages) or provide a tunnel URL (e.g., `ngrok`) for judges to access.
2. **Source‑code repository link** – Push the entire `BrandLens` folder to a public GitHub repository.
3. **Updated project PDF** – Export this README (or a dedicated spec document) to PDF and upload it to the repository (e.g., `BrandLens.pdf`).
4. **List of completed features** – Include the **Core Features Implemented** section above in the PDF.
5. **Technology & implementation details** – Already covered in the **Technology Stack** and **How to Run** sections.
6. **Explanation of any changes** – The only change from Round 1 was the removal of the `google-genai` dependency and updating the requirements file.
7. **Three major improvements for Round 3** (see below).

## Planned Improvements for Round 3
1. **LLM‑powered suggestion engine** – Replace the rule‑based static checks with a configurable LLM that can generate contextual improvement suggestions while still respecting brand guidelines.
2. **Real user management & persistence** – Integrate Supabase (or another managed Postgres) for user accounts, document storage, and audit logs instead of the local SQLite demo.
3. **Analytics & dashboard** – Build a detailed analytics dashboard showing trends over time (e.g., most‑flagged clauses, average review time, user activity) and exportable reports for brand managers.


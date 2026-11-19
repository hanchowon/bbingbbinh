# Project Rules & Guidelines

## 1. Tech Stack & Environment
- **Frontend:** GAS, Tailwind CSS, TypeScript
- **Backend / API:** Python (FastAPI), Google Cloud Run
- **Database / Storage:** Supabase, Chroma DB
- **Environment:** Node.js, Python 3.10+

## 2. Core Files & Architecture
- **Google Apps Script / Frontend:**
  - `code.gs`: Apps Script backend logic and web app handlers.
  - `index.html`: Frontend UI interface served via Apps Script.
    - Handles frontend UI, Google Sheets integration, and user interaction.
  - Uses standard GAS APIs (`SpreadsheetApp`, `UrlFetchApp`, etc.).
- **Python / Backend / Deployment:**
  - `main.py`: FastAPI or Python backend entry point.
  - `requirements.txt`: Python dependencies list.
  - `Dockerfile`: Container configuration for Google Cloud Run deployment.
    - Handles heavy data processing, AI/API logic, algorithm, and core computation via FastAPI.
  - Deployed on Google Cloud Run.

## 3. Core Architecture & Coding Standards
- **Component Design:** Use functional components with TypeScript interfaces. Keep components modular and reusable.
- **Code Style:** Follow clean code practices. Write concise code and avoid unnecessary boilerplate.
- **Language:** Respond in Korean unless specified otherwise. Keep technical terms and code comments clear.
- Keep separation of concerns clear between Apps Script frontend/backend and Python microservices.
- Write clean, production-ready code with concise explanations.

## 4. Integration Guidelines
- **Communication:** GAS (`code.gs`) communicates with Python (`main.py`) via REST API calls using `UrlFetchApp`.
- **Boundaries:** Never mix GAS syntax into Python files or Python syntax into GAS files. Keep separation of concerns strict.

## 5. Response Guidelines
- **Direct & Concise:** Do not repeat the user's prompt or add lengthy conversational filler. Give the solution immediately.
- **Code Snippets:** When modifying existing files, output only the modified blocks or changed functions rather than rewriting the entire file, unless requested.
- **No Unused Imports:** Ensure all imports and variables are used.

## 6. Token Optimization
- When referencing files, refer to them by their exact names (`code.gs`, `main.py`, etc.).
- Output only modified code blocks rather than rewriting entire files unless requested.
- **Concise Outputs:** Return only the requested code blocks or modified functions. Avoid redundant explanations or repeating the prompt.
- **Targeted Reference:** Rely on the file definitions above when asked to update `code.gs` or `main.py`.

## 7. Error Handling & Logging
- **API Response:** Always return standardized JSON structures from Python (`main.py`).
- **Debugging:** Implement try-catch blocks in `code.gs` when calling Python APIs to handle network errors gracefully.

## 8. Security & Environment Variables
- Never hardcode sensitive keys or URLs. Use GAS PropertiesService or Python environment variables (`.env`).
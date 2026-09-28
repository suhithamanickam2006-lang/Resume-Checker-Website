# Automated Resume Reviewer for College Placement Cells

A Flask application for placement cells, coordinators, and students to review resumes, calculate ATS compatibility scores, detect grammatical errors, flag missing sections, and keep local history in SQLite.

## Technology Stack

- **Backend:** Python + Flask
- **Frontend:** HTML5 + CSS3 + Vanilla JavaScript
- **Storage:** SQLite (`placement_cell.db`, created automatically)
- **PDF Extraction:** PyMuPDF (`fitz`) / `pdfplumber`
- **Grammar Checking:** LanguageTool with an offline heuristic engine
- **ATS Engine:** Weighted scoring model for contact details, sections, skills, formatting, and grammar

## Project Structure

```
├── app.py              # Flask routes and application server
├── config.py           # Application configuration and SQLite path
├── database.py         # SQLite schema and CRUD operations
├── parser.py           # PDF text extraction and resume parsing
├── analyzer.py         # ATS scoring and grammar analysis
├── generate_sample_pdf.py
├── requirements.txt
├── style.css             # Shared stylesheet
├── script.js             # Browser interactions
└── *.html                # Flask templates
```

## Prerequisites

1. **Python 3.9+** installed on your system.
2. **Visual Studio Code (VS Code).**

## Exact VS Code Setup Instructions

1. **Open VS Code.**
2. Go to **File -> Open Folder...** and select the project folder.
3. Open a new Terminal in VS Code (**Terminal -> New Terminal** or press ``Ctrl + ` ``).
4. (Optional but recommended) Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
5. Install all required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
6. Generate sample student PDF resumes for testing:
   ```powershell
   python generate_sample_pdf.py
   ```
7. Start the Flask application:
   ```powershell
   python app.py
   ```
8. Open your web browser and navigate to:
   **`http://127.0.0.1:5000`**

The SQLite database and its tables are initialized automatically when the app starts. No separate database server or setup command is required.

## Configuration

Create a `.env` file when you need to override defaults:

```env
SECRET_KEY=use_a_long_random_value
TPO_USERNAME=tpo_admin
TPO_PASSWORD=use_a_long_random_value
ENABLE_LANGUAGE_TOOL=false
```

The upload folder and local database file are created or used by the application in the project directory.

## Deploy With Netlify

Netlify hosts the public site and proxies requests to the Flask backend. The Flask process must run on a Python host such as Render or Railway because Netlify does not run a persistent Python web server.

1. Create a Web Service on Render or Railway from this repository.
2. Use the existing `Procfile` command and set these environment variables:
   ```env
   SECRET_KEY=use_a_long_random_value
   TPO_USERNAME=tpo_admin
   TPO_PASSWORD=use_a_long_random_value
   ENABLE_LANGUAGE_TOOL=false
   ```
3. Confirm the backend works at its public URL, for example `https://your-app.onrender.com`.
4. In `netlify.toml`, replace `REPLACE_WITH_YOUR_FLASK_BACKEND_URL` with that backend hostname, without `https://` and without a trailing slash.
5. Import this repository into Netlify. Netlify will use the included configuration and proxy every route to Flask.

SQLite and uploaded files are local to the backend instance. For durable production storage, use persistent disk storage or replace SQLite/uploads with managed storage.

## Testing

Generate the sample PDFs first, then run:

```powershell
python test_pipeline.py
```
# Automated Resume Reviewer for College Placement Cells

A full-stack, enterprise-grade web application built for university training and placement cells (TPOs), department coordinators, and college students to automatically review resumes, calculate ATS compatibility scores, detect grammatical errors, flag missing critical sections, and store analytics in a **MySQL** database.

---

## Architecture & Technology Stack

- **Backend:** Python + Flask
- **Frontend:** HTML5 + Modern CSS3 (Variables, Responsive Grid/Flexbox) + Vanilla JavaScript
- **Database:** MySQL (Relational schema: `students`, `resumes`, `resume_results`, `grammar_issues`, `missing_fields`)
- **PDF Extraction:** PyMuPDF (`fitz`) / `pdfplumber`
- **Grammar & Spell Checking:** `language_tool_python` with LanguageTool + Offline heuristic engine
- **ATS Scrutiny Engine:** Weighted scoring model (0–100%) benchmarking Contact Details, Placement Core Sections, Technical Keywords, Action Verbs, and Grammar.

## Deploy With Netlify

This project is a Flask application, so Netlify serves as the public URL and reverse-proxies requests to a Python backend. Netlify cannot run this Flask process by itself.

### 1. Deploy the backend

Create a web service on Render, Railway, or another Python host from this repository. The included `Procfile` starts it with Gunicorn. Set these environment variables on the backend:

```env
SECRET_KEY=use_a_long_random_value
TPO_USERNAME=tpo_admin
TPO_PASSWORD=use_a_long_random_value
MYSQL_HOST=your-managed-mysql-host
MYSQL_PORT=3306
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=placement_cell_db
ENABLE_SQLITE_FALLBACK=false
ENABLE_LANGUAGE_TOOL=false
```

Use the backend's public URL, for example `https://resume-reviewer.onrender.com`.

### 2. Connect Netlify

In `netlify.toml`, replace `REPLACE_WITH_YOUR_BACKEND_URL` with the backend hostname, without a trailing slash. Then import this repository into Netlify. Netlify will proxy the complete Flask app, including uploads, login, templates, and API routes.

The database must be managed MySQL in production. The local SQLite fallback and local `uploads/` directory are for development only and do not provide durable serverless storage.

---

## Project Structure

```
placement_resume_reviewer/
├── app.py                      # Flask application router & main execution server
├── config.py                   # App configurations, MySQL credentials & thresholds
├── database.py                 # MySQL / database connection manager & CRUD operations
├── database.sql                # Complete MySQL DDL schema (5 tables + indexes)
├── parser.py                   # PyMuPDF PDF text extractor & regex info parser
├── analyzer.py                 # ATS score engine, LanguageTool grammar checker & suggestion generator
├── generate_sample_pdf.py      # Automated script to generate 3 test student PDF resumes
├── requirements.txt            # Python package dependencies
├── .env.example                # Template for MySQL username and password
├── static/
│   ├── style.css               # Placement Cell design system, responsive UI & print stylesheet
│   └── script.js               # Drag-and-drop uploader, loading stepper & score gauge animation
├── templates/
│   ├── base.html               # Base layout with navbar, announcements & footer
│   ├── index.html              # Modern placement landing page with stats & workflow
│   ├── upload.html             # PDF drag-and-drop form with live step animation
│   ├── result.html             # Interactive ATS Result Dashboard & report print/export
│   └── history.html            # Database archive of all evaluated student resumes
└── sample_resumes/             # Directory where test PDF resumes are generated
```

---

## 1. Prerequisites

1. **Python 3.9+** installed on your system.
2. **MySQL Server** (XAMPP, WampServer, MySQL Workbench, or standard MySQL Server).
3. **Visual Studio Code (VS Code)**.

---

## 2. MySQL Database Setup

### Step 2.1: Start MySQL Server
Ensure MySQL is running on port `3306` (e.g. start MySQL in **XAMPP Control Panel** or run `net start mysql` in Windows Terminal).

### Step 2.2: Create the Database & Tables
Open **MySQL Workbench**, **phpMyAdmin** (`http://localhost/phpmyadmin`), or your MySQL Command Line Client, and run the SQL script:

```sql
SOURCE C:/Users/WELCOME/.gemini/antigravity/scratch/placement_resume_reviewer/database.sql;
```

Or execute the commands manually:
```sql
CREATE DATABASE IF NOT EXISTS placement_cell_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE placement_cell_db;

-- 1. Students Table
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(25),
    branch VARCHAR(100),
    graduation_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Resumes Table
CREATE TABLE IF NOT EXISTS resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT DEFAULT 0,
    extracted_text LONGTEXT,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Resume Analysis Results Table
CREATE TABLE IF NOT EXISTS resume_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_id INT NOT NULL,
    ats_score DECIMAL(5,2) NOT NULL,
    contact_score DECIMAL(5,2) DEFAULT 0.00,
    sections_score DECIMAL(5,2) DEFAULT 0.00,
    skills_score DECIMAL(5,2) DEFAULT 0.00,
    grammar_score DECIMAL(5,2) DEFAULT 0.00,
    formatting_score DECIMAL(5,2) DEFAULT 0.00,
    status_level VARCHAR(20) DEFAULT 'Needs Improvement',
    detected_skills TEXT,
    target_role VARCHAR(100) DEFAULT 'Software Engineer',
    summary_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Grammar Issues Table
CREATE TABLE IF NOT EXISTS grammar_issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_id INT NOT NULL,
    issue_type VARCHAR(50) DEFAULT 'Grammar',
    rule_id VARCHAR(100),
    message TEXT NOT NULL,
    context_snippet TEXT,
    suggested_fix TEXT,
    char_offset INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Missing Fields Table
CREATE TABLE IF NOT EXISTS missing_fields (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_id INT NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    field_category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'Medium',
    suggestion TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
) ENGINE=InnoDB;
```

---

## 3. How to Configure MySQL Username / Password

You can configure MySQL credentials using either `.env` or directly inside `config.py`:

### Option A: Using `.env` file (Recommended)
Create a file named `.env` in the root folder (or copy `.env.example` to `.env`):
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_mysql_password
MYSQL_DB=placement_cell_db
SECRET_KEY=placement_cell_super_secret_key_12345
```

### Option B: Directly in `config.py`
Open `config.py` and modify lines 15-20:
```python
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_mysql_password'  # Leave empty '' if using default root without password
MYSQL_DB = 'placement_cell_db'
```

> **Note:** If MySQL server is temporarily offline or unreachable, the application automatically enables fallback mode (SQLite) so development and testing never stall!

---

## 4. Exact VS Code Setup Instructions

1. **Open VS Code**.
2. Go to **File -> Open Folder...** and select:
   `C:\Users\WELCOME\.gemini\antigravity\scratch\placement_resume_reviewer`
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

---

## 5. Sample Resume Testing & Scenarios

The project includes 3 pre-generated sample student resumes located in `sample_resumes/`:

| File Name | Candidate | Target Role | Expected ATS Score | Key Features |
| :--- | :--- | :--- | :--- | :--- |
| **`sample_high_score_resume.pdf`** | Priya Sharma | Software Engineer | **90% - 96% (Green)** | Full contact details, GitHub/LinkedIn links, Education, Categorized Technical Skills, Internship, 2 Projects with metrics, AWS certification. |
| **`sample_medium_score_resume.pdf`** | Rohan Verma | Full Stack Dev | **65% - 75% (Amber)** | Good core sections, but contains subtle grammar mistakes (*"I am study"*, *"Work as a intern"*), and missing certifications. |
| **`sample_low_score_resume.pdf`** | Kunal | Software Engineer | **25% - 40% (Red)** | Incomplete profile, missing contact phone/email, no separate education/skills headers, missing projects. |

---

## 6. Detailed Explanation of Each File

- **`app.py`**:
  The central Flask web server. Handles routing (`/`, `/upload`, `/result/<id>`, `/history`, `/api/stats`), secure file storage in `uploads/`, invokes `parser.py` and `analyzer.py`, persists data into MySQL tables, and renders dynamic Jinja2 views.

- **`config.py`**:
  Application configuration class loading environment variables for MySQL host, port, user, password, database name, upload limits (16MB max), allowed extensions (`.pdf`), and grammar threshold limits.

- **`database.py`**:
  Database abstraction layer. Establishes connection to MySQL with automatic fallback to SQLite. Provides helper CRUD functions: `init_db()`, `save_student()`, `save_resume()`, `save_analysis_results()`, `save_grammar_issues()`, `save_missing_fields()`, `get_result_by_resume_id()`, `get_all_resumes()`, and `get_stats()`.

- **`database.sql`**:
  Pure SQL DDL script creating `placement_cell_db` and the 5 relational tables (`students`, `resumes`, `resume_results`, `grammar_issues`, `missing_fields`) with foreign key constraints, cascading deletes, and optimized query indexes.

- **`parser.py`**:
  High-performance PDF parser using PyMuPDF (`fitz`) and regex. Extracts raw text, line structures, contact information (Name, Email, Phone, LinkedIn, GitHub, Portfolio), detects core sections (Education, Skills, Projects, Experience, Certifications), and classifies technical skills across 8 distinct domains.

- **`analyzer.py`**:
  Calculates the comprehensive 0-100% weighted ATS score. Evaluates contact completeness (15%), core section presence (25%), skills & keyword density (25%), formatting & action verbs (15%), and grammar accuracy (20%). Integrates `language_tool_python` to detect typos and grammar issues with context snippets.

- **`templates/index.html`**:
  Modern placement cell landing page with hero banner, live placement metrics (Total evaluated, Average ATS, Placement Ready count), 4-step workflow, and feature showcases.

- **`templates/upload.html`**:
  Interactive resume upload page featuring student metadata inputs, target role selector, drag-and-drop PDF dropzone, validation, and a live multi-step processing loading animation.

- **`templates/result.html`**:
  Placement ATS Diagnostic Dashboard featuring an animated circular score gauge, Green/Yellow/Red status cards, missing fields table, grammar & spelling fixes with snippets, extracted skills matrix, and a 1-click **Print / Download PDF Report** button.

- **`templates/history.html`**:
  Archive page displaying past student submissions, roll numbers, branches, ATS scores, and links to detailed audit reports.

- **`static/style.css`**:
  Complete design system featuring CSS variables, modern card layouts, circular progress charts, responsive grids/flexbox, typography, and print media rules.

- **`static/script.js`**:
  Client-side controller managing mobile navbar toggling, drag-and-drop file upload events, file size/type validation, multi-step loading overlay animation, and circular score chart rendering.

- **`generate_sample_pdf.py`**:
  Standalone utility script generating 3 realistic sample student resumes in PDF format for immediate testing and demonstration.

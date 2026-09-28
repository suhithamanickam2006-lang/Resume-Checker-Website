import json
import sqlite3

from config import Config


def get_db_connection():
    """Open the local SQLite database used by the application."""
    connection = sqlite3.connect(Config.SQLITE_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Create the tables required by the application if they do not exist."""
    try:
        conn = get_db_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                branch TEXT,
                graduation_year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                extracted_text TEXT,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS resume_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                ats_score REAL NOT NULL,
                contact_score REAL DEFAULT 0.0,
                sections_score REAL DEFAULT 0.0,
                skills_score REAL DEFAULT 0.0,
                grammar_score REAL DEFAULT 0.0,
                formatting_score REAL DEFAULT 0.0,
                status_level TEXT DEFAULT 'Needs Improvement',
                detected_skills TEXT,
                target_role TEXT DEFAULT 'Software Engineer',
                summary_feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS grammar_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                issue_type TEXT DEFAULT 'Grammar',
                rule_id TEXT,
                message TEXT NOT NULL,
                context_snippet TEXT,
                suggested_fix TEXT,
                char_offset INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS missing_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                field_category TEXT NOT NULL,
                severity TEXT DEFAULT 'Medium',
                suggestion TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        conn.close()
        print("[Database] SQLite tables verified/created successfully.")
    except Exception as error:
        print(f"[Database Error] Initialization failed: {error}")


def save_student(roll_number, name, email, phone="", branch="", graduation_year=None):
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO students (roll_number, name, email, phone, branch, graduation_year)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(roll_number) DO UPDATE SET
                name = excluded.name,
                email = excluded.email,
                phone = excluded.phone,
                branch = excluded.branch,
                graduation_year = excluded.graduation_year
        """, (roll_number, name, email, phone, branch, graduation_year))
        conn.commit()
        row = conn.execute(
            "SELECT id FROM students WHERE roll_number = ?", (roll_number,)
        ).fetchone()
        return row['id'] if row else None
    finally:
        conn.close()


def save_resume(student_id, file_name, file_path, file_size, extracted_text):
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO resumes (student_id, file_name, file_path, file_size, extracted_text)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, file_name, file_path, file_size, extracted_text))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def save_analysis_results(resume_id, ats_score, contact_score, sections_score, skills_score,
                          grammar_score, formatting_score, status_level, detected_skills,
                          target_role, summary_feedback):
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO resume_results (
                resume_id, ats_score, contact_score, sections_score, skills_score,
                grammar_score, formatting_score, status_level, detected_skills,
                target_role, summary_feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (resume_id, ats_score, contact_score, sections_score, skills_score,
              grammar_score, formatting_score, status_level,
              json.dumps(detected_skills) if isinstance(detected_skills, (list, dict))
              else str(detected_skills), target_role, summary_feedback))
        conn.commit()
    finally:
        conn.close()


def save_grammar_issues(resume_id, grammar_issues):
    if not grammar_issues:
        return
    conn = get_db_connection()
    try:
        conn.executemany("""
            INSERT INTO grammar_issues
                (resume_id, issue_type, rule_id, message, context_snippet, suggested_fix, char_offset)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [(
            resume_id, issue.get('issue_type', 'Grammar'), issue.get('rule_id', ''),
            issue.get('message', ''), issue.get('context_snippet', ''),
            issue.get('suggested_fix', ''), issue.get('char_offset', 0)
        ) for issue in grammar_issues])
        conn.commit()
    finally:
        conn.close()


def save_missing_fields(resume_id, missing_fields):
    if not missing_fields:
        return
    conn = get_db_connection()
    try:
        conn.executemany("""
            INSERT INTO missing_fields
                (resume_id, field_name, field_category, severity, suggestion)
            VALUES (?, ?, ?, ?, ?)
        """, [(
            resume_id, item.get('field_name', ''), item.get('field_category', 'General'),
            item.get('severity', 'Medium'), item.get('suggestion', '')
        ) for item in missing_fields])
        conn.commit()
    finally:
        conn.close()


def get_result_by_resume_id(resume_id):
    conn = get_db_connection()
    try:
        row = conn.execute("""
            SELECT r.id AS resume_id, r.file_name, r.file_size, r.upload_timestamp, r.extracted_text,
                   s.id AS student_id, s.roll_number, s.name, s.email, s.phone, s.branch, s.graduation_year,
                   rr.ats_score, rr.contact_score, rr.sections_score, rr.skills_score,
                   rr.grammar_score, rr.formatting_score, rr.status_level, rr.detected_skills,
                   rr.target_role, rr.summary_feedback
            FROM resumes r
            JOIN students s ON r.student_id = s.id
            LEFT JOIN resume_results rr ON rr.resume_id = r.id
            WHERE r.id = ?
        """, (resume_id,)).fetchone()
        if not row:
            return None

        info = dict(row)
        try:
            info['detected_skills_list'] = json.loads(info.get('detected_skills') or '[]')
        except (TypeError, json.JSONDecodeError):
            info['detected_skills_list'] = []
        return {
            'info': info,
            'grammar_issues': [dict(item) for item in conn.execute(
                "SELECT * FROM grammar_issues WHERE resume_id = ? ORDER BY id ASC", (resume_id,)
            ).fetchall()],
            'missing_fields': [dict(item) for item in conn.execute(
                "SELECT * FROM missing_fields WHERE resume_id = ? ORDER BY id ASC", (resume_id,)
            ).fetchall()]
        }
    finally:
        conn.close()


def search_resumes(query=None, branch=None, status=None, role=None, limit=200):
    conn = get_db_connection()
    try:
        sql = """
            SELECT r.id AS resume_id, r.file_name, r.upload_timestamp,
                   s.roll_number, s.name, s.branch, s.email, s.phone, s.graduation_year,
                   rr.ats_score, rr.status_level, rr.target_role, rr.skills_score, rr.grammar_score
            FROM resumes r
            JOIN students s ON r.student_id = s.id
            LEFT JOIN resume_results rr ON rr.resume_id = r.id
            WHERE 1=1
        """
        params = []
        if query:
            sql += " AND (s.name LIKE ? OR s.roll_number LIKE ? OR s.email LIKE ?)"
            params.extend([f"%{query}%"] * 3)
        if branch and branch != "All":
            sql += " AND s.branch = ?"
            params.append(branch)
        if status == "Ready":
            sql += " AND rr.ats_score >= 75"
        elif status == "NeedsWork":
            sql += " AND rr.ats_score < 75"
        if role and role != "All":
            sql += " AND rr.target_role = ?"
            params.append(role)
        sql += " ORDER BY r.upload_timestamp DESC LIMIT ?"
        params.append(limit)
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_all_resumes(limit=50):
    return search_resumes(limit=limit)


def get_student_resumes(roll_number):
    return search_resumes(query=roll_number)


def get_tpo_analytics():
    conn = get_db_connection()
    analytics = {
        'total_resumes': 0, 'avg_score': 0.0, 'ready_count': 0,
        'needs_work_count': 0, 'departments': [], 'roles': []
    }
    try:
        row = conn.execute("""
            SELECT COUNT(*) AS total_resumes, COALESCE(AVG(ats_score), 0) AS avg_score,
                   SUM(CASE WHEN ats_score >= 75 THEN 1 ELSE 0 END) AS ready_count,
                   SUM(CASE WHEN ats_score < 75 THEN 1 ELSE 0 END) AS needs_work_count
            FROM resume_results
        """).fetchone()
        if row:
            analytics['total_resumes'] = row['total_resumes'] or 0
            analytics['avg_score'] = round(float(row['avg_score'] or 0), 1)
            analytics['ready_count'] = row['ready_count'] or 0
            analytics['needs_work_count'] = row['needs_work_count'] or 0

        analytics['departments'] = [dict(item) for item in conn.execute("""
            SELECT s.branch, COUNT(*) AS count, ROUND(AVG(rr.ats_score), 1) AS avg_dept_score
            FROM resumes r JOIN students s ON r.student_id = s.id
            LEFT JOIN resume_results rr ON rr.resume_id = r.id
            GROUP BY s.branch ORDER BY count DESC
        """).fetchall()]
        analytics['roles'] = [dict(item) for item in conn.execute("""
            SELECT rr.target_role, COUNT(*) AS count
            FROM resume_results rr GROUP BY rr.target_role ORDER BY count DESC
        """).fetchall()]
    except Exception as error:
        print(f"[Analytics Error] {error}")
    finally:
        conn.close()
    return analytics


def get_stats():
    return get_tpo_analytics()


def delete_resume(resume_id):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
        conn.commit()
        return True
    except Exception as error:
        print(f"[Delete Error] {error}")
        return False
    finally:
        conn.close()
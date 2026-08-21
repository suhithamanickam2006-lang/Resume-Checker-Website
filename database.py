import mysql.connector
from mysql.connector import Error
import sqlite3
import os
import json
from config import Config

def get_db_connection():
    """
    Attempts to establish a MySQL connection.
    If MySQL server is unreachable and fallback is enabled, returns a SQLite connection.
    """
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4',
            use_unicode=True
        )
        if connection.is_connected():
            return connection, 'mysql'
    except Error as e:
        print(f"[Database Notice] MySQL ({Config.MYSQL_USER}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}) error: {e}")
        if Config.ENABLE_SQLITE_FALLBACK:
            conn = sqlite3.connect(Config.SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn, 'sqlite'
        else:
            raise e
    except Exception as general_err:
        if Config.ENABLE_SQLITE_FALLBACK:
            conn = sqlite3.connect(Config.SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn, 'sqlite'
        raise general_err


def init_db():
    """
    Initializes required tables in the database (MySQL or SQLite fallback).
    """
    try:
        # Try creating MySQL database first if it doesn't exist
        try:
            root_conn = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD
            )
            if root_conn.is_connected():
                cursor = root_conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.close()
                root_conn.close()
        except Exception:
            pass

        conn, db_type = get_db_connection()
        cursor = conn.cursor()

        if db_type == 'mysql':
            tables = [
                """
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
                """,
                """
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
                """,
                """
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
                """,
                """
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
                """,
                """
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
                """
            ]
            for t in tables:
                cursor.execute(t)
            conn.commit()
            print("[Database] MySQL tables verified/created successfully.")
        else:
            # SQLite syntax
            cursor.execute("""
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
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                extracted_text TEXT,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            );
            """)
            cursor.execute("""
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
                FOREIGN KEY (resume_id) REFERENCES resumes(id)
            );
            """)
            cursor.execute("""
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
                FOREIGN KEY (resume_id) REFERENCES resumes(id)
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS missing_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                field_category TEXT NOT NULL,
                severity TEXT DEFAULT 'Medium',
                suggestion TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id)
            );
            """)
            conn.commit()
            print("[Database] SQLite tables verified/created successfully.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[Database Error] Initialization failed: {e}")


def save_student(roll_number, name, email, phone="", branch="", graduation_year=None):
    """
    Saves student or updates existing student record by roll_number. Returns student_id.
    """
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    student_id = None

    try:
        if db_type == 'mysql':
            query = """
            INSERT INTO students (roll_number, name, email, phone, branch, graduation_year)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name),
                email = VALUES(email),
                phone = VALUES(phone),
                branch = VALUES(branch),
                graduation_year = VALUES(graduation_year)
            """
            cursor.execute(query, (roll_number, name, email, phone, branch, graduation_year))
            conn.commit()
            
            cursor.execute("SELECT id FROM students WHERE roll_number = %s", (roll_number,))
            row = cursor.fetchone()
            if row:
                student_id = row[0]
        else:
            query = """
            INSERT INTO students (roll_number, name, email, phone, branch, graduation_year)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(roll_number) DO UPDATE SET
                name = excluded.name,
                email = excluded.email,
                phone = excluded.phone,
                branch = excluded.branch,
                graduation_year = excluded.graduation_year
            """
            cursor.execute(query, (roll_number, name, email, phone, branch, graduation_year))
            conn.commit()
            cursor.execute("SELECT id FROM students WHERE roll_number = ?", (roll_number,))
            row = cursor.fetchone()
            if row:
                student_id = row[0] if isinstance(row, tuple) else row['id']

    finally:
        cursor.close()
        conn.close()

    return student_id


def save_resume(student_id, file_name, file_path, file_size, extracted_text):
    """
    Saves resume file record. Returns resume_id.
    """
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    resume_id = None

    try:
        if db_type == 'mysql':
            query = """
            INSERT INTO resumes (student_id, file_name, file_path, file_size, extracted_text)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (student_id, file_name, file_path, file_size, extracted_text))
            conn.commit()
            resume_id = cursor.lastrowid
        else:
            query = """
            INSERT INTO resumes (student_id, file_name, file_path, file_size, extracted_text)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(query, (student_id, file_name, file_path, file_size, extracted_text))
            conn.commit()
            resume_id = cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

    return resume_id


def save_analysis_results(resume_id, ats_score, contact_score, sections_score, skills_score, 
                          grammar_score, formatting_score, status_level, detected_skills, 
                          target_role, summary_feedback):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    skills_json = json.dumps(detected_skills) if isinstance(detected_skills, (list, dict)) else str(detected_skills)

    try:
        if db_type == 'mysql':
            query = """
            INSERT INTO resume_results (
                resume_id, ats_score, contact_score, sections_score, skills_score,
                grammar_score, formatting_score, status_level, detected_skills,
                target_role, summary_feedback
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                resume_id, ats_score, contact_score, sections_score, skills_score,
                grammar_score, formatting_score, status_level, skills_json,
                target_role, summary_feedback
            ))
            conn.commit()
        else:
            query = """
            INSERT INTO resume_results (
                resume_id, ats_score, contact_score, sections_score, skills_score,
                grammar_score, formatting_score, status_level, detected_skills,
                target_role, summary_feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                resume_id, ats_score, contact_score, sections_score, skills_score,
                grammar_score, formatting_score, status_level, skills_json,
                target_role, summary_feedback
            ))
            conn.commit()
    finally:
        cursor.close()
        conn.close()


def save_grammar_issues(resume_id, grammar_issues):
    if not grammar_issues:
        return

    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    try:
        if db_type == 'mysql':
            query = """
            INSERT INTO grammar_issues (resume_id, issue_type, rule_id, message, context_snippet, suggested_fix, char_offset)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            data = [
                (
                    resume_id,
                    issue.get('issue_type', 'Grammar'),
                    issue.get('rule_id', ''),
                    issue.get('message', ''),
                    issue.get('context_snippet', ''),
                    issue.get('suggested_fix', ''),
                    issue.get('char_offset', 0)
                )
                for issue in grammar_issues
            ]
            cursor.executemany(query, data)
            conn.commit()
        else:
            query = """
            INSERT INTO grammar_issues (resume_id, issue_type, rule_id, message, context_snippet, suggested_fix, char_offset)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            data = [
                (
                    resume_id,
                    issue.get('issue_type', 'Grammar'),
                    issue.get('rule_id', ''),
                    issue.get('message', ''),
                    issue.get('context_snippet', ''),
                    issue.get('suggested_fix', ''),
                    issue.get('char_offset', 0)
                )
                for issue in grammar_issues
            ]
            cursor.executemany(query, data)
            conn.commit()
    finally:
        cursor.close()
        conn.close()


def save_missing_fields(resume_id, missing_fields):
    if not missing_fields:
        return

    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    try:
        if db_type == 'mysql':
            query = """
            INSERT INTO missing_fields (resume_id, field_name, field_category, severity, suggestion)
            VALUES (%s, %s, %s, %s, %s)
            """
            data = [
                (
                    resume_id,
                    item.get('field_name', ''),
                    item.get('field_category', 'General'),
                    item.get('severity', 'Medium'),
                    item.get('suggestion', '')
                )
                for item in missing_fields
            ]
            cursor.executemany(query, data)
            conn.commit()
        else:
            query = """
            INSERT INTO missing_fields (resume_id, field_name, field_category, severity, suggestion)
            VALUES (?, ?, ?, ?, ?)
            """
            data = [
                (
                    resume_id,
                    item.get('field_name', ''),
                    item.get('field_category', 'General'),
                    item.get('severity', 'Medium'),
                    item.get('suggestion', '')
                )
                for item in missing_fields
            ]
            cursor.executemany(query, data)
            conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_result_by_resume_id(resume_id):
    conn, db_type = get_db_connection()
    cursor = conn.cursor(dictionary=True) if db_type == 'mysql' else conn.cursor()
    result = {}

    try:
        if db_type == 'mysql':
            q1 = """
            SELECT r.id AS resume_id, r.file_name, r.file_size, r.upload_timestamp, r.extracted_text,
                   s.id AS student_id, s.roll_number, s.name, s.email, s.phone, s.branch, s.graduation_year,
                   rr.ats_score, rr.contact_score, rr.sections_score, rr.skills_score,
                   rr.grammar_score, rr.formatting_score, rr.status_level, rr.detected_skills,
                   rr.target_role, rr.summary_feedback
            FROM resumes r
            JOIN students s ON r.student_id = s.id
            LEFT JOIN resume_results rr ON rr.resume_id = r.id
            WHERE r.id = %s
            """
            cursor.execute(q1, (resume_id,))
            resume_data = cursor.fetchone()
        else:
            q1 = """
            SELECT r.id AS resume_id, r.file_name, r.file_size, r.upload_timestamp, r.extracted_text,
                   s.id AS student_id, s.roll_number, s.name, s.email, s.phone, s.branch, s.graduation_year,
                   rr.ats_score, rr.contact_score, rr.sections_score, rr.skills_score,
                   rr.grammar_score, rr.formatting_score, rr.status_level, rr.detected_skills,
                   rr.target_role, rr.summary_feedback
            FROM resumes r
            JOIN students s ON r.student_id = s.id
            LEFT JOIN resume_results rr ON rr.resume_id = r.id
            WHERE r.id = ?
            """
            cursor.execute(q1, (resume_id,))
            row = cursor.fetchone()
            resume_data = dict(row) if row else None

        if not resume_data:
            return None

        result['info'] = resume_data
        
        try:
            if isinstance(resume_data.get('detected_skills'), str):
                result['info']['detected_skills_list'] = json.loads(resume_data['detected_skills'])
            else:
                result['info']['detected_skills_list'] = resume_data.get('detected_skills') or []
        except Exception:
            result['info']['detected_skills_list'] = []

        if db_type == 'mysql':
            cursor.execute("SELECT * FROM grammar_issues WHERE resume_id = %s ORDER BY id ASC", (resume_id,))
            result['grammar_issues'] = cursor.fetchall()
            cursor.execute("SELECT * FROM missing_fields WHERE resume_id = %s ORDER BY id ASC", (resume_id,))
            result['missing_fields'] = cursor.fetchall()
        else:
            cursor.execute("SELECT * FROM grammar_issues WHERE resume_id = ? ORDER BY id ASC", (resume_id,))
            result['grammar_issues'] = [dict(r) for r in cursor.fetchall()]
            cursor.execute("SELECT * FROM missing_fields WHERE resume_id = ? ORDER BY id ASC", (resume_id,))
            result['missing_fields'] = [dict(r) for r in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()

    return result


def search_resumes(query=None, branch=None, status=None, role=None, limit=200):
    """
    Powerful search and filter query for the Placement Cell (TPO) dashboard.
    """
    conn, db_type = get_db_connection()
    cursor = conn.cursor(dictionary=True) if db_type == 'mysql' else conn.cursor()
    resumes = []

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
        placeholder = "%s" if db_type == 'mysql' else "?"

        if query:
            sql += f" AND (s.name LIKE {placeholder} OR s.roll_number LIKE {placeholder} OR s.email LIKE {placeholder})"
            q_like = f"%{query}%"
            params.extend([q_like, q_like, q_like])

        if branch and branch != "All":
            sql += f" AND s.branch = {placeholder}"
            params.append(branch)

        if status and status != "All":
            if status == "Ready":
                sql += " AND rr.ats_score >= 75"
            elif status == "NeedsWork":
                sql += " AND rr.ats_score < 75"

        if role and role != "All":
            sql += f" AND rr.target_role = {placeholder}"
            params.append(role)

        sql += f" ORDER BY r.upload_timestamp DESC LIMIT {placeholder}"
        params.append(limit)

        cursor.execute(sql, tuple(params))
        if db_type == 'mysql':
            resumes = cursor.fetchall()
        else:
            resumes = [dict(r) for r in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()

    return resumes


def get_all_resumes(limit=50):
    return search_resumes(limit=limit)


def get_student_resumes(roll_number):
    """
    Fetches all submissions made by a student matching their roll number.
    """
    return search_resumes(query=roll_number)


def get_tpo_analytics():
    """
    Computes placement cell analytics (department stats, score tiers, role distributions).
    """
    conn, db_type = get_db_connection()
    cursor = conn.cursor(dictionary=True) if db_type == 'mysql' else conn.cursor()
    
    analytics = {
        'total_resumes': 0,
        'avg_score': 0.0,
        'ready_count': 0,
        'needs_work_count': 0,
        'departments': [],
        'roles': []
    }

    try:
        # Overview Stats
        cursor.execute("""
        SELECT 
            COUNT(*) as total_resumes,
            COALESCE(AVG(ats_score), 0) as avg_score,
            SUM(CASE WHEN ats_score >= 75 THEN 1 ELSE 0 END) as ready_count,
            SUM(CASE WHEN ats_score < 75 THEN 1 ELSE 0 END) as needs_work_count
        FROM resume_results
        """)
        row = cursor.fetchone()
        if row:
            if db_type != 'mysql': row = dict(row)
            analytics['total_resumes'] = row.get('total_resumes') or 0
            analytics['avg_score'] = round(float(row.get('avg_score') or 0), 1)
            analytics['ready_count'] = row.get('ready_count') or 0
            analytics['needs_work_count'] = row.get('needs_work_count') or 0

        # Department breakdown
        cursor.execute("""
        SELECT s.branch, COUNT(*) as count, ROUND(AVG(rr.ats_score), 1) as avg_dept_score
        FROM resumes r
        JOIN students s ON r.student_id = s.id
        LEFT JOIN resume_results rr ON rr.resume_id = r.id
        GROUP BY s.branch
        ORDER BY count DESC
        """)
        dept_rows = cursor.fetchall() if db_type == 'mysql' else [dict(r) for r in cursor.fetchall()]
        analytics['departments'] = dept_rows

        # Role breakdown
        cursor.execute("""
        SELECT rr.target_role, COUNT(*) as count
        FROM resume_results rr
        GROUP BY rr.target_role
        ORDER BY count DESC
        """)
        role_rows = cursor.fetchall() if db_type == 'mysql' else [dict(r) for r in cursor.fetchall()]
        analytics['roles'] = role_rows

    except Exception as e:
        print(f"[Analytics Error] {e}")
    finally:
        cursor.close()
        conn.close()

    return analytics


def get_stats():
    return get_tpo_analytics()


def delete_resume(resume_id):
    """
    Deletes resume and cascading linked results.
    """
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    try:
        placeholder = "%s" if db_type == 'mysql' else "?"
        cursor.execute(f"DELETE FROM resumes WHERE id = {placeholder}", (resume_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"[Delete Error] {e}")
        return False
    finally:
        cursor.close()
        conn.close()

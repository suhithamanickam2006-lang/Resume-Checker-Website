import os
import uuid
import csv
import io
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, Response, send_file
)
from werkzeug.utils import secure_filename

from config import Config
from database import (
    init_db, save_student, save_resume, save_analysis_results,
    save_grammar_issues, save_missing_fields, get_result_by_resume_id,
    get_all_resumes, get_tpo_analytics, search_resumes,
    get_student_resumes, delete_resume
)
from parser import parse_resume
from analyzer import analyze_complete_resume

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database schema on startup
with app.app_context():
    init_db()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def tpo_login_required(f):
    """
    Decorator to protect Placement Cell / TPO Admin routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('tpo_logged_in'):
            flash('Placement Cell login required to access this portal.', 'warning')
            return redirect(url_for('tpo_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# =======================================================================
# 1. STUDENT PORTAL ROUTES
# =======================================================================

@app.route('/')
def index():
    """
    Student Landing Page with live placement statistics.
    """
    analytics = get_tpo_analytics()
    return render_template('index.html', stats=analytics)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    Student Resume Upload & Diagnostic Pipeline.
    """
    if request.method == 'GET':
        return render_template('upload.html')

    # Validate file presence
    if 'resume_file' not in request.files:
        flash('No file uploaded. Please select a PDF resume.', 'danger')
        return redirect(request.url)

    file = request.files['resume_file']
    if file.filename == '':
        flash('No file selected. Please choose a PDF file.', 'danger')
        return redirect(request.url)

    if not allowed_file(file.filename):
        flash('Invalid file format. Only .PDF resumes are accepted.', 'warning')
        return redirect(request.url)

    try:
        # Secure filename with unique prefix to avoid collision
        original_name = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{original_name}"
        saved_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(saved_file_path)
        file_size = os.path.getsize(saved_file_path)

        # 1. Parse Resume with PyMuPDF
        parsed_data = parse_resume(saved_file_path)

        # 2. Form Inputs or Extracted Fallbacks
        roll_number = request.form.get('roll_number', '').strip()
        student_name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        branch = request.form.get('branch', 'Computer Science & Engineering').strip()
        grad_year_str = request.form.get('graduation_year', '').strip()
        target_role = request.form.get('target_role', 'Software Engineer').strip()

        # Fallback to extracted data if form fields were left blank
        contact = parsed_data.get('contact', {})
        if not student_name and contact.get('name'):
            student_name = contact['name']
        if not student_name:
            student_name = "Candidate"

        if not email and contact.get('email'):
            email = contact['email']
        if not email:
            email = f"student_{uuid.uuid4().hex[:6]}@college.edu"

        if not phone and contact.get('phone'):
            phone = contact['phone']

        if not roll_number:
            roll_number = f"STU-{uuid.uuid4().hex[:6].upper()}"

        try:
            graduation_year = int(grad_year_str) if grad_year_str else 2026
        except ValueError:
            graduation_year = 2026

        # 3. Analyze Resume (ATS Score, Grammar, Missing Fields)
        analysis_data = analyze_complete_resume(parsed_data, target_role=target_role)
        scores = analysis_data['scores']
        grammar_issues = analysis_data['grammar_issues']
        missing_fields = analysis_data['missing_fields']

        # 4. Save to Database (Students, Resumes, Results, Grammar, Missing Fields)
        student_id = save_student(
            roll_number=roll_number,
            name=student_name,
            email=email,
            phone=phone,
            branch=branch,
            graduation_year=graduation_year
        )

        resume_id = save_resume(
            student_id=student_id,
            file_name=original_name,
            file_path=saved_file_path,
            file_size=file_size,
            extracted_text=parsed_data.get('raw_text', '')
        )

        save_analysis_results(
            resume_id=resume_id,
            ats_score=scores['ats_score'],
            contact_score=scores['contact_score'],
            sections_score=scores['sections_score'],
            skills_score=scores['skills_score'],
            grammar_score=scores['grammar_score'],
            formatting_score=scores['formatting_score'],
            status_level=scores['status_level'],
            detected_skills=parsed_data.get('skills', {}).get('all', []),
            target_role=target_role,
            summary_feedback=scores['summary_feedback']
        )

        save_grammar_issues(resume_id, grammar_issues)
        save_missing_fields(resume_id, missing_fields)

        flash('Resume analyzed and scored successfully!', 'success')
        return redirect(url_for('result', resume_id=resume_id))

    except Exception as e:
        flash(f'An error occurred during resume processing: {str(e)}', 'danger')
        print(f"[App Error] Processing failure: {e}")
        return redirect(url_for('upload'))


@app.route('/result/<int:resume_id>')
def result(resume_id):
    """
    Student Diagnostic Result Dashboard with ATS Score & Fix Suggestions.
    """
    report = get_result_by_resume_id(resume_id)
    if not report:
        flash('Resume analysis record not found.', 'warning')
        return redirect(url_for('upload'))

    raw_text = report['info'].get('extracted_text', '')
    parsed = parse_resume_text_details(raw_text)

    return render_template(
        'result.html',
        info=report['info'],
        grammar_issues=report['grammar_issues'],
        missing_fields=report['missing_fields'],
        sections=parsed['sections'],
        skills_categorized=parsed['skills']['categorized'],
        all_skills=report['info'].get('detected_skills_list', []),
        action_verbs=parsed['action_verbs'],
        word_count=parsed['word_count']
    )


@app.route('/student/lookup', methods=['GET', 'POST'])
def student_lookup():
    """
    Allows students to look up their previous submissions using their Roll Number.
    """
    resumes = []
    searched_roll = ""

    if request.method == 'POST':
        searched_roll = request.form.get('roll_number', '').strip()
        if searched_roll:
            resumes = get_student_resumes(searched_roll)
            if not resumes:
                flash(f'No resume records found for Roll Number "{searched_roll}".', 'info')

    return render_template('student_lookup.html', resumes=resumes, searched_roll=searched_roll)


# =======================================================================
# 2. PLACEMENT CELL (TPO ADMIN) PORTAL ROUTES
# =======================================================================

@app.route('/tpo/login', methods=['GET', 'POST'])
def tpo_login():
    """
    Placement Cell Officer Login.
    """
    if session.get('tpo_logged_in'):
        return redirect(url_for('tpo_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username == Config.TPO_USERNAME and password == Config.TPO_PASSWORD:
            session['tpo_logged_in'] = True
            session['tpo_user'] = username
            flash('Successfully logged in to Placement Cell Portal.', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('tpo_dashboard'))
        else:
            flash('Invalid Placement Officer credentials. Please check username and password.', 'danger')

    return render_template('tpo_login.html')


@app.route('/tpo/logout')
def tpo_logout():
    """
    Placement Officer Logout.
    """
    session.pop('tpo_logged_in', None)
    session.pop('tpo_user', None)
    flash('Logged out of Placement Cell Portal.', 'info')
    return redirect(url_for('tpo_login'))


@app.route('/tpo/dashboard')
@tpo_login_required
def tpo_dashboard():
    """
    Executive Placement Cell (TPO) Dashboard:
    - View and filter all students across batches and departments
    - Track ATS score distribution and placement readiness
    """
    query = request.args.get('q', '').strip()
    branch = request.args.get('branch', 'All').strip()
    status = request.args.get('status', 'All').strip()
    role = request.args.get('role', 'All').strip()

    analytics = get_tpo_analytics()
    student_records = search_resumes(query=query, branch=branch, status=status, role=role, limit=300)

    return render_template(
        'tpo_dashboard.html',
        analytics=analytics,
        records=student_records,
        selected_query=query,
        selected_branch=branch,
        selected_status=status,
        selected_role=role
    )


@app.route('/tpo/export-csv')
@tpo_login_required
def tpo_export_csv():
    """
    Exports all student ATS scores and contact details to CSV for recruiters.
    """
    records = get_all_resumes(limit=5000)
    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow([
        'Resume ID', 'Roll Number', 'Student Name', 'Email', 'Phone',
        'Branch', 'Graduation Year', 'Target Role', 'ATS Score (%)',
        'Status Level', 'Skills Score (out of 25)', 'Grammar Score (out of 20)',
        'Evaluated Date'
    ])

    for r in records:
        writer.writerow([
            r.get('resume_id'),
            r.get('roll_number'),
            r.get('name'),
            r.get('email'),
            r.get('phone', 'N/A'),
            r.get('branch'),
            r.get('graduation_year', '2026'),
            r.get('target_role'),
            r.get('ats_score'),
            r.get('status_level'),
            r.get('skills_score'),
            r.get('grammar_score'),
            r.get('upload_timestamp')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=placement_cell_student_ats_scores.csv"}
    )


@app.route('/tpo/delete/<int:resume_id>', methods=['POST'])
@tpo_login_required
def tpo_delete(resume_id):
    """
    Deletes a student submission from Placement records.
    """
    if delete_resume(resume_id):
        flash('Student resume record deleted successfully.', 'success')
    else:
        flash('Failed to delete resume record.', 'danger')
    return redirect(url_for('tpo_dashboard'))


# =======================================================================
# 3. UTILITY & REDIRECT ROUTES
# =======================================================================

@app.route('/history')
@tpo_login_required
def history():
    """
    Placement master history (restricted strictly to authenticated TPO faculty).
    """
    return redirect(url_for('tpo_dashboard'))


@app.route('/api/stats')
def api_stats():
    """
    Public summary analytics.
    """
    stats = get_tpo_analytics()
    return jsonify(stats)


def parse_resume_text_details(text):
    """
    Helper function to extract categorized details for the dashboard display.
    """
    from parser import detect_sections, extract_skills
    from analyzer import evaluate_action_verbs

    sections = detect_sections(text)
    skills = extract_skills(text)
    action_verbs = evaluate_action_verbs(text)
    word_count = len(text.split())

    return {
        "sections": sections,
        "skills": skills,
        "action_verbs": action_verbs,
        "word_count": word_count
    }


@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="The requested page was not found."), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('index.html', error="An internal server error occurred."), 500


if __name__ == '__main__':
    print("=" * 60)
    print(" Starting Placement Cell Automated Resume Reviewer Server")
    print(" Student Portal: http://127.0.0.1:5000")
    print(" Placement Cell (TPO): http://127.0.0.1:5000/tpo/login")
    print(" (Default TPO Login: tpo_admin / admin123)")
    print("=" * 60)
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )

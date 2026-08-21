import re
import os
import unicodedata

# Try importing fitz (PyMuPDF), with fallback to pdfplumber
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


# Comprehensive Skills Database categorized by domain
SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "java", "c++", "c", "c#", "javascript", "typescript", "php", "ruby",
        "swift", "kotlin", "go", "golang", "rust", "scala", "r", "dart", "matlab", "sql"
    ],
    "Web & Frontend": [
        "html", "html5", "css", "css3", "sass", "bootstrap", "tailwind css", "react", "react.js",
        "angular", "vue.js", "next.js", "redux", "jquery", "rest api", "graphql", "webpack"
    ],
    "Backend & Frameworks": [
        "node.js", "express.js", "flask", "django", "fastapi", "spring boot", "asp.net",
        "laravel", "ruby on rails", "microservices", "restful apis"
    ],
    "Databases & Storage": [
        "mysql", "postgresql", "sqlite", "mongodb", "redis", "oracle", "mariadb",
        "firebase", "cassandra", "dynamodb", "elasticsearch", "neo4j"
    ],
    "Cloud & DevOps": [
        "aws", "amazon web services", "azure", "google cloud platform", "gcp", "docker",
        "kubernetes", "jenkins", "git", "github", "gitlab", "ci/cd", "terraform", "ansible", "linux"
    ],
    "AI, ML & Data Science": [
        "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
        "scikit-learn", "keras", "pandas", "numpy", "matplotlib", "seaborn", "opencv",
        "data analysis", "power bi", "tableau", "llm", "genai", "prompt engineering"
    ],
    "Core CS & Methodologies": [
        "data structures", "algorithms", "dsa", "object oriented programming", "oops",
        "system design", "operating systems", "dbms", "computer networks", "agile", "scrum"
    ],
    "Soft Skills": [
        "leadership", "teamwork", "problem solving", "communication", "time management",
        "critical thinking", "collaboration", "adaptability", "presentation"
    ]
}

# Common Section Header Patterns
SECTION_PATTERNS = {
    "education": [
        r"\b(education|academic background|academic qualifications|academics|educational details)\b"
    ],
    "skills": [
        r"\b(skills|technical skills|technical competencies|core competencies|technologies|tools & technologies|skill set)\b"
    ],
    "experience": [
        r"\b(experience|work experience|employment history|professional experience|internships|internship experience|work history)\b"
    ],
    "projects": [
        r"\b(projects|academic projects|personal projects|key projects|capstone project|portfolio projects)\b"
    ],
    "certifications": [
        r"\b(certifications|certificates|licenses & certifications|courses|training & certifications)\b"
    ],
    "achievements": [
        r"\b(achievements|awards|honors|extracurricular activities|leadership|co-curricular activities)\b"
    ]
}


def extract_text_from_pdf(pdf_path):
    """
    Extracts raw text, line list, and page count from a PDF file using PyMuPDF or pdfplumber.
    """
    text = ""
    num_pages = 0

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")

    # Primary method: PyMuPDF (fitz)
    if HAS_FITZ:
        try:
            doc = fitz.open(pdf_path)
            num_pages = len(doc)
            for page in doc:
                text += page.get_text("text") + "\n"
            doc.close()
        except Exception as e:
            print(f"[Parser Warning] PyMuPDF extraction issue: {e}")

    # Fallback method: pdfplumber
    if not text.strip() and HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"[Parser Warning] pdfplumber extraction issue: {e}")

    # Normalize unicode text
    cleaned_text = unicodedata.normalize("NFKD", text).strip()
    return cleaned_text, num_pages


def extract_contact_info(text):
    """
    Extracts Name, Email, Phone, LinkedIn, GitHub, Portfolio links from resume text.
    """
    contact = {
        "name": None,
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "portfolio": None
    }

    # 1. Email Regex
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    email_match = re.search(email_regex, text)
    if email_match:
        contact["email"] = email_match.group(0).lower()

    # 2. Phone Number Regex (Supports +91, (123), dashes, 10-digit Indian/US numbers)
    phone_regex = r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{4,5}\b'
    phone_matches = re.finditer(phone_regex, text)
    for m in phone_matches:
        raw_phone = m.group(0).strip()
        # Clean non-digits
        digits = re.sub(r'\D', '', raw_phone)
        if 10 <= len(digits) <= 13:
            contact["phone"] = raw_phone
            break

    # 3. LinkedIn Regex
    linkedin_regex = r'(https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+|linkedin\.com/in/[A-Za-z0-9_-]+)'
    linkedin_match = re.search(linkedin_regex, text, re.IGNORECASE)
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group(0)

    # 4. GitHub Regex
    github_regex = r'(https?://(?:www\.)?github\.com/[A-Za-z0-9_-]+|github\.com/[A-Za-z0-9_-]+)'
    github_match = re.search(github_regex, text, re.IGNORECASE)
    if github_match:
        contact["github"] = github_match.group(0)

    # 5. Portfolio / Personal Website
    portfolio_regex = r'(https?://[A-Za-z0-9.-]+\.(?:dev|me|io|in|app|site|tech|com)(?:/[^\s]*)?)'
    portfolio_matches = re.findall(portfolio_regex, text, re.IGNORECASE)
    for url in portfolio_matches:
        if "linkedin" not in url.lower() and "github" not in url.lower():
            contact["portfolio"] = url
            break

    # 6. Candidate Name Extraction Heuristics
    # Top 3 non-empty lines usually contain the candidate's name
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines[:5]:
        # Exclude headers, emails, links, or digits
        if "@" in line or "http" in line or "resume" in line.lower() or "curriculum" in line.lower():
            continue
        # Names are typically 2 to 4 capitalized words
        words = line.split()
        if 1 < len(words) <= 4:
            if all(w.isalpha() or w in ['.', '-'] for w in words):
                contact["name"] = line
                break

    return contact


def detect_sections(text):
    """
    Identifies which standard placement resume sections are present or missing.
    """
    text_lower = text.lower()
    sections_status = {}

    for section_name, patterns in SECTION_PATTERNS.items():
        found = False
        for pat in patterns:
            if re.search(pat, text_lower, re.IGNORECASE):
                found = True
                break
        sections_status[section_name] = found

    return sections_status


def extract_skills(text):
    """
    Matches keywords from the multi-domain taxonomy against resume text.
    """
    text_lower = text.lower()
    # Normalize punctuation for clean token matching
    normalized_text = re.sub(r'[,/|•;\(\)]', ' ', text_lower)
    words_set = set(normalized_text.split())

    categorized_skills = {}
    total_skills_detected = []

    for category, skill_list in SKILL_TAXONOMY.items():
        detected_in_cat = []
        for skill in skill_list:
            skill_clean = skill.lower()
            # For multi-word skills like "machine learning" or "spring boot"
            if " " in skill_clean or "." in skill_clean or "+" in skill_clean or "#" in skill_clean:
                # Use regex with boundary or exact match
                escaped = re.escape(skill_clean)
                if re.search(rf'(?:\b|^){escaped}(?:\b|$)', normalized_text):
                    detected_in_cat.append(skill.title() if len(skill) > 3 else skill.upper())
            else:
                if skill_clean in words_set:
                    detected_in_cat.append(skill.title() if len(skill) > 3 else skill.upper())

        if detected_in_cat:
            categorized_skills[category] = list(sorted(set(detected_in_cat)))
            total_skills_detected.extend(detected_in_cat)

    return {
        "categorized": categorized_skills,
        "all": list(sorted(set(total_skills_detected)))
    }


def parse_resume(pdf_path):
    """
    Main parser entrypoint. Returns structured resume dictionary.
    """
    raw_text, num_pages = extract_text_from_pdf(pdf_path)
    contact = extract_contact_info(raw_text)
    sections = detect_sections(raw_text)
    skills = extract_skills(raw_text)

    # Word and bullet count statistics
    word_count = len(raw_text.split())
    bullet_count = len(re.findall(r'[\u2022\u2023\u25E6\u2043\u2219\*\-]\s+', raw_text))

    return {
        "raw_text": raw_text,
        "num_pages": num_pages,
        "word_count": word_count,
        "bullet_count": bullet_count,
        "contact": contact,
        "sections": sections,
        "skills": skills
    }

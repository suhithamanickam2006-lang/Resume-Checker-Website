import re
from config import Config

# Try initializing LanguageTool with graceful fallback
_tool = None
_language_tool_available = False

def get_language_tool():
    global _tool, _language_tool_available
    if _tool is not None:
        return _tool
    
    if Config.ENABLE_LANGUAGE_TOOL:
        try:
            import language_tool_python
            _tool = language_tool_python.LanguageTool('en-US')
            _language_tool_available = True
            print("[LanguageTool] LanguageTool successfully initialized for grammar checking.")
        except Exception as e:
            print(f"[LanguageTool Notice] LanguageTool offline or Java not detected ({e}). Using built-in rule checker.")
            _language_tool_available = False
            _tool = None
    return _tool


# Role-specific recommended keywords for College Placements
ROLE_KEYWORD_RECOMMENDATIONS = {
    "Software Engineer": [
        "Data Structures", "Algorithms", "Python", "Java", "C++", "OOP", "DBMS", 
        "SQL", "Git", "System Design", "Problem Solving", "Linux"
    ],
    "Full Stack Developer": [
        "React", "Node.js", "Express.js", "JavaScript", "HTML5", "CSS3", "REST API",
        "MongoDB", "MySQL", "Git", "TypeScript", "Tailwind CSS"
    ],
    "Data Scientist / AI Engineer": [
        "Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
        "Pandas", "NumPy", "Scikit-Learn", "Data Analysis", "SQL", "Tableau", "NLP"
    ],
    "DevOps / Cloud Engineer": [
        "AWS", "Docker", "Kubernetes", "CI/CD", "Linux", "Terraform", "Git",
        "Jenkins", "Bash", "Ansible", "Cloud Security", "Monitoring"
    ],
    "Frontend Developer": [
        "HTML5", "CSS3", "JavaScript", "React", "TypeScript", "Redux", "Bootstrap",
        "Tailwind CSS", "Responsive Design", "UI/UX", "REST API"
    ],
    "Backend Developer": [
        "Java", "Python", "Node.js", "Spring Boot", "Django", "FastAPI", "PostgreSQL",
        "MySQL", "Redis", "Microservices", "Docker", "RESTful APIs"
    ]
}

# Strong Action Verbs for College Resumes
ACTION_VERBS = [
    "developed", "engineered", "designed", "implemented", "built", "created",
    "optimized", "architected", "integrated", "automated", "spearheaded",
    "deployed", "resolved", "collaborated", "managed", "delivered", "led",
    "refactored", "formulated", "established", "analyzed", "reduced", "improved"
]

# Common Spelling & Grammar Rule patterns for offline fallback
COMMON_GRAMMAR_RULES = [
    (r"\bi\s+am\s+study\b", "Grammar", "Use 'I am studying' or 'Pursuing'"),
    (r"\bresponsibe\b", "Spelling", "Did you mean 'responsible'?"),
    (r"\bexperiance\b", "Spelling", "Did you mean 'experience'?"),
    (r"\bknowlege\b", "Spelling", "Did you mean 'knowledge'?"),
    (r"\bcollaboration with\s+a\s+teams\b", "Grammar", "Use 'collaboration with teams' or 'a team'"),
    (r"\bwork as a\s+intern\b", "Grammar", "Use 'worked as an intern'"),
    (r"\breciever?\b", "Spelling", "Did you mean 'received' or 'receiver'?"),
    (r"\btechincal\b", "Spelling", "Did you mean 'technical'?")
]


def analyze_grammar(text):
    """
    Analyzes resume text for grammar and spelling errors using LanguageTool or regex fallback.
    """
    grammar_issues = []
    tool = get_language_tool()

    if tool and _language_tool_available:
        try:
            # Check up to first 3500 chars to maintain sub-second response
            sample_text = text[:3500]
            matches = tool.check(sample_text)
            for m in matches[:Config.MAX_GRAMMAR_ISSUES]:
                matched_str = sample_text[m.offset: m.offset + m.errorLength] if (hasattr(m, 'offset') and hasattr(m, 'errorLength')) else ""
                
                # Exclude false positives common in resumes (e.g. single letters, all-caps acronyms)
                if len(matched_str) <= 1 or (matched_str.isupper() and len(matched_str) > 1):
                    continue

                rule_id = getattr(m, 'ruleId', 'GRAMMAR_CHECK') or 'GRAMMAR_CHECK'
                rule_type = getattr(m, 'ruleIssueType', '') or ''
                
                issue_type = "Grammar"
                if "SPELLING" in str(rule_type).upper() or "MORFOLOGIK" in str(rule_id).upper() or "HUNSPELL" in str(rule_id).upper():
                    issue_type = "Spelling"
                elif "TYPOGRAPHY" in str(rule_type).upper() or "PUNCTUATION" in str(rule_type).upper():
                    issue_type = "Punctuation"

                context_snippet = getattr(m, 'context', '')
                if not context_snippet and hasattr(m, 'offset') and hasattr(m, 'errorLength'):
                    context_snippet = sample_text[max(0, m.offset - 25): min(len(sample_text), m.offset + m.errorLength + 25)]
                
                replacements = getattr(m, 'replacements', [])
                suggested_fix = replacements[0] if replacements else "Review phrasing"
                message = getattr(m, 'message', 'Grammar or spelling improvement suggested')

                grammar_issues.append({
                    "issue_type": issue_type,
                    "rule_id": rule_id,
                    "message": message,
                    "context_snippet": context_snippet.strip() if context_snippet else matched_str,
                    "suggested_fix": suggested_fix,
                    "char_offset": getattr(m, 'offset', 0)
                })
        except Exception as e:
            print(f"[Grammar Warning] LanguageTool check exception: {e}")

    # Fallback / augment with rule-based checks
    if len(grammar_issues) == 0:
        for pattern, issue_type, suggestion in COMMON_GRAMMAR_RULES:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                grammar_issues.append({
                    "issue_type": issue_type,
                    "rule_id": "RULE_MATCH",
                    "message": suggestion,
                    "context_snippet": text[start:end].strip(),
                    "suggested_fix": suggestion,
                    "char_offset": match.start()
                })

    return grammar_issues


def check_missing_fields(parsed_data, target_role="Software Engineer"):
    """
    Identifies missing contact details, sections, and role-specific keywords.
    """
    missing_fields = []
    contact = parsed_data.get("contact", {})
    sections = parsed_data.get("sections", {})
    detected_skills = [s.lower() for s in parsed_data.get("skills", {}).get("all", [])]

    # 1. Contact Info Checks
    if not contact.get("email"):
        missing_fields.append({
            "field_name": "Email Address",
            "field_category": "Contact",
            "severity": "High",
            "suggestion": "Add a professional email address (e.g. name@college.edu or name.dev@gmail.com) at the top of your resume."
        })
    if not contact.get("phone"):
        missing_fields.append({
            "field_name": "Phone Number",
            "field_category": "Contact",
            "severity": "High",
            "suggestion": "Add an active contact phone number with country code for recruiter callbacks."
        })
    if not contact.get("linkedin"):
        missing_fields.append({
            "field_name": "LinkedIn Profile",
            "field_category": "Contact",
            "severity": "Medium",
            "suggestion": "Include a link to your updated LinkedIn profile to build recruiter credibility."
        })
    if not contact.get("github"):
        missing_fields.append({
            "field_name": "GitHub Profile",
            "field_category": "Contact",
            "severity": "Medium",
            "suggestion": "Add your GitHub URL showing source code for personal and academic projects."
        })

    # 2. Section Checks
    if not sections.get("education"):
        missing_fields.append({
            "field_name": "Education Section",
            "field_category": "Core Section",
            "severity": "High",
            "suggestion": "College recruiters look for Degree, Branch, College Name, CGPA/Percentage, and Year of Graduation."
        })
    if not sections.get("skills"):
        missing_fields.append({
            "field_name": "Technical Skills Section",
            "field_category": "Core Section",
            "severity": "High",
            "suggestion": "Create a clear 'Skills' section categorized by Programming Languages, Frameworks, and Tools."
        })
    if not sections.get("projects"):
        missing_fields.append({
            "field_name": "Projects Section",
            "field_category": "Core Section",
            "severity": "High",
            "suggestion": "Include 2-3 prominent engineering projects with technologies used and quantifiable results."
        })
    if not sections.get("experience"):
        missing_fields.append({
            "field_name": "Experience / Internships",
            "field_category": "Core Section",
            "severity": "Medium",
            "suggestion": "Include summer internships, research assistantships, or student club technical lead roles."
        })
    if not sections.get("certifications"):
        missing_fields.append({
            "field_name": "Certifications",
            "field_category": "Core Section",
            "severity": "Low",
            "suggestion": "Add relevant online certificates (Coursera, AWS, HackerRank, NPTEL) to substantiate skills."
        })

    # 3. Target Role Keyword Gaps
    expected_keywords = ROLE_KEYWORD_RECOMMENDATIONS.get(target_role, ROLE_KEYWORD_RECOMMENDATIONS["Software Engineer"])
    missing_role_keywords = []
    for kw in expected_keywords:
        if kw.lower() not in detected_skills and kw.lower() not in parsed_data.get("raw_text", "").lower():
            missing_role_keywords.append(kw)

    if missing_role_keywords:
        sample_missing = missing_role_keywords[:4]
        missing_fields.append({
            "field_name": f"Keywords for {target_role}",
            "field_category": "Skill",
            "severity": "Medium",
            "suggestion": f"Consider showcasing keywords relevant to {target_role}: {', '.join(sample_missing)}."
        })

    return missing_fields, missing_role_keywords


def evaluate_action_verbs(text):
    """
    Checks if resume uses strong action verbs to describe accomplishments.
    """
    text_lower = text.lower()
    found_verbs = []
    for verb in ACTION_VERBS:
        if re.search(rf'\b{verb}\b', text_lower):
            found_verbs.append(verb.title())
    return found_verbs


def calculate_ats_score(parsed_data, grammar_issues, target_role="Software Engineer"):
    """
    Calculates weighted ATS Compatibility Score (0 - 100).
    Breakdown:
      - Contact Info: 15%
      - Core Sections: 25%
      - Skills & Keywords: 25%
      - Formatting & Verbs: 15%
      - Grammar & Spelling: 20%
    """
    contact = parsed_data.get("contact", {})
    sections = parsed_data.get("sections", {})
    skills = parsed_data.get("skills", {})
    all_skills = skills.get("all", [])
    raw_text = parsed_data.get("raw_text", "")
    num_pages = parsed_data.get("num_pages", 1)
    word_count = parsed_data.get("word_count", 0)

    # 1. Contact Score (Max 15)
    contact_score = 0
    if contact.get("name"): contact_score += 3
    if contact.get("email"): contact_score += 4
    if contact.get("phone"): contact_score += 4
    if contact.get("linkedin"): contact_score += 2
    if contact.get("github") or contact.get("portfolio"): contact_score += 2
    contact_score = min(15.0, float(contact_score))

    # 2. Sections Score (Max 25)
    sections_score = 0
    if sections.get("education"): sections_score += 7
    if sections.get("skills"): sections_score += 7
    if sections.get("projects"): sections_score += 6
    if sections.get("experience"): sections_score += 3
    if sections.get("certifications") or sections.get("achievements"): sections_score += 2
    sections_score = min(25.0, float(sections_score))

    # 3. Skills Score (Max 25)
    skills_score = 0
    num_skills = len(all_skills)
    if num_skills >= 10:
        skills_score += 15
    elif num_skills >= 5:
        skills_score += 10
    elif num_skills >= 2:
        skills_score += 5

    # Role keyword match
    expected_keywords = ROLE_KEYWORD_RECOMMENDATIONS.get(target_role, ROLE_KEYWORD_RECOMMENDATIONS["Software Engineer"])
    matched_role_kw = sum(1 for kw in expected_keywords if kw.lower() in [s.lower() for s in all_skills] or kw.lower() in raw_text.lower())
    role_match_ratio = matched_role_kw / max(1, len(expected_keywords))
    skills_score += role_match_ratio * 10
    skills_score = min(25.0, round(float(skills_score), 2))

    # 4. Formatting & Verbs (Max 15)
    formatting_score = 0
    # Page count check (1 page is ideal for freshers)
    if num_pages == 1:
        formatting_score += 4
    elif num_pages == 2:
        formatting_score += 3
    else:
        formatting_score += 1

    # Word count check (200 - 800 words is healthy)
    if 250 <= word_count <= 800:
        formatting_score += 4
    elif 150 <= word_count < 250:
        formatting_score += 2
    elif word_count > 800:
        formatting_score += 2

    # Action verbs check
    action_verbs = evaluate_action_verbs(raw_text)
    if len(action_verbs) >= 6:
        formatting_score += 4
    elif len(action_verbs) >= 3:
        formatting_score += 2
    else:
        formatting_score += 1

    # Bullet usage
    if parsed_data.get("bullet_count", 0) >= 4:
        formatting_score += 3
    else:
        formatting_score += 1

    formatting_score = min(15.0, float(formatting_score))

    # 5. Grammar & Spelling Score (Max 20)
    # Deduct 2 points per issue
    num_issues = len(grammar_issues)
    grammar_score = max(0.0, 20.0 - (num_issues * 2.0))

    # Total ATS Score
    total_ats = round(contact_score + sections_score + skills_score + formatting_score + grammar_score, 1)
    total_ats = max(10.0, min(100.0, total_ats))

    # Status Category
    if total_ats >= 80:
        status_level = "Excellent"
    elif total_ats >= 60:
        status_level = "Good"
    else:
        status_level = "Needs Improvement"

    # Generate constructive summary feedback
    feedback = []
    if total_ats >= 80:
        feedback.append("Excellent placement-ready resume! Well-structured with strong technical keywords and clean presentation.")
    elif total_ats >= 60:
        feedback.append("Good baseline resume. Enhancing project details, eliminating spelling/grammar errors, and adding quantifiable impact will make it top-tier.")
    else:
        feedback.append("Resume requires key structural updates before campus recruitment drives. Review the missing sections and contact details below.")

    if not contact.get("github") and not contact.get("linkedin"):
        feedback.append("Add LinkedIn and GitHub links to demonstrate practical code samples.")
    if len(action_verbs) < 4:
        feedback.append("Begin project bullet points with strong action verbs (e.g., 'Engineered', 'Optimized', 'Deployed').")
    if num_issues > 3:
        feedback.append(f"Resolve {num_issues} detected grammar/spelling inconsistencies to present a polished image.")

    return {
        "ats_score": total_ats,
        "contact_score": contact_score,
        "sections_score": sections_score,
        "skills_score": skills_score,
        "formatting_score": formatting_score,
        "grammar_score": grammar_score,
        "status_level": status_level,
        "action_verbs": action_verbs,
        "summary_feedback": " ".join(feedback)
    }


def analyze_complete_resume(parsed_data, target_role="Software Engineer"):
    """
    Runs full analysis pipeline on parsed resume data.
    """
    raw_text = parsed_data.get("raw_text", "")
    
    # 1. Grammar & Spelling Check
    grammar_issues = analyze_grammar(raw_text)

    # 2. Missing Fields Check
    missing_fields, missing_role_keywords = check_missing_fields(parsed_data, target_role)

    # 3. Calculate ATS Score
    scoring_result = calculate_ats_score(parsed_data, grammar_issues, target_role)

    return {
        "scores": scoring_result,
        "grammar_issues": grammar_issues,
        "missing_fields": missing_fields,
        "missing_role_keywords": missing_role_keywords
    }

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_sample_resumes():
    output_dir = os.path.join(os.path.dirname(__file__), "sample_resumes")
    os.makedirs(output_dir, exist_ok=True)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569'),
        alignment=0
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e40af'),
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1e293b')
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        leftIndent=12
    )

    # -------------------------------------------------------------
    # 1. High Score Sample Resume (Software Engineer / Full Stack)
    # -------------------------------------------------------------
    pdf1_path = os.path.join(output_dir, "sample_high_score_resume.pdf")
    doc1 = SimpleDocTemplate(pdf1_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story1 = []

    story1.append(Paragraph("PRIYA SHARMA", title_style))
    story1.append(Paragraph("Email: priya.sharma@college.edu | Phone: +91 98765 43210 | Bangalore, India", subtitle_style))
    story1.append(Paragraph("LinkedIn: linkedin.com/in/priyasharma-dev | GitHub: github.com/priyasharma | Portfolio: priya.dev", subtitle_style))
    story1.append(Spacer(1, 10))

    story1.append(Paragraph("EDUCATION", heading_style))
    story1.append(Paragraph("<b>B.Tech in Computer Science and Engineering</b> — National Institute of Technology (2022 – 2026)", body_style))
    story1.append(Paragraph("CGPA: 9.12 / 10.0 | Relevant Coursework: Data Structures, Algorithms, DBMS, Operating Systems, Computer Networks", bullet_style))
    story1.append(Spacer(1, 8))

    story1.append(Paragraph("TECHNICAL SKILLS", heading_style))
    story1.append(Paragraph("<b>Programming Languages:</b> Python, Java, C++, JavaScript, TypeScript, SQL", body_style))
    story1.append(Paragraph("<b>Web Technologies & Frameworks:</b> React, Node.js, Express.js, Flask, FastAPI, HTML5, CSS3, Tailwind CSS", body_style))
    story1.append(Paragraph("<b>Databases & Cloud:</b> MySQL, PostgreSQL, MongoDB, Redis, AWS (S3, EC2), Docker, Git, Linux", body_style))
    story1.append(Paragraph("<b>Core CS:</b> Object Oriented Programming (OOP), System Design, REST APIs, Microservices", body_style))
    story1.append(Spacer(1, 8))

    story1.append(Paragraph("EXPERIENCE & INTERNSHIPS", heading_style))
    story1.append(Paragraph("<b>Software Engineering Intern</b> — TechCorp Solutions (May 2025 – July 2025)", body_style))
    story1.append(Paragraph("• Engineered high-performance RESTful APIs using Python Flask and PostgreSQL, reducing latency by 35%.", bullet_style))
    story1.append(Paragraph("• Implemented automated CI/CD pipeline using Docker and GitHub Actions for continuous test deployment.", bullet_style))
    story1.append(Paragraph("• Collaborated with frontend team to integrate React dashboard with real-time WebSocket notifications.", bullet_style))
    story1.append(Spacer(1, 8))

    story1.append(Paragraph("PROJECTS", heading_style))
    story1.append(Paragraph("<b>Campus Placement Portal & Resume Parser</b> | <i>React, Flask, MySQL, PyMuPDF, Docker</i>", body_style))
    story1.append(Paragraph("• Developed full-stack web application used by 1,200+ students to track campus placement interviews.", bullet_style))
    story1.append(Paragraph("• Architected relational schema in MySQL and integrated automated PDF text extraction algorithms.", bullet_style))
    story1.append(Paragraph("• Optimized query performance with indexing, achieving sub-100ms response times on large datasets.", bullet_style))
    
    story1.append(Spacer(1, 4))
    story1.append(Paragraph("<b>Distributed Task Queue & Cache System</b> | <i>Python, Redis, RabbitMQ</i>", body_style))
    story1.append(Paragraph("• Built asynchronous task processor handling 5,000+ background requests with automated worker balancing.", bullet_style))
    story1.append(Paragraph("• Designed failover mechanism with Redis sentinel for 99.9% uptime during peak loads.", bullet_style))
    story1.append(Spacer(1, 8))

    story1.append(Paragraph("CERTIFICATIONS & ACHIEVEMENTS", heading_style))
    story1.append(Paragraph("• AWS Certified Cloud Practitioner (2025)", bullet_style))
    story1.append(Paragraph("• 5-Star Coder on HackerRank (Problem Solving, Python, SQL)", bullet_style))
    story1.append(Paragraph("• Finalist in National Smart India Hackathon (SIH 2024)", bullet_style))

    doc1.build(story1)
    print(f"[Generated] {pdf1_path}")

    # -------------------------------------------------------------
    # 2. Medium Score Sample Resume (Minor Grammar & Missing Certs)
    # -------------------------------------------------------------
    pdf2_path = os.path.join(output_dir, "sample_medium_score_resume.pdf")
    doc2 = SimpleDocTemplate(pdf2_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story2 = []

    story2.append(Paragraph("ROHAN VERMA", title_style))
    story2.append(Paragraph("Email: rohan.verma@gmail.com | Phone: 9845123456 | Pune, India", subtitle_style))
    story2.append(Paragraph("LinkedIn: linkedin.com/in/rohanverma", subtitle_style))
    story2.append(Spacer(1, 10))

    story2.append(Paragraph("EDUCATION", heading_style))
    story2.append(Paragraph("<b>Bachelor of Engineering in Information Technology</b> — Pune University (2022 - 2026)", body_style))
    story2.append(Paragraph("CGPA: 7.8 / 10.0", bullet_style))
    story2.append(Spacer(1, 8))

    story2.append(Paragraph("TECHNICAL SKILLS", heading_style))
    story2.append(Paragraph("Languages: Java, Python, JavaScript, HTML, CSS", body_style))
    story2.append(Paragraph("Databases: MySQL, MongoDB", body_style))
    story2.append(Paragraph("Tools: Git, VS Code, Eclipse", body_style))
    story2.append(Spacer(1, 8))

    story2.append(Paragraph("EXPERIENCE", heading_style))
    story2.append(Paragraph("<b>Web Developer Trainee</b> — Alpha Tech (June 2025 - July 2025)", body_style))
    story2.append(Paragraph("• I am study web design and created landing pages using HTML CSS.", bullet_style))
    story2.append(Paragraph("• Work as a intern to develop database queries in MySQL.", bullet_style))
    story2.append(Spacer(1, 8))

    story2.append(Paragraph("PROJECTS", heading_style))
    story2.append(Paragraph("<b>Online Library Management System</b> | <i>Java, MySQL, HTML</i>", body_style))
    story2.append(Paragraph("• Created library catalog for book issued and return records.", bullet_style))
    story2.append(Paragraph("• Built simple admin interface to manage student login accounts.", bullet_style))

    doc2.build(story2)
    print(f"[Generated] {pdf2_path}")

    # -------------------------------------------------------------
    # 3. Low Score Sample Resume (Missing Core Sections & Links)
    # -------------------------------------------------------------
    pdf3_path = os.path.join(output_dir, "sample_low_score_resume.pdf")
    doc3 = SimpleDocTemplate(pdf3_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story3 = []

    story3.append(Paragraph("KUNAL", title_style))
    story3.append(Paragraph("City: Delhi", subtitle_style))
    story3.append(Spacer(1, 10))

    story3.append(Paragraph("OBJECTIVE", heading_style))
    story3.append(Paragraph("Seeking good job in reputed software company where I can gain knowlege and experiance.", body_style))
    story3.append(Spacer(1, 10))

    story3.append(Paragraph("SUMMARY OF KNOWLEDGE", heading_style))
    story3.append(Paragraph("Have basic understand of computers, MS Office, basic C programming and internet browsing.", body_style))

    doc3.build(story3)
    print(f"[Generated] {pdf3_path}")


if __name__ == "__main__":
    create_sample_resumes()

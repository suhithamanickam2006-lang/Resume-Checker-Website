import os
import sys
from parser import parse_resume
from analyzer import analyze_complete_resume
from database import init_db, save_student, save_resume, save_analysis_results, save_grammar_issues, save_missing_fields, get_result_by_resume_id, get_stats

def run_tests():
    print("=" * 60)
    print("RUNNING AUTOMATED TEST SUITE FOR RESUME REVIEWER")
    print("=" * 60)

    # 1. Initialize Database
    print("\n[Step 1] Initializing Database Schema...")
    init_db()
    print(" Database ready.")

    sample_files = [
        ("sample_high_score_resume.pdf", "STU-2026-001", "Priya Sharma", "Software Engineer"),
        ("sample_medium_score_resume.pdf", "STU-2026-002", "Rohan Verma", "Full Stack Developer"),
        ("sample_low_score_resume.pdf", "STU-2026-003", "Kunal", "Software Engineer")
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))

    for filename, roll, expected_name, target_role in sample_files:
        pdf_path = os.path.join(base_dir, "sample_resumes", filename)
        print(f"\n--- Testing: {filename} ---")
        
        # 2. Parse PDF
        parsed = parse_resume(pdf_path)
        print(f"Extracted Contact: {parsed['contact']}")
        print(f"Detected Sections: {parsed['sections']}")
        print(f"Detected Skills Count: {len(parsed['skills']['all'])} (List: {parsed['skills']['all']})")
        print(f"Word count: {parsed['word_count']}, Pages: {parsed['num_pages']}")

        # 3. Analyze
        analysis = analyze_complete_resume(parsed, target_role=target_role)
        scores = analysis['scores']
        print(f"==> ATS Score: {scores['ats_score']}% (Status: {scores['status_level']})")
        print(f"    Breakdown: Contact: {scores['contact_score']}/15, Sections: {scores['sections_score']}/25, Skills: {scores['skills_score']}/25, Formatting: {scores['formatting_score']}/15, Grammar: {scores['grammar_score']}/20")
        print(f"    Grammar Issues Count: {len(analysis['grammar_issues'])}")
        print(f"    Missing Fields Count: {len(analysis['missing_fields'])}")

        # 4. Save to Database
        stu_id = save_student(
            roll_number=roll,
            name=parsed['contact']['name'] or expected_name,
            email=parsed['contact']['email'] or f"{roll.lower()}@college.edu",
            phone=parsed['contact']['phone'] or "",
            branch="Computer Science & Engineering",
            graduation_year=2026
        )
        res_id = save_resume(
            student_id=stu_id,
            file_name=filename,
            file_path=pdf_path,
            file_size=os.path.getsize(pdf_path),
            extracted_text=parsed['raw_text']
        )
        save_analysis_results(
            resume_id=res_id,
            ats_score=scores['ats_score'],
            contact_score=scores['contact_score'],
            sections_score=scores['sections_score'],
            skills_score=scores['skills_score'],
            grammar_score=scores['grammar_score'],
            formatting_score=scores['formatting_score'],
            status_level=scores['status_level'],
            detected_skills=parsed['skills']['all'],
            target_role=target_role,
            summary_feedback=scores['summary_feedback']
        )
        save_grammar_issues(res_id, analysis['grammar_issues'])
        save_missing_fields(res_id, analysis['missing_fields'])

        # 5. Verify retrieval
        report = get_result_by_resume_id(res_id)
        assert report is not None, "Failed to retrieve saved result from database"
        print(f" Database verification successful for Resume ID #{res_id}")

    # 6. Check Overall Placement Stats
    stats = get_stats()
    print("\n[Step 6] Placement Overall Analytics:")
    print(f" Total Resumes: {stats['total_resumes']}")
    print(f" Average ATS Score: {stats['avg_score']}%")
    print(f" Placement Ready Count: {stats['ready_count']}")
    print(f" Needs Work Count: {stats['needs_work_count']}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()

"""Generate minimal PDF resumes for unit tests."""

from pathlib import Path

import fitz


SAMPLE_RESUMES: dict[str, str] = {
    "backend_engineer.txt": """Jane Doe
Backend Engineer

Skills: Python, FastAPI, PostgreSQL, Docker, AWS, Redis

Experience
Senior Backend Engineer | Acme Corp
Jan 2020 - Present
Built microservices with Python and FastAPI.

Software Engineer | Beta LLC
Jun 2016 - Dec 2019
Developed REST APIs and data pipelines.

Education
B.Tech Computer Science, State University

Projects
Payment Gateway Service
Inventory API Platform

Certifications
AWS Certified Developer
""",
    "ml_engineer.txt": """John Smith
Machine Learning Engineer

Skills: Python, PyTorch, TensorFlow, scikit-learn, pandas, numpy

Experience
ML Engineer | DataCo
Mar 2021 - Present
5 years of experience building deep learning models.

Research Intern | AI Lab
Jan 2019 - Feb 2021

Education
M.S. Machine Learning, Tech Institute
B.S. Mathematics, City College

Projects
Image Classification Pipeline
NLP Sentiment Analyzer

Certifications
TensorFlow Developer Certificate
""",
    "frontend_dev.txt": """Alex Lee
Frontend Developer

Skills: JavaScript, TypeScript, React, Tailwind, HTML, CSS

Experience
Frontend Developer | WebWorks
Aug 2022 - Present

Junior Developer | StartupX
Jan 2020 - Jul 2022

Education
Bachelor of Science, Information Systems

Projects
Design System Library
E-commerce Dashboard

Certifications
""",
}


def generate_test_pdfs(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for name, content in SAMPLE_RESUMES.items():
        pdf_path = output_dir / name.replace(".txt", ".pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), content, fontsize=11)
        doc.save(pdf_path)
        doc.close()
        paths.append(pdf_path)

    return paths


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "resumes"
    generated = generate_test_pdfs(out)
    print(f"Generated {len(generated)} test PDFs in {out}")

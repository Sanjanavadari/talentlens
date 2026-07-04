"""Unit tests for rule-based resume field extraction."""

from app.services.info_extractor import (
    extract_certifications,
    extract_education,
    extract_projects,
    extract_skills,
    extract_structured_fields,
    extract_years_of_experience,
)

FULL_RESUME = """
Jane Doe
Senior Backend Engineer

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
"""

NO_CERTIFICATIONS_RESUME = """
Alex Lee
Frontend Developer

Skills: JavaScript, TypeScript, React, Tailwind, HTML, CSS

Experience
Frontend Developer | WebWorks
Aug 2022 - Present

Education
Bachelor of Science, Information Systems

Projects
Design System Library
"""

MULTI_DEGREE_RESUME = """
Dr. Aisha Rahman
Principal Machine Learning Scientist

Skills: Python, PyTorch, TensorFlow, scikit-learn, pandas, numpy

Experience
Principal ML Scientist | NeuroLabs
Jul 2017 - Present
8 years of experience deploying production ML systems.

Education
Ph.D. Computer Science, Stanford University
M.S. Artificial Intelligence, MIT
B.S. Mathematics, City College

Projects
Fraud Detection Transformer

Certifications
TensorFlow Developer Certificate
AWS Machine Learning Specialty
"""

AMBIGUOUS_YEARS_RESUME = """
Marcus Chen
Backend Engineer

Skills: Python, Django, MySQL, Docker

Experience
Backend Engineer | Horizon Systems
Mar 2021 - Present
3-5 years of experience shipping Django services.

Education
B.S. Computer Science, Midwest University

Projects
Subscription Billing API

Certifications
"""


def test_extract_skills_from_keyword_list() -> None:
    skills = extract_skills(FULL_RESUME)
    assert "python" in skills
    assert "fastapi" in skills
    assert "postgresql" in skills
    assert "docker" in skills
    assert "aws" in skills
    assert "redis" in skills


def test_extract_years_from_date_ranges() -> None:
    years = extract_years_of_experience(FULL_RESUME)
    assert years >= 5


def test_extract_years_from_explicit_mention() -> None:
    text = "ML Engineer with 5 years of experience building models."
    assert extract_years_of_experience(text) == 5.0


def test_extract_years_from_ambiguous_range() -> None:
    """Ambiguous ranges like '3-5 years of experience' use the upper bound."""
    years = extract_years_of_experience(AMBIGUOUS_YEARS_RESUME)
    assert years == 5.0


def test_extract_education_single_degree() -> None:
    education = extract_education(FULL_RESUME)
    assert len(education) >= 1
    assert any("B.Tech" in entry for entry in education)


def test_extract_education_multiple_degrees() -> None:
    education = extract_education(MULTI_DEGREE_RESUME)
    assert len(education) >= 2
    assert any("Ph.D" in entry or "Ph.D." in entry for entry in education)
    assert any("M.S." in entry for entry in education)


def test_extract_projects() -> None:
    projects = extract_projects(FULL_RESUME)
    assert len(projects) >= 2
    assert any("Payment" in project for project in projects)


def test_extract_certifications_present() -> None:
    certifications = extract_certifications(FULL_RESUME)
    assert len(certifications) >= 1
    assert any("AWS" in cert for cert in certifications)


def test_extract_certifications_absent() -> None:
    certifications = extract_certifications(NO_CERTIFICATIONS_RESUME)
    assert certifications == []


def test_structured_fields_full_resume() -> None:
    fields = extract_structured_fields(FULL_RESUME)
    assert "python" in fields["skills"]
    assert fields["years_of_experience"] >= 5
    assert any("B.Tech" in edu for edu in fields["education"])
    assert len(fields["projects"]) >= 1
    assert len(fields["certifications"]) >= 1
    assert fields["recent_experience_end"] == "Present"


def test_structured_fields_no_certifications() -> None:
    fields = extract_structured_fields(NO_CERTIFICATIONS_RESUME)
    assert "react" in fields["skills"]
    assert fields["certifications"] == []
    assert len(fields["projects"]) >= 1


def test_structured_fields_multiple_degrees() -> None:
    fields = extract_structured_fields(MULTI_DEGREE_RESUME)
    assert len(fields["education"]) >= 2
    assert fields["years_of_experience"] >= 8
    assert len(fields["certifications"]) >= 2


def test_structured_fields_ambiguous_year_range() -> None:
    fields = extract_structured_fields(AMBIGUOUS_YEARS_RESUME)
    assert fields["years_of_experience"] == 5.0
    assert fields["certifications"] == []

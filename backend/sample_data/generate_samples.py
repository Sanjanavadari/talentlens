"""Generate reproducible sample resumes (PDF) and job descriptions (TXT).

Run from repo root or backend/:
    python sample_data/generate_samples.py
"""

from __future__ import annotations

from pathlib import Path

import fitz

SAMPLE_ROOT = Path(__file__).resolve().parent
RESUMES_DIR = SAMPLE_ROOT / "resumes"
JOB_DESCRIPTIONS_DIR = SAMPLE_ROOT / "job_descriptions"

# Fixed, hand-authored content — deterministic across regenerations.
RESUME_PROFILES: dict[str, str] = {
    "01_jane_doe_backend_senior.pdf": """Jane Doe
Senior Backend Engineer

Skills: Python, FastAPI, PostgreSQL, Docker, AWS, Redis, REST, microservices

Experience
Senior Backend Engineer | Acme Corp
Jan 2020 - Present
Led Python microservices with FastAPI and PostgreSQL on AWS.

Software Engineer | Beta LLC
Jun 2016 - Dec 2019
Built REST APIs, Redis caching, and Docker-based deployments.

Education
B.Tech Computer Science, State University

Projects
Payment Gateway Service
Inventory API Platform

Certifications
AWS Certified Developer
""",
    "02_marcus_chen_backend_mid.pdf": """Marcus Chen
Backend Engineer

Skills: Python, Django, MySQL, Docker, Git, Linux, REST

Experience
Backend Engineer | Horizon Systems
Mar 2021 - Present
4 years of experience shipping Django services and MySQL schemas.

Junior Developer | CodeSpring
Jul 2019 - Feb 2021
Maintained REST endpoints and unit tests.

Education
B.S. Computer Science, Midwest University

Projects
Subscription Billing API
Admin Portal Backend

Certifications
""",
    "03_priya_sharma_backend_junior.pdf": """Priya Sharma
Junior Backend Developer

Skills: Python, Flask, SQL, Git, HTML

Experience
Backend Intern | LaunchPad Labs
Jun 2024 - Present
2 years of experience building Flask APIs and SQL queries.

Education
B.Tech Information Technology, Pune Institute

Projects
Campus Events API
Library Checkout Service

Certifications
""",
    "04_david_okonkwo_platform_senior.pdf": """David Okonkwo
Staff Platform Engineer

Skills: Go, Kubernetes, Docker, AWS, microservices, Linux, Terraform

Experience
Staff Platform Engineer | CloudScale Inc
May 2018 - Present
10 years of experience operating Go microservices on Kubernetes.

Platform Engineer | NetForge
Jan 2014 - Apr 2018
Built container platforms and CI/CD pipelines.

Education
M.S. Computer Engineering, Georgia Tech
B.E. Electronics, National Institute

Projects
Multi-tenant Service Mesh
Autoscaling Control Plane

Certifications
AWS Certified Solutions Architect
Kubernetes Administrator
""",
    "05_emily_watson_java_backend.pdf": """Emily Watson
Backend Engineer (Java)

Skills: Java, Spring, SQL, PostgreSQL, Docker, REST, Git

Experience
Backend Engineer | FinEdge
Aug 2020 - Present
Developed Spring Boot services and PostgreSQL data models.

Software Engineer | RetailSoft
Jun 2017 - Jul 2020
Integrated payment providers and REST APIs.

Education
Bachelor of Science, Software Engineering

Projects
Ledger Reconciliation Service
Fraud Detection API

Certifications
""",
    "06_alex_lee_frontend_mid.pdf": """Alex Lee
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
    "07_sofia_martinez_frontend_senior.pdf": """Sofia Martinez
Senior Frontend Engineer

Skills: TypeScript, React, Next.js, Tailwind, GraphQL, JavaScript, CSS

Experience
Senior Frontend Engineer | PixelCraft
Feb 2019 - Present
7 years of experience leading React and TypeScript product teams.

Frontend Engineer | AdVista
Jun 2016 - Jan 2019
Shipped design systems and GraphQL-driven dashboards.

Education
B.S. Computer Science, UCLA

Projects
Component Design System
Marketing Analytics Portal

Certifications
""",
    "08_james_park_frontend_junior.pdf": """James Park
Junior Frontend Developer

Skills: JavaScript, React, HTML, CSS, Git

Experience
Frontend Intern | BrightUI
May 2024 - Present
1 year of experience building React components and responsive layouts.

Education
Associate Degree, Web Development, City College

Projects
Portfolio Site Generator
Recipe Finder App

Certifications
""",
    "09_nina_kowalski_frontend_mid.pdf": """Nina Kowalski
Frontend Engineer

Skills: JavaScript, Vue, Angular, TypeScript, HTML, CSS, REST

Experience
Frontend Engineer | TravelHub
Sep 2021 - Present
Built Vue and Angular modules for booking flows.

UI Developer | MediaLoop
Jan 2019 - Aug 2021

Education
B.A. Digital Media, Warsaw University

Projects
Flight Search Widget
Accessibility Audit Toolkit

Certifications
""",
    "10_john_smith_ml_mid.pdf": """John Smith
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
    "11_aisha_rahman_ml_senior.pdf": """Dr. Aisha Rahman
Principal Machine Learning Scientist

Skills: Python, PyTorch, TensorFlow, deep learning, scikit-learn, pandas, numpy

Experience
Principal ML Scientist | NeuroLabs
Jul 2017 - Present
8 years of experience deploying production ML systems.

Research Scientist | VisionAI
Aug 2014 - Jun 2017
Published work on computer vision and NLP.

Education
Ph.D. Computer Science, Stanford University
M.S. Artificial Intelligence, MIT

Projects
Fraud Detection Transformer
Multimodal Search Ranking

Certifications
TensorFlow Developer Certificate
AWS Machine Learning Specialty
""",
    "12_kevin_tran_ml_junior.pdf": """Kevin Tran
Junior Machine Learning Engineer

Skills: Python, scikit-learn, pandas, numpy, SQL

Experience
ML Intern | Insight Analytics
Jun 2023 - Present
2 years of experience training scikit-learn models on tabular data.

Education
B.S. Statistics, Oregon State

Projects
Churn Prediction Notebook
Sales Forecasting Pipeline

Certifications
""",
    "13_laura_fischer_ml_mid.pdf": """Laura Fischer
Machine Learning Engineer

Skills: Python, PyTorch, pandas, numpy, SQL, REST

Experience
ML Engineer | LanguageLoop
Apr 2020 - Present
Built NLP microservices with PyTorch and FastAPI integrations.

Data Analyst | QueryPoint
Jul 2017 - Mar 2020

Education
M.S. Data Science, Berkeley
B.S. Computer Science, UC Davis

Projects
Entity Linking Service
Document Classifier API

Certifications
""",
    "14_omar_hassan_data_senior.pdf": """Omar Hassan
Senior Data Engineer

Skills: Python, Spark, Airflow, SQL, PostgreSQL, AWS, ETL, Kafka

Experience
Senior Data Engineer | StreamMetrics
Jan 2018 - Present
8 years of experience building Spark pipelines and Airflow DAGs.

Data Engineer | RetailLake
Mar 2014 - Dec 2017
Designed ETL jobs and PostgreSQL warehouses.

Education
M.S. Information Systems, UT Austin
B.Tech Computer Science, IIT Delhi

Projects
Real-time Clickstream Warehouse
Customer 360 Lakehouse

Certifications
AWS Certified Data Analytics
""",
    "15_rachel_green_data_mid.pdf": """Rachel Green
Data Engineer

Skills: Python, SQL, PostgreSQL, Airflow, ETL, pandas, Docker

Experience
Data Engineer | HealthSync
Oct 2020 - Present
Implemented Airflow workflows and PostgreSQL marts.

Analytics Engineer | CareMetrics
Jun 2018 - Sep 2020

Education
B.S. Mathematics, University of Michigan

Projects
Claims ETL Pipeline
Provider Quality Dashboard

Certifications
""",
    "16_tom_bradley_data_junior.pdf": """Tom Bradley
Junior Data Analyst

Skills: SQL, Python, pandas, Excel, Git

Experience
Data Analyst Intern | ShopMetrics
Jan 2024 - Present
1 year of experience writing SQL reports and pandas notebooks.

Education
Bachelor of Science, Economics, Boston University

Projects
Weekly Sales Dashboard
Inventory Variance Report

Certifications
""",
    "17_chris_morrison_devops_senior.pdf": """Chris Morrison
Senior DevOps Engineer

Skills: Kubernetes, Docker, Terraform, AWS, Linux, Ansible, Prometheus, Grafana

Experience
Senior DevOps Engineer | InfraCore
Apr 2017 - Present
9 years of experience running Kubernetes clusters and Terraform modules.

DevOps Engineer | ShipFast
Feb 2013 - Mar 2017
Built CI/CD and monitoring with Prometheus and Grafana.

Education
B.S. Computer Engineering, Virginia Tech

Projects
GitOps Deployment Platform
Multi-region Failover Automation

Certifications
AWS Certified DevOps Engineer
Kubernetes Administrator
""",
    "18_megan_liu_devops_mid.pdf": """Megan Liu
DevOps Engineer

Skills: Docker, Linux, Ansible, CI/CD, Git, AWS, Terraform

Experience
DevOps Engineer | SecureStack
Jul 2021 - Present
Managed Docker hosts, Ansible playbooks, and AWS staging environments.

Systems Administrator | LocalNet
Aug 2018 - Jun 2021

Education
B.Tech Information Technology, NUS

Projects
Immutable AMI Pipeline
Secrets Rotation Playbook

Certifications
""",
    "19_sam_irving_sre_junior.pdf": """Sam Irving
Junior Site Reliability Engineer

Skills: Linux, Docker, Git, Python, Prometheus

Experience
SRE Intern | Uptime Labs
May 2024 - Present
2 years of experience assisting on-call rotations and Docker compose stacks.

Education
Associate Degree, Network Administration

Projects
Uptime Dashboard Prototype
Log Shipping Script

Certifications
""",
    "20_olivia_turner_fullstack_mid.pdf": """Olivia Turner
Full-Stack Engineer

Skills: TypeScript, React, Node.js, Python, PostgreSQL, Docker, REST

Experience
Full-Stack Engineer | ProductNest
Mar 2020 - Present
5 years of experience delivering React frontends and Node.js APIs.

Software Engineer | Craftly
Jul 2018 - Feb 2020

Education
B.S. Computer Science, University of Washington

Projects
Collaboration Workspace
Billing Portal

Certifications
""",
}

JOB_DESCRIPTIONS: dict[str, str] = {
    "backend_engineer.txt": """Backend Engineer

About the role
We are hiring a Backend Engineer to design and operate production APIs and data services.

Requirements
- 5+ years of experience building backend services
- Strong proficiency in Python, FastAPI, PostgreSQL, Docker, and AWS
- Experience with Redis, REST APIs, and microservices architecture
- B.Tech, B.S., or equivalent degree in Computer Science or related field

Nice to have
- Kubernetes and event-driven systems
- Performance tuning and observability
""",
    "ml_engineer.txt": """Machine Learning Engineer

About the role
Join our AI platform team to train, evaluate, and deploy machine learning models at scale.

Requirements
- 4+ years of experience in machine learning engineering
- Python, PyTorch, TensorFlow, scikit-learn, pandas, and numpy
- Experience shipping NLP or computer vision models to production
- M.S. or Ph.D. in Machine Learning, Computer Science, or related field preferred

Nice to have
- Deep learning research background
- Model monitoring and A/B experimentation
""",
    "full_stack_engineer.txt": """Full-Stack Engineer

About the role
Build end-to-end product features across our React frontend and Node.js/Python backend.

Requirements
- 3+ years of experience as a full-stack software engineer
- TypeScript, React, Node.js, Python, PostgreSQL, Docker, and REST APIs
- Comfortable owning features from database schema to UI components
- Bachelor's degree or equivalent practical experience

Nice to have
- GraphQL and Next.js
- CI/CD and cloud deployment on AWS
""",
    "data_engineer.txt": """Data Engineer

About the role
Design reliable data pipelines and warehouse models that power analytics and ML features.

Requirements
- 5+ years of experience in data engineering
- Python, Spark, Airflow, SQL, PostgreSQL, AWS, ETL, and Kafka
- Experience building batch and streaming pipelines
- B.S. or M.S. in Computer Science, Information Systems, or related field

Nice to have
- Lakehouse architectures
- Data quality frameworks and lineage tooling
""",
    "devops_engineer.txt": """DevOps Engineer

About the role
Own our cloud infrastructure, deployment automation, and production reliability practices.

Requirements
- 6+ years of experience in DevOps or platform engineering
- Kubernetes, Docker, Terraform, AWS, Linux, Ansible, Prometheus, and Grafana
- Strong CI/CD pipeline design and incident response experience
- Bachelor's degree in Engineering or equivalent experience

Nice to have
- GitOps and multi-region failover
- Security hardening and compliance automation
""",
}


def write_text_pdf(pdf_path: Path, content: str, *, font_size: float = 10.0) -> None:
    """Render multi-line text into a PDF with automatic pagination."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # US Letter
    margin = 54
    line_height = font_size * 1.35
    x = margin
    y = margin
    max_y = 792 - margin
    writable_width = 612 - (2 * margin)

    for paragraph in content.strip().split("\n"):
        if not paragraph.strip():
            y += line_height
            continue

        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if fitz.get_text_length(candidate, fontname="helv", fontsize=font_size) <= writable_width:
                line = candidate
            else:
                if y + line_height > max_y:
                    page = doc.new_page(width=612, height=792)
                    y = margin
                page.insert_text((x, y), line, fontsize=font_size, fontname="helv")
                y += line_height
                line = word

        if line:
            if y + line_height > max_y:
                page = doc.new_page(width=612, height=792)
                y = margin
            page.insert_text((x, y), line, fontsize=font_size, fontname="helv")
            y += line_height

    doc.save(pdf_path)
    doc.close()


def generate_resume_pdfs(output_dir: Path = RESUMES_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for filename in sorted(RESUME_PROFILES):
        pdf_path = output_dir / filename
        write_text_pdf(pdf_path, RESUME_PROFILES[filename])
        paths.append(pdf_path)
    return paths


def generate_job_description_files(output_dir: Path = JOB_DESCRIPTIONS_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for filename in sorted(JOB_DESCRIPTIONS):
        txt_path = output_dir / filename
        txt_path.write_text(JOB_DESCRIPTIONS[filename].strip() + "\n", encoding="utf-8")
        paths.append(txt_path)
    return paths


def generate_all() -> tuple[list[Path], list[Path]]:
    resumes = generate_resume_pdfs()
    job_descriptions = generate_job_description_files()
    return resumes, job_descriptions


def main() -> None:
    resumes, job_descriptions = generate_all()
    print(f"Generated {len(resumes)} resume PDFs in {RESUMES_DIR}")
    print(f"Generated {len(job_descriptions)} job descriptions in {JOB_DESCRIPTIONS_DIR}")


if __name__ == "__main__":
    main()

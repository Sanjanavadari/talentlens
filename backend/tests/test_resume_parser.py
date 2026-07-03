from pathlib import Path

import pytest

from app.services.info_extractor import extract_structured_fields
from app.services.resume_parser import extract_text_from_pdf_bytes, extract_text_from_pdf_path
from tests.fixtures.generate_test_pdfs import SAMPLE_RESUMES, generate_test_pdfs


@pytest.fixture(scope="module")
def test_pdf_dir(tmp_path_factory) -> Path:
    directory = tmp_path_factory.mktemp("resumes")
    generate_test_pdfs(directory)
    return directory


def test_extract_text_from_pdf_path(test_pdf_dir: Path) -> None:
    backend_pdf = test_pdf_dir / "backend_engineer.pdf"
    text = extract_text_from_pdf_path(backend_pdf)
    assert "Jane Doe" in text
    assert "FastAPI" in text


def test_extract_structured_fields_backend() -> None:
    fields = extract_structured_fields(SAMPLE_RESUMES["backend_engineer.txt"])
    assert "python" in fields["skills"]
    assert "fastapi" in fields["skills"]
    assert fields["years_of_experience"] >= 5
    assert any("B.Tech" in edu for edu in fields["education"])
    assert len(fields["projects"]) >= 1
    assert len(fields["certifications"]) >= 1
    assert fields["recent_experience_end"] == "Present"


def test_extract_structured_fields_ml() -> None:
    fields = extract_structured_fields(SAMPLE_RESUMES["ml_engineer.txt"])
    assert "pytorch" in fields["skills"]
    assert "tensorflow" in fields["skills"]
    assert fields["years_of_experience"] >= 5
    assert any("M.S." in edu for edu in fields["education"])


def test_extract_structured_fields_frontend() -> None:
    fields = extract_structured_fields(SAMPLE_RESUMES["frontend_dev.txt"])
    assert "react" in fields["skills"]
    assert "typescript" in fields["skills"]
    assert fields["years_of_experience"] >= 2


def test_pdf_bytes_round_trip(test_pdf_dir: Path) -> None:
    pdf_path = test_pdf_dir / "frontend_dev.pdf"
    text = extract_text_from_pdf_bytes(pdf_path.read_bytes())
    fields = extract_structured_fields(text)
    assert "javascript" in fields["skills"]

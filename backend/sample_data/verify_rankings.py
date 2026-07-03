"""Upload sample resumes and rank against sample job descriptions."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_ROOT = BACKEND_ROOT / "sample_data"
RESUMES_DIR = SAMPLE_ROOT / "resumes"
JD_DIR = SAMPLE_ROOT / "job_descriptions"
DEFAULT_BASE_URL = "http://127.0.0.1:8002"


def upload_samples(client: httpx.Client) -> list[int]:
    ids: list[int] = []
    for pdf_path in sorted(RESUMES_DIR.glob("*.pdf")):
        with pdf_path.open("rb") as handle:
            response = client.post(
                "/api/v1/candidates/upload",
                files={"files": (pdf_path.name, handle, "application/pdf")},
            )
        response.raise_for_status()
        ids.append(response.json()[0]["id"])
    return ids


def rank_for_jd(
    client: httpx.Client,
    jd_path: Path,
    candidate_ids: list[int],
) -> dict:
    text = jd_path.read_text(encoding="utf-8")
    title = text.splitlines()[0].strip()
    response = client.post(
        "/api/v1/rank",
        json={
            "job_description_text": text,
            "job_description_title": title,
            "candidate_ids": candidate_ids,
        },
    )
    response.raise_for_status()
    return response.json()


def summarize_ranking(label: str, payload: dict) -> None:
    ranked = payload["ranked_candidates"]
    scores = [item["final_score"] for item in ranked]
    spread = max(scores) - min(scores) if scores else 0.0
    stddev = statistics.pstdev(scores) if len(scores) > 1 else 0.0

    print(f"\n=== {label} ===")
    print(f"Candidates ranked: {len(ranked)}")
    print(f"Score range: {min(scores):.3f} – {max(scores):.3f} (spread {spread:.3f}, stdev {stddev:.3f})")
    print("Rank order:")
    for item in ranked:
        skills = ", ".join(item["breakdown"]["matched_skills"][:5])
        trailing = "..." if len(item["breakdown"]["matched_skills"]) > 5 else ""
        print(
            f"  #{item['rank']:>2}  {item['final_score']:.3f}  "
            f"sem={item['semantic_score']:.3f} rule={item['rule_score']:.3f}  "
            f"{item['filename']}"
        )
        if skills:
            print(f"       matched: {skills}{trailing}")


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE_URL
    client = httpx.Client(base_url=base_url, timeout=120.0)

    print(f"Uploading resumes from {RESUMES_DIR} ...")
    candidate_ids = upload_samples(client)
    print(f"Uploaded {len(candidate_ids)} candidates.")

    for jd_name in ["backend_engineer.txt", "ml_engineer.txt", "devops_engineer.txt"]:
        jd_path = JD_DIR / jd_name
        payload = rank_for_jd(client, jd_path, candidate_ids)
        summarize_ranking(jd_name.replace(".txt", "").replace("_", " ").title(), payload)

    # Sanity assertions
    backend = rank_for_jd(client, JD_DIR / "backend_engineer.txt", candidate_ids)
    backend_top = backend["ranked_candidates"][0]["filename"]
    ml = rank_for_jd(client, JD_DIR / "ml_engineer.txt", candidate_ids)
    ml_top = ml["ranked_candidates"][0]["filename"]

    backend_scores = [c["final_score"] for c in backend["ranked_candidates"]]
    ml_scores = [c["final_score"] for c in ml["ranked_candidates"]]

    assert max(backend_scores) - min(backend_scores) >= 0.15, "Backend ranking too clustered"
    assert max(ml_scores) - min(ml_scores) >= 0.15, "ML ranking too clustered"
    assert "backend" in backend_top or "jane_doe" in backend_top or "david" in backend_top
    assert "ml" in ml_top or "aisha" in ml_top or "john_smith" in ml_top

    print("\nSanity checks passed.")


if __name__ == "__main__":
    main()

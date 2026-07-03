#!/usr/bin/env python3
"""Verify Docker Compose networking via the frontend Vite proxy."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

FRONTEND_BASE = "http://127.0.0.1:5173"
BACKEND_BASE = "http://127.0.0.1:8002"
SAMPLE_ROOT = Path(__file__).resolve().parent.parent / "backend" / "sample_data"


def main() -> None:
    backend = httpx.Client(base_url=BACKEND_BASE, timeout=120.0)
    frontend = httpx.Client(base_url=FRONTEND_BASE, timeout=120.0)

    print("Checking backend health (direct)...")
    health = backend.get("/health")
    health.raise_for_status()
    print(f"  OK: {health.json()}")

    print("Checking API through frontend proxy (/api/v1/candidates)...")
    listed = frontend.get("/api/v1/candidates")
    listed.raise_for_status()
    print(f"  OK: {len(listed.json())} candidates in database")

    resumes = sorted((SAMPLE_ROOT / "resumes").glob("*.pdf"))[:3]
    jd_text = (SAMPLE_ROOT / "job_descriptions" / "backend_engineer.txt").read_text()
    jd_title = jd_text.splitlines()[0].strip()

    print("Uploading sample resumes through frontend proxy...")
    uploaded_ids: list[int] = []
    for resume in resumes:
        with resume.open("rb") as handle:
            response = frontend.post(
                "/api/v1/candidates/upload",
                files={"files": (resume.name, handle, "application/pdf")},
            )
        response.raise_for_status()
        uploaded_ids.append(response.json()[0]["id"])
    print(f"  OK: uploaded {len(uploaded_ids)} resumes")

    print("Creating job description and ranking through frontend proxy...")
    jd = frontend.post(
        "/api/v1/job-descriptions",
        json={"title": jd_title, "text": jd_text},
    ).json()
    rank = frontend.post(
        "/api/v1/rank",
        json={
            "candidate_ids": uploaded_ids,
            "job_description_id": jd["id"],
            "job_description_text": jd_text,
            "job_description_title": jd_title,
        },
    )
    rank.raise_for_status()
    ranked = rank.json()["ranked_candidates"]
    scores = [item["final_score"] for item in ranked]
    assert scores == sorted(scores, reverse=True)

    print("Rank order:")
    for item in ranked:
        print(f"  #{item['rank']} {item['filename']} — {item['final_score']:.3f}")

    print("\nDocker Compose verification passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        sys.exit(1)

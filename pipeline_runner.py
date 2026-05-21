import argparse
import json
import os
from typing import List

import pdfplumber

from job_fetcher import fetch_and_save
from sbert_matcher import score_jobs_with_resume, save_shortlist


def load_resume_text(path: str) -> str:
    path = os.path.expanduser(path)
    if path.lower().endswith('.pdf'):
        with pdfplumber.open(path) as pdf:
            pages = [page.extract_text() or '' for page in pdf.pages]
        return '\n'.join(pages)

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def run_pipeline(
    query: str,
    location: str,
    source: str,
    pages: int,
    resume_path: str,
    top: int,
    shortlist_out: str,
    jobs_json: str,
    fetch_only: bool,
    score_only: bool,
) -> None:
    if not score_only:
        print('Starting job fetch...')
        jobs = fetch_and_save(query, location, source, pages)
        print(f'Fetched {len(jobs)} jobs and saved to {jobs_json}.')
    else:
        jobs = []

    if score_only:
        if os.path.exists(jobs_json):
            with open(jobs_json, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
        else:
            raise FileNotFoundError(f"Jobs file not found: {jobs_json}")

    if resume_path and not fetch_only:
        print('Loading resume and scoring jobs...')
        resume_text = load_resume_text(resume_path)
        scored = score_jobs_with_resume(resume_text, jobs)
        save_shortlist(scored, shortlist_out, top)
        print(f'Saved top {top} shortlisted jobs to {shortlist_out}.')
    elif not resume_path:
        print('No resume path provided; skipping scoring.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run job fetch and optional SBERT scoring in sequence.')
    parser.add_argument('query', help='Job search query, e.g. "data scientist".')
    parser.add_argument('--location', help='City or location.', default=None)
    parser.add_argument('--source', help='Source: naukri or indeed.', choices=['naukri', 'indeed'], default='naukri')
    parser.add_argument('--pages', type=int, help='Number of search pages to crawl.', default=1)
    parser.add_argument('--resume', help='Path to resume file (PDF or text) for SBERT scoring.')
    parser.add_argument('--top', type=int, default=5, help='Number of top jobs to keep in the shortlist.')
    parser.add_argument('--out', default='output/shortlist.json', help='Output path for the shortlist JSON.')
    parser.add_argument('--jobs-json', default='output/job_listings.json', help='Path to save or read fetched jobs JSON.')
    parser.add_argument('--fetch-only', action='store_true', help='Only fetch jobs, do not score.')
    parser.add_argument('--score-only', action='store_true', help='Only score jobs from an existing jobs JSON file.')
    args = parser.parse_args()

    run_pipeline(
        query=args.query,
        location=args.location,
        source=args.source,
        pages=args.pages,
        resume_path=args.resume,
        top=args.top,
        shortlist_out=args.out,
        jobs_json=args.jobs_json,
        fetch_only=args.fetch_only,
        score_only=args.score_only,
    )

from typing import List, Dict
import json
import os
import pdfplumber
from sentence_transformers import SentenceTransformer, util


def load_resume_text(path: str) -> str:
    path = os.path.expanduser(path)
    if path.lower().endswith('.pdf'):
        with pdfplumber.open(path) as pdf:
            pages = [page.extract_text() or '' for page in pdf.pages]
        return '\n'.join(pages)

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _make_text_for_job(job: Dict) -> str:
    parts = []
    for key in ("title", "company", "skills", "description"):
        v = job.get(key)
        if v:
            parts.append(str(v))
    return " \n ".join(parts)


def score_jobs_with_resume(resume_text: str, jobs: List[Dict], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[Dict]:
    """Return jobs annotated with 'score' (cosine similarity to resume).

    The function embeds the resume and job texts and computes cosine similarity.
    """
    model = SentenceTransformer(model_name)
    resume_emb = model.encode(resume_text, convert_to_tensor=True)

    job_texts = [_make_text_for_job(job) for job in jobs]
    job_embs = model.encode(job_texts, convert_to_tensor=True)

    similarities = util.cos_sim(resume_emb, job_embs)[0]

    scored = []
    for job, sim in zip(jobs, similarities):
        job_copy = dict(job)
        job_copy["score"] = float(sim.item())
        scored.append(job_copy)

    scored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return scored


def save_shortlist(scored_jobs: List[Dict], out_json: str = "output/shortlist.json", top_n: int = 5) -> None:
    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    top = scored_jobs[:top_n]
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(top, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Score jobs against a resume using SBERT.")
    parser.add_argument("--resume", required=True, help="Path to resume text file or PDF.")
    parser.add_argument("--jobs", required=False, default="output/job_listings.json", help="Path to jobs JSON produced by job_fetcher (output/job_listings.json)")
    parser.add_argument("--top", type=int, default=5, help="Number of top jobs to save")
    parser.add_argument("--out", default="output/shortlist.json", help="Output JSON path for shortlist")
    args = parser.parse_args()

    resume_text = load_resume_text(args.resume)
    with open(args.jobs, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    scored = score_jobs_with_resume(resume_text, jobs)
    save_shortlist(scored, args.out, args.top)
    print(f"Saved top {args.top} jobs to {args.out}")

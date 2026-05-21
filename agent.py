from dataclasses import dataclass
import json
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore
from langchain.tools import tool
from job_fetcher import fetch_and_save
from sbert_matcher import load_resume_text, score_jobs_with_resume, save_shortlist

load_dotenv()

deepseek_key = os.getenv("DEEPSEEK_API_KEY")

deepseek_model = None
agent = None

try:
    if deepseek_key:
        deepseek_model = init_chat_model(
        model="deepseek-v4-flash",
        model_provider="deepseek", # explicit provider routing
        api_key=deepseek_key,
        model_kwargs={
            # Passes directly to the raw request payload
            "extra_body": {
                "thinking": {
                    "type": "disabled"
                }
            }
        }
    )
except Exception as exc:
    print("Deepseek init failed, falling back to local mode:", exc)
    deepseek_model = None

@dataclass
class Context:
    """Agent context schema for job fetch and SBERT scoring."""


@tool
def fetch_jobs(query: str, location: str = "New Delhi", source: str = "naukri", pages: int = 1) -> dict:
    """Fetch jobs from Naukri or Indeed and save them locally."""
    jobs = fetch_and_save(query, location, source, pages)
    return {
        "job_count": len(jobs),
        "jobs_json": os.path.abspath("output/job_listings.json"),
        "jobs_csv": os.path.abspath("output/job_listings.csv"),
    }


@tool
def score_jobs(resume_path: str, jobs_json: str = "output/job_listings.json", top: int = 5) -> dict:
    """Score fetched jobs against a resume and save a shortlist JSON."""
    resume_text = load_resume_text(resume_path)
    with open(jobs_json, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    if not jobs:
        return {"error": f"No jobs found in {jobs_json}."}

    scored = score_jobs_with_resume(resume_text, jobs)
    shortlist_path = os.path.abspath("output/shortlist.json")
    save_shortlist(scored, shortlist_path, top)

    top_jobs = [
        {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "score": job.get("score", 0.0),
        }
        for job in scored[:top]
    ]
    return {
        "shortlist_json": shortlist_path,
        "top_jobs": top_jobs,
        "total_jobs_scored": len(scored),
    }


agent = None
if deepseek_model is not None:
    agent = create_agent(
        model=deepseek_model,
        tools=[fetch_jobs, score_jobs],
        context_schema=Context,
        store=InMemoryStore(),
    )


def run_local_mode() -> None:
    print("Local mode active. No API_KEY found.")
    print("This will run fetch and score using local Python code only.")

    while True:
        print("\nChoose an action:")
        print("1. Fetch jobs")
        print("2. Score jobs")
        print("3. Fetch jobs and score")
        print("4. Exit")
        choice = input("> ").strip()

        if choice == "4" or choice.lower() in {"exit", "quit"}:
            print("Exiting local mode.")
            break
        if choice == "1":
            query = input("Query: ").strip()
            location = input("Location (optional): ").strip() or "New Delhi"
            source = input("Source (naukri/indeed) [naukri]: ").strip() or "naukri"
            pages = input("Pages [1]: ").strip() or "1"
            try:
                pages = int(pages)
            except ValueError:
                pages = 1
            result = fetch_jobs(query, location, source, pages)
            print(f"Fetched {result['job_count']} jobs.")
            print(f"Jobs saved to: {result['jobs_json']}")
        elif choice == "2":
            resume_path = input("Resume path: ").strip()
            jobs_json = input("Jobs JSON path [output/job_listings.json]: ").strip() or "output/job_listings.json"
            top = input("Top jobs to save [5]: ").strip() or "5"
            try:
                top = int(top)
            except ValueError:
                top = 5
            result = score_jobs(resume_path, jobs_json, top)
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(f"Saved shortlist to: {result['shortlist_json']}")
                for idx, job in enumerate(result["top_jobs"], start=1):
                    print(f"{idx}. {job['title']} at {job['company']} (score {job['score']:.4f})")
        elif choice == "3":
            query = input("Query: ").strip()
            location = input("Location (optional): ").strip() or "New Delhi"
            source = input("Source (naukri/indeed) [naukri]: ").strip() or "naukri"
            pages = input("Pages [1]: ").strip() or "1"
            try:
                pages = int(pages)
            except ValueError:
                pages = 1
            resume_path = input("Resume path: ").strip()
            jobs_json = "output/job_listings.json"
            result = fetch_jobs(query, location, source, pages)
            print(f"Fetched {result['job_count']} jobs.")
            score_result = score_jobs(resume_path, jobs_json, 5)
            if score_result.get("error"):
                print(f"Error: {score_result['error']}")
            else:
                print(f"Saved shortlist to: {score_result['shortlist_json']}")
                for idx, job in enumerate(score_result["top_jobs"], start=1):
                    print(f"{idx}. {job['title']} at {job['company']} (score {job['score']:.4f})")
        else:
            print("Invalid choice, please enter 1, 2, 3, or 4.")


def main() -> None:
    if agent is None:
        run_local_mode()
        return

    print("Agent ready. Type 'exit' or 'quit' to stop.")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Stopping agent.")
            break
        if not user_input:
            continue

        try:
            response = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        except Exception as exc:
            print(f"Agent error: {exc}")
            continue

        messages = response.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = getattr(last_message, "content", last_message)
            print(f"\nAgent: {content}")
        else:
            print("\nAgent: No response returned.")


if __name__ == "__main__":
    main()

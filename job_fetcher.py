import json
import re
from time import sleep
from typing import Dict, List, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from botasaurus.browser import browser, Driver
import pdfplumber
from sbert_matcher import score_jobs_with_resume, save_shortlist

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWe"
    "bKit/537.36"
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
}


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _get_html(url: str) -> str:
    session = _make_session()
    response = session.get(url, timeout=15)
    response.raise_for_status()
    return response.text


def _build_search_url(query: str, location: Optional[str], source: str, page: int) -> str:
    params = {"q": query} if source == "indeed" else {"k": query}
    if location:
        key = "l" if source == "indeed" else "l"
        params[key] = location
    if page > 0:
        params["start" if source == "indeed" else "pageno"] = page * 10 if source == "indeed" else page + 1

    if source == "indeed":
        return f"https://in.indeed.com/jobs?{urlencode(params)}"
    return f"https://www.naukri.com/jobs?{urlencode(params)}"


@browser(headless=True)
def browser_fetch_search_links(driver: Driver, data: Dict) -> List[str]:
    driver.get(data["url"])

    if "naukri.com" in data["url"]:
        links = driver.get_all_links("a[href*='/job-listings-']", url_contains_text="/job-listings-")
    else:
        links = driver.get_all_links("a[href*='clk?jk=']", url_contains_text="clk?jk=")

    # Keep unique URLs in display order
    seen = set()
    filtered = []
    for href in links:
        if href not in seen:
            seen.add(href)
            filtered.append(href)
    return filtered


@browser(headless=True)
def browser_fetch_job_details(driver: Driver, data: Dict) -> Dict:
    driver.get(data["url"])
    sleep(2)
    details = {
        "title": "",
        "company": "",
        "location": "",
        "description": "",
        "skills": "",
        "salary": "",
        "employmentType": "",
        "datePosted": "",
        "source_url": data["url"],
    }
    selectors = {
        "title": ["h1", "h1.job-title", "h1.heading"],
        "company": [".company", ".companyName", ".topcard-org-name"],
        "location": [".location", ".companyLocation", ".topcard__flavor--bullet"],

        "description": [
            "div.job-description", ".jobDescriptionText", "#jobDescriptionText",
            ".description", "div#jobDescriptionText", ".job-snippet",
        ],
    }

    for key, selectors_list in selectors.items():
        for selector in selectors_list:
            try:
                details[key] = driver.get_text(selector)
                if details[key].strip():
                    break
            except Exception:
                continue

    html = driver.page_html
    jsonld = _parse_jsonld_job_posting(html)
    schema_data = _extract_job_schema_fields(jsonld)
    for key, value in schema_data.items():
        if value and not details.get(key):
            details[key] = value

    skills_list = []
    if jsonld:
        skills_list.extend(_extract_skills_from_jsonld(jsonld))
    if not skills_list and details["description"]:
        skills_list.extend(_extract_skills_from_description(details["description"]))
    if not skills_list:
        skills_list.extend(_extract_skills_from_description(_plain_text_from_html(html)))

    details["skills"] = ", ".join(dict.fromkeys([_clean_text(skill) for skill in skills_list if skill]))
    return details


def _clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _plain_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(separator="\n")).strip()


def _parse_jsonld_job_posting(html: str) -> Optional[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        content = script.string
        if not content:
            continue
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue

        items = []
        if isinstance(data, list):
            items.extend(data)
        elif isinstance(data, dict):
            items.append(data)
            graph = data.get("@graph")
            if isinstance(graph, list):
                items.extend(graph)

        for item in items:
            if isinstance(item, dict) and item.get("@type", "").lower() == "jobposting":
                return item
    return None


def _extract_skills_from_jsonld(jsonld: Optional[Dict]) -> List[str]:
    if not jsonld:
        return []
    skills = jsonld.get("skills") or jsonld.get("skill") or []
    if isinstance(skills, str):
        skills = [skills]
    if isinstance(skills, list):
        extracted = []
        for item in skills:
            if isinstance(item, str) and item.strip():
                extracted.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("name") or item.get("@value")
                if isinstance(text, str) and text.strip():
                    extracted.append(text.strip())
        return extracted
    return []


def _extract_skills_from_description(description: str) -> List[str]:
    if not description:
        return []
    description = description.replace("\u2022", "\n").replace("•", "\n")
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    skills = []
    for line in lines:
        match = re.search(
            r"\b(?:skills|skill set|technical skills|required skills|preferred skills|technologies|tools|frameworks)\b[:\-\s]*(.+)$",
            line,
            flags=re.I,
        )
        if match:
            parts = re.split(r"[;,•\u2022]| and | or ", match.group(1))
            for part in parts:
                part = part.strip()
                if part:
                    skills.append(part)

    if not skills:
        for line in lines:
            if re.search(
                r"\b(Python|SQL|Java|AWS|Docker|TensorFlow|PyTorch|React|Node\.js|Machine Learning|Deep Learning|NLP|Kubernetes|Spark|Hadoop)\b",
                line,
                flags=re.I,
            ):
                skills.append(line)
    return list(dict.fromkeys(skills))


def _extract_job_schema_fields(jsonld: Optional[Dict]) -> Dict[str, str]:
    result = {}
    if not jsonld:
        return result
    if not result.get("title"):
        result["title"] = _clean_text(jsonld.get("title", ""))
    org = jsonld.get("hiringOrganization")
    if isinstance(org, dict):
        result["company"] = _clean_text(org.get("name", ""))
    location_data = jsonld.get("jobLocation")
    if isinstance(location_data, dict):
        address = location_data.get("address")
        if isinstance(address, dict):
            locality = address.get("addressLocality")
            region = address.get("addressRegion")
            country = address.get("addressCountry")
            if isinstance(locality, list):
                result["location"] = ", ".join([_clean_text(str(x)) for x in locality if x])
            elif locality:
                result["location"] = _clean_text(str(locality))
            elif region:
                result["location"] = _clean_text(str(region))
            elif country:
                result["location"] = _clean_text(str(country))
    if not result.get("description"):
        result["description"] = _clean_text(jsonld.get("description", ""))
    salary = jsonld.get("baseSalary")
    if isinstance(salary, dict):
        value = salary.get("value")
        if isinstance(value, dict):
            result["salary"] = _clean_text(value.get("value", ""))
        else:
            result["salary"] = _clean_text(str(value or ""))
    result["employmentType"] = _clean_text(jsonld.get("employmentType", ""))
    result["datePosted"] = _clean_text(jsonld.get("datePosted", ""))
    return result


def _fetch_job_links(query: str, location: Optional[str], source: str, pages: int) -> List[str]:
    links = []
    for page in range(pages):
        url = _build_search_url(query, location, source, page)
        try:
            page_links = browser_fetch_search_links({"url": url})
        except Exception as exc:
            print(f"Browser search failed for {source}: {exc}")
            break
        links.extend(page_links)
        sleep(1)
    return links


def fetch_naukri_jobs(query: str, location: Optional[str] = None, pages: int = 1) -> List[Dict]:
    """Fetch job listings from Naukri search results."""
    jobs = []
    links = _fetch_job_links(query, location, "naukri", pages)
    for link in links[:20]:
        try:
            details = browser_fetch_job_details({"url": link})
            details["source"] = "naukri"
            jobs.append(details)
            sleep(1)
        except Exception as exc:
            print(f"Failed to scrape Naukri job page {link}: {exc}")
    return jobs


def fetch_indeed_jobs(query: str, location: Optional[str] = None, pages: int = 1) -> List[Dict]:
    """Fetch job listings from Indeed search results."""
    jobs = []
    links = _fetch_job_links(query, location, "indeed", pages)
    for link in links[:20]:
        try:
            details = browser_fetch_job_details({"url": link})
            details["source"] = "indeed"
            jobs.append(details)
            sleep(1)
        except Exception as exc:
            print(f"Failed to scrape Indeed job page {link}: {exc}")
    return jobs


def save_jobs_to_json(jobs: List[Dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def save_jobs_to_csv(jobs: List[Dict], path: str) -> None:
    import csv

    if not jobs:
        return

    keys = jobs[0].keys()
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(jobs)


def fetch_and_save(query: str, location: Optional[str] = None, source: str = "naukri", pages: int = 1) -> List[Dict]:
    if source == "naukri":
        jobs = fetch_naukri_jobs(query, location, pages)
    elif source == "indeed":
        jobs = fetch_indeed_jobs(query, location, pages)
    else:
        raise ValueError("Source must be 'naukri' or 'indeed'.")

    save_jobs_to_json(jobs, "output/job_listings.json")
    save_jobs_to_csv(jobs, "output/job_listings.csv")
    return jobs


if __name__ == '__main__':
    import argparse


    parser = argparse.ArgumentParser(description="Fetch job listings from Naukri or Indeed.")
    parser.add_argument("query", help="Job search query, e.g. 'data scientist'.")
    parser.add_argument("--location", help="City or location.", default='New Delhi')
    parser.add_argument("--source", help="Source: naukri or indeed.", choices=["naukri", "indeed"], default="naukri")
    parser.add_argument("--pages", type=int, help="Number of search pages to crawl.", default=1)
    parser.add_argument("--page", type=int, dest="pages", help="Alias for --pages.")
    parser.add_argument("--shortlist", action="store_true", help="Run SBERT scoring and save a shortlist")
    parser.add_argument("--resume", help="Path to resume (plain text or PDF) used for scoring")
    parser.add_argument("--top", type=int, default=5, help="Number of top jobs to keep when shortlisting")
    parser.add_argument("--out", default="output/shortlist.json", help="Output path for shortlist JSON")
    args = parser.parse_args()

    jobs = fetch_and_save(args.query, args.location, args.source, args.pages)
    print(f"Fetched {len(jobs)} jobs from {args.source}. Saved to output/job_listings.json and output/job_listings.csv.")
    print("It might be take around 20-25 minutes to complete his work")
    if args.shortlist:
        if not args.resume:
            print("--shortlist requested but no --resume provided. Skipping scoring.")
        else:
            resume_text = ""
            try:
                if args.resume.lower().endswith('.pdf'):
                    with pdfplumber.open(args.resume) as pdf:
                        pages = [p.extract_text() or "" for p in pdf.pages]
                        resume_text = "\n".join(pages)
                else:
                    with open(args.resume, 'r', encoding='utf-8') as f:
                        resume_text = f.read()
            except Exception as e:
                print(f"Failed to read resume {args.resume}: {e}")
                resume_text = ""

            if resume_text:
                scored = score_jobs_with_resume(resume_text, jobs)
                save_shortlist(scored, args.out, args.top)
                print(f"Saved top {args.top} shortlist to {args.out}")
            else:
                print("Empty resume text; skipping scoring.")

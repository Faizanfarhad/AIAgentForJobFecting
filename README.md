# AI Job Fetcher

## Status :- In Progress 

This project contains a simple job-fetch automation helper for Naukri and Indeed search results.

## New helper

- `job_fetcher.py` — fetches job listings from Naukri or Indeed and saves results to `output/job_listings.json` and `output/job_listings.csv`.

## Install dependencies

```bash
pip install -r requirments.txt
```

## Run

```bash
python job_fetcher.py "data scientist" --location "Bangalore" --source naukri --pages 1
```

or

```bash
python job_fetcher.py "software intern" --location "Mumbai" --source indeed --pages 1
```

## Pipeline runner

Use `pipeline_runner.py` to fetch jobs first and then run SBERT scoring on the same results.

```bash
python pipeline_runner.py "machine learning" --location "Delhi" --source naukri --pages 1 --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

If you want to fetch only, use:

```bash
python pipeline_runner.py "machine learning" --location "Delhi" --source naukri --pages 1 --fetch-only
```

If you already have `output/job_listings.json` and want to score without fetching again:

```bash
python pipeline_runner.py "machine learning" --score-only --jobs-json output/job_listings.json --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

## Notes

- This is a basic scraping helper, not an official API client.
- Use it responsibly and respect each site’s terms of service.
- If you want, I can next wire this into your existing `agent.py` workflow and add role matching.

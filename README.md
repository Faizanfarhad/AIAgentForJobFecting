# AI Job Fetcher

A simple Python project to fetch job listings from Naukri or Indeed and score them against a resume.

## Why this project

This repository helps you:

- scrape job postings from Naukri or Indeed search results
- save job listings to JSON and CSV files
- rank job postings by how well they match your resume using SBERT
- run a local menu-driven assistant with `agent.py`

## Requirements

- Python 3.8 or newer
- `pip`
- Internet access for scraping and model downloads

## Install dependencies

```bash
pip install -r requirments.txt
```

> Use the existing `requirments.txt` file in the repository.

## How to use this project

### 1. Fetch job listings only

Run `job_fetcher.py` with your search query, location, and source.

```bash
python job_fetcher.py "data scientist" --location "Bangalore" --source naukri --pages 1
```

Example for Indeed:

```bash
python job_fetcher.py "software intern" --location "Mumbai" --source indeed --pages 1
```

This saves jobs to:

- `output/job_listings.json`
- `output/job_listings.csv`

### 2. Fetch jobs and score them with your resume

Use `pipeline_runner.py` to run both fetching and scoring in one command.

```bash
python pipeline_runner.py "machine learning" --location "Delhi" --source naukri --pages 1 --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

What this does:

1. fetches jobs from Naukri or Indeed
2. loads your resume from a PDF or text file
3. computes SBERT similarity between resume and jobs
4. saves the top matching jobs to `output/shortlist.json`

### 3. Fetch jobs only with pipeline_runner

If you already want to fetch jobs but not score them yet:

```bash
python pipeline_runner.py "machine learning" --location "Delhi" --source naukri --pages 1 --fetch-only
```

### 4. Score existing job results only

When you already have `output/job_listings.json`, score those jobs directly with this command:

```bash
python pipeline_runner.py --score-only --jobs-json output/job_listings.json --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

### 5. Run the local interactive agent

Start `agent.py` if you want a simple menu-driven flow:

```bash
python agent.py
```

Then choose one of the options:

- fetch jobs
- score jobs
- fetch jobs and score
- exit

If you set `DEEPSEEK_API_KEY` in your environment, `agent.py` will try to use Deepseek. Otherwise it will run locally.

## Output files

- `output/job_listings.json`: raw fetched job listings
- `output/job_listings.csv`: raw job listings in spreadsheet format
- `output/shortlist.json`: top scored job matches

## Tips for success

- Use a clear query like `"backend developer"` or `"data scientist"`.
- Set the location using `--location` when you want results for a city or region.
- Choose either `--source naukri` or `--source indeed`.
- `--pages 1` is a good starting point; higher values gather more jobs but take longer.
- Provide a valid resume path to get shortlist results.

## Important notes

- This is a scraping tool, not an official API client.
- Use it responsibly and follow the terms of service for Naukri and Indeed.
- The first SBERT run may download a model and take extra time.

## Troubleshooting

- If a command fails, check that the resume path is correct.
- Make sure `output/job_listings.json` exists before using `--score-only`.
- Ensure the `output/` folder is writable.
- Confirm Python is installed with `python --version`.

## Example workflow

1. Fetch jobs:

```bash
python job_fetcher.py "frontend developer" --location "Bangalore" --source naukri --pages 1
```

2. Score jobs:

```bash
python pipeline_runner.py --score-only --jobs-json output/job_listings.json --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

3. Review `output/shortlist.json` to see the best matches.

# AI Job Fetcher

A simple Python tool to fetch job listings from Naukri or Indeed and optionally score them against your resume.

## What this project does

- Scrapes job listings from Naukri or Indeed search results
- Saves job listings to `output/job_listings.json` and `output/job_listings.csv`
- Scores jobs against a resume using SBERT embeddings
- Saves a ranked shortlist to `output/shortlist.json`
- Includes a local interactive mode via `agent.py`

## Requirements

- Python 3.8 or newer
- `pip`
- Internet access for web scraping and model downloads

## Install dependencies

```bash
pip install -r requirments.txt
```

> Note: This repository uses packages such as `botasaurus`, `pdfplumber`, `sentence_transformers`, `requests`, `beautifulsoup4`, and `langchain`.

## 1. Fetch job listings

Use `job_fetcher.py` with a search query, optional location, and source.

```bash
python job_fetcher.py "data scientist" --location "Bangalore" --source naukri --pages 1
```

Example for Indeed:

```bash
python job_fetcher.py "software intern" --location "Mumbai" --source indeed --pages 1
```

### Output files

- `output/job_listings.json`
- `output/job_listings.csv`

## 2. Score jobs with a resume

Use `pipeline_runner.py` to fetch jobs and score them in one command.

```bash
python pipeline_runner.py "machine learning" --location "Delhi" --source naukri --pages 1 --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

This command will:

1. Fetch jobs from the selected source
2. Load your resume from the provided file
3. Compute SBERT similarity scores
4. Save the top matching jobs to `output/shortlist.json`

## 3. Fetch only

If you only want to fetch jobs without scoring:

```bash
python pipeline_runner.py "machine learning" --location "Delhi" --source naukri --pages 1 --fetch-only
```

## 4. Score existing results only

If you already have `output/job_listings.json`, score those jobs directly:

```bash
python pipeline_runner.py --score-only --jobs-json output/job_listings.json --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

## 5. Use local interactive mode

Run `agent.py` for a simple menu-driven interface:

```bash
python agent.py
```

Then choose one of the options:

- Fetch jobs
- Score jobs
- Fetch jobs and score
- Exit

If `DEEPSEEK_API_KEY` is set in your environment, `agent.py` will attempt to use the Deepseek model. Otherwise it runs locally.

## Helpful tips

- Use a clear query such as `"data scientist"` or `"machine learning engineer"`.
- Use `--location` for the city or region you want.
- Use `--source naukri` or `--source indeed`.
- Increase `--pages` if you want more results, but note that scraping takes longer.
- Provide `--resume path/to/resume.pdf` to generate a shortlist.

## Important notes

- This project scrapes websites, not official APIs.
- Use the tool responsibly and follow each site’s terms of service.
- The first scoring run may download the sentence-transformers model, which can take extra time.

## Troubleshooting

- Confirm the resume path is correct.
- Confirm `output/job_listings.json` exists before using `--score-only`.
- Make sure `output/` is writable.
- Verify Python and pip are installed with `python --version` and `pip --version`.

## Example workflow

1. Fetch jobs:

```bash
python job_fetcher.py "frontend developer" --location "Bangalore" --source naukri --pages 1
```

2. Score jobs:

```bash
python pipeline_runner.py --score-only --jobs-json output/job_listings.json --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

3. Open `output/shortlist.json` to see the top matching jobs.

# AI Job Fetcher

A simple Python tool for fetching job listings from Naukri or Indeed and ranking them against your resume.

## What this project does

- Fetches job listings from Naukri or Indeed search results.
- Saves raw job listings to `output/job_listings.json` and `output/job_listings.csv`.
- Scores how well each job matches your resume using SBERT embeddings.
- Saves the top job matches to `output/shortlist.json`.
- Supports a local menu-driven mode with `agent.py`.

## Requirements

- Python 3.8 or newer
- `pip`
- Internet access for scraping and model downloads

## Install dependencies

```bash
pip install -r requirments.txt
```

> Note: The dependency file is named `requirments.txt` in this repository.

## Getting started

### 1. Fetch job listings only
> Note: Before running this commands create an .env file and store your API inside it and go to agent.py(14 line) and replace the "DEEPSEEK_API_KEY" with your variable name

Run `job_fetcher.py` with a search query, location, source, and page count.

```bash
python job_fetcher.py "data scientist" --location "Bangalore" --source naukri --pages 1
```

Example for Indeed:

```bash
python job_fetcher.py "software intern" --location "Mumbai" --source indeed --pages 1
```

This creates:

- `output/job_listings.json`
- `output/job_listings.csv`

### 2. Fetch jobs and score them using your resume

Use `pipeline_runner.py` to fetch jobs and score them in one command.

```bash
python pipeline_runner.py "machine learning" --location "Delhi" --source naukri --pages 1 --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

This command will:

1. fetch jobs from the selected source
2. load your resume from a PDF or plain text file
3. compute SBERT similarity between the resume and job postings
4. save the top matching jobs to `output/shortlist.json`

### 3. Fetch jobs only with `pipeline_runner.py`

If you want to fetch jobs without scoring them yet:

```bash
python pipeline_runner.py "machine learning" --location "Delhi" --source naukri --pages 1 --fetch-only
```

### 4. Score an existing job list only

If you already have `output/job_listings.json`, score it directly:

```bash
python pipeline_runner.py --score-only --jobs-json output/job_listings.json --resume path/to/resume.pdf --top 5 --out output/shortlist.json
```

### 5. Use the local interactive agent

Run `agent.py` for a simple text menu:

```bash
python agent.py
```

Then choose one of the options:

- fetch jobs
- score jobs
- fetch jobs and score
- exit

If `DEEPSEEK_API_KEY` is set in your environment, `agent.py` will attempt to use the Deepseek model. Otherwise it runs in local mode.

## Output files

- `output/job_listings.json`: raw fetched job listings
- `output/job_listings.csv`: the same job listings in CSV format
- `output/shortlist.json`: top-ranked job matches after scoring

## Tips for best results

- Use specific queries such as `"backend developer"` or `"data scientist"`.
- Use `--location` to focus on a particular city or region.
- Use `--source naukri` or `--source indeed`.
- Start with `--pages 1` and increase gradually if you want more results.
- Provide a valid resume file path to generate a shortlist.

## Important notes

- This tool scrapes websites; it is not an official API client.
- Use it responsibly and follow each site’s terms of service.
- The first SBERT scoring run may download the model and take extra time.

## Troubleshooting

- If a command fails, verify the resume path and file type.
- Make sure `output/job_listings.json` exists before using `--score-only`.
- Ensure the `output/` directory is writable.
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

3. Open `output/shortlist.json` to review the best matches.

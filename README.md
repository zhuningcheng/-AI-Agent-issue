# collect_data

GitHub Issues data collection tool for crawling specified repositories and saving Issue data in JSONL format.

## Features

- Incremental crawling of GitHub Issues (based on `since` parameter)
- Automatic filtering of Pull Requests
- Collects Issue details, comments, and reaction data
- Data validation and deduplication

## File Description

| File | Description |
|------|-------------|
| `github_client.py` | GitHub API client (Token authentication, pagination) |
| `utils.py` | Common utility functions (data fetching, storage, metadata management) |
| `crawler_openclaw.py` | OpenClaw repository crawler entry point |
| `crawler_hermers.py` | Hermes-agent repository crawler entry point |
| `validate_data.py` | Data validation and deduplication tool |
| `repair_openclaw.py` | OpenClaw data repair script |
| `repair_hermers.py` | Hermes data repair script |
| `data/*.jsonl` | Crawled data files (managed by Git LFS) |
| `metadata/*.json` | Crawler metadata (last crawl timestamp) |

## Usage

### 1. Configure Environment Variables

```bash
# Set in .env file
GITHUB_TOKEN=your_token
```

### 2. Run Crawlers

```bash
# Crawl OpenClaw repository
python crawler_openclaw.py

# Crawl Hermes-agent repository
python crawler_hermers.py
```

### 3. Data Validation

```bash
# Validate all JSONL files under data/
python validate_data.py

# Validate a specific file
python validate_data.py data/hermes.jsonl

# Clean duplicate data (preview mode)
python validate_data.py --clean data/hermes.jsonl

# Clean duplicate data (write to file)
python validate_data.py --clean --write data/hermes.jsonl
```

## Data Format

Each record contains:

- `repo` — Repository name
- `issue_id` — GitHub Issue unique ID
- `issue_number` — Issue number
- `title` / `body` — Title and body text
- `state` — Status (open/closed)
- `author` — Author username
- `created_at` / `updated_at` / `closed_at` — Timestamps
- `labels` — List of labels
- `reactions` — Reaction statistics
- `comments` — List of comments (author, timestamp, content)

## Validation Rules

The validation tool checks the following:

- Duplicate `issue_id`
- Duplicate `issue_number` within the same repo
- Missing required fields
- Valid JSON format
- Exclusion of non-Issue data such as PRs, Discussions, and Commits

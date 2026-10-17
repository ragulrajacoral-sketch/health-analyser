# GitHub Repository Health Analyzer

A Flask web app that fetches public repository data from GitHub's REST API and displays a transparent, heuristic health score.

## Features
- Accepts `owner/repo` or a public GitHub repository URL
- Shows stars, forks, watchers, open issues, branch, dates, archive status, and license
- Displays language data and a sample of recent commits
- Explains score deductions and handles common API/network errors

> The score is an educational heuristic, not an official GitHub rating or a complete code-quality/security assessment. Unauthenticated GitHub API rate limits apply.

## Requirements
- Python 3.10+
- Internet connection

## Run on Windows
```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 and try `psf/requests` or another public repository.

## Score logic
The score starts at 100 and applies simple deductions for archived status, stale push activity, many open issues, no stars, missing language data, or an empty recent-commit sample. Edit `calculate_health()` in `app.py` to customize the thresholds.

## Structure
```text
github-repository-health-analyzer/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── templates/index.html
└── static/style.css
```

## Safety
No GitHub token is required for public repositories. Never commit tokens, passwords, `.env` files, or virtual environments.

## Future improvements
- Optional GitHub token support
- Health snapshots over time
- Automated tests and code-quality checks
- Release and issue-response-time analysis
- PDF report export

## License
MIT. See `LICENSE`.

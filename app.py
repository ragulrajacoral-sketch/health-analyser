from datetime import datetime, timezone
import requests
from flask import Flask, render_template, request

app = Flask(__name__)
GITHUB_API = "https://api.github.com"
TIMEOUT_SECONDS = 12


def github_get(path):
    response = requests.get(
        f"{GITHUB_API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-Repository-Health-Analyzer",
        },
        timeout=TIMEOUT_SECONDS,
    )
    if response.status_code == 404:
        raise ValueError("Repository not found, or it is private. Enter a public repository URL.")
    if response.status_code == 403:
        raise ValueError("GitHub API rate limit or access restriction reached. Try again later.")
    response.raise_for_status()
    return response.json()


def parse_repo_input(value):
    value = (value or "").strip().rstrip("/").removesuffix(".git")
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    parts = [part for part in value.split("/") if part]
    if len(parts) != 2 or any(part in {".", ".."} for part in parts):
        raise ValueError("Enter owner/repo or https://github.com/owner/repo.")
    owner, repo = parts
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    if any(ch not in allowed for ch in owner + repo):
        raise ValueError("The repository name contains unsupported characters.")
    return owner, repo


def calculate_health(repo, languages, commits):
    """A transparent educational heuristic, not an official GitHub rating."""
    score, reasons = 100, []
    if repo.get("archived"):
        score -= 30
        reasons.append("Repository is archived.")
    else:
        reasons.append("Repository is not archived.")

    pushed_at = repo.get("pushed_at")
    days_since_push = None
    if pushed_at:
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        days_since_push = max(0, (datetime.now(timezone.utc) - pushed).days)
        if days_since_push > 365:
            score -= 25
            reasons.append(f"No push in {days_since_push} days; activity may be stale.")
        elif days_since_push > 180:
            score -= 15
            reasons.append(f"Last push was {days_since_push} days ago.")
        elif days_since_push > 90:
            score -= 8
            reasons.append(f"Last push was {days_since_push} days ago.")
        else:
            reasons.append("Recent push activity detected.")
    else:
        score -= 10
        reasons.append("No push date is available.")

    open_issues = repo.get("open_issues_count", 0)
    if open_issues > 100:
        score -= 15
        reasons.append("Large number of open issues; triage may be needed.")
    elif open_issues > 30:
        score -= 8
        reasons.append("Moderate-to-high open issue count.")
    else:
        reasons.append("Open issue count is relatively low.")

    if repo.get("stargazers_count", 0) == 0:
        score -= 5
        reasons.append("No stars yet; this is not necessarily a quality problem.")
    if not languages:
        score -= 5
        reasons.append("GitHub did not report language data.")
    if commits is not None:
        if not commits:
            score -= 10
            reasons.append("No commits found in the recent-commit sample.")
        else:
            reasons.append(f"Found {len(commits)} recent commit(s) in the sample.")
    else:
        reasons.append("Recent commit data could not be loaded.")

    score = max(0, min(100, score))
    label = "Healthy" if score >= 80 else "Needs attention" if score >= 60 else "At risk"
    return {"score": score, "label": label, "reasons": reasons, "days_since_push": days_since_push}


@app.route("/", methods=["GET", "POST"])
def index():
    result, error = None, None
    repo_input = ""
    if request.method == "POST":
        repo_input = request.form.get("repository", "")
        try:
            owner, repo_name = parse_repo_input(repo_input)
            repo = github_get(f"/repos/{owner}/{repo_name}")
            languages = github_get(f"/repos/{owner}/{repo_name}/languages")
            try:
                commits = github_get(f"/repos/{owner}/{repo_name}/commits?per_page=10")
                if not isinstance(commits, list):
                    commits = None
            except (requests.RequestException, ValueError):
                commits = None
            result = {
                "name": repo.get("full_name", f"{owner}/{repo_name}"),
                "description": repo.get("description") or "No description provided.",
                "url": repo.get("html_url", f"https://github.com/{owner}/{repo_name}"),
                "owner": (repo.get("owner") or {}).get("login", owner),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
                "watchers": repo.get("subscribers_count", 0),
                "default_branch": repo.get("default_branch", "Unknown"),
                "created_at": (repo.get("created_at") or "")[:10] or "Unknown",
                "updated_at": (repo.get("updated_at") or "")[:10] or "Unknown",
                "pushed_at": (repo.get("pushed_at") or "")[:10] or "Unknown",
                "archived": repo.get("archived", False),
                "license": (repo.get("license") or {}).get("spdx_id", "Not specified"),
                "languages": sorted(languages.items(), key=lambda item: item[1], reverse=True),
                "health": calculate_health(repo, languages, commits),
                "commit_count": len(commits) if commits is not None else None,
            }
        except ValueError as exc:
            error = str(exc)
        except requests.Timeout:
            error = "GitHub took too long to respond. Please try again."
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            error = f"GitHub API request failed (HTTP {status}). Please try again later."
        except requests.RequestException:
            error = "Could not connect to GitHub. Check your internet connection and try again."
    return render_template("index.html", result=result, error=error, repo_input=repo_input)


if __name__ == "__main__":
    app.run(debug=True)

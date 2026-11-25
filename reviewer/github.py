"""Minimal GitHub REST client (stdlib only)."""
from __future__ import annotations

import json
import urllib.request

API = "https://api.github.com"


def _req(method: str, url: str, token: str, body: dict | None = None, accept: str = "application/vnd.github+json"):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "ai-pr-review-agent"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def get_pr_diff(repo: str, pr: int, token: str) -> str:
    return _req("GET", f"{API}/repos/{repo}/pulls/{pr}", token, accept="application/vnd.github.v3.diff")


def get_pr_title(repo: str, pr: int, token: str) -> str:
    return json.loads(_req("GET", f"{API}/repos/{repo}/pulls/{pr}", token)).get("title", "")


def post_comment(repo: str, pr: int, token: str, body: str) -> None:
    _req("POST", f"{API}/repos/{repo}/issues/{pr}/comments", token, {"body": body})

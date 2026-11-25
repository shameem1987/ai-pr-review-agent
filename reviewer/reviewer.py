from __future__ import annotations

import json
import os
from typing import Callable

from .diff import chunk, filter_files, split_files
from .prompt import SYSTEM, build_user_prompt

SEV_ORDER = {"high": 0, "medium": 1, "low": 2}


def anthropic_llm(model: str | None = None) -> Callable[[str, str], str]:
    import anthropic

    client = anthropic.Anthropic()
    model = model or os.getenv("REVIEW_MODEL", "claude-sonnet-5-5")

    def call(system: str, user: str) -> str:
        resp = client.messages.create(model=model, max_tokens=2000, system=system,
                                      messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    return call


def parse_response(text: str) -> dict:
    """Tolerant JSON extraction; a malformed reply degrades to an empty review, never a crash."""
    try:
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        findings = [f for f in data.get("findings", []) if isinstance(f, dict) and f.get("title")]
        return {"summary": str(data.get("summary", "")), "findings": findings}
    except (ValueError, json.JSONDecodeError):
        return {"summary": "", "findings": []}


def review_diff(diff: str, llm: Callable[[str, str], str], pr_title: str = "",
                max_chars: int = 24_000) -> dict:
    files = filter_files(split_files(diff))
    summaries, findings = [], []
    for batch in chunk(files, max_chars):
        r = parse_response(llm(SYSTEM, build_user_prompt(batch, pr_title)))
        if r["summary"]:
            summaries.append(r["summary"])
        findings.extend(r["findings"])
    findings.sort(key=lambda f: SEV_ORDER.get(f.get("severity", "low"), 3))
    return {"files_reviewed": len(files), "summary": " ".join(summaries), "findings": findings}


def to_markdown(result: dict) -> str:
    icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}
    lines = ["## 🤖 AI Review (advisory)", ""]
    if result["summary"]:
        lines += [result["summary"], ""]
    if not result["findings"]:
        lines.append("No significant issues found. ✅")
    for f in result["findings"]:
        lines.append(f"- {icon.get(f.get('severity'), '⚪')} **{f['title']}** (`{f.get('file', '?')}`): {f.get('detail', '')}")
    lines += ["", f"<sub>{result['files_reviewed']} file(s) reviewed. AI can be wrong; a human reviewer decides.</sub>"]
    return "\n".join(lines)

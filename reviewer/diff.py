"""Split a unified diff into per-file chunks that fit an LLM context budget."""
from __future__ import annotations

import re

DEFAULT_IGNORE = (
    r"(^|/)(package-lock\.json|yarn\.lock|poetry\.lock|pnpm-lock\.yaml)$",
    r"\.(min\.js|map|svg|png|jpg|jpeg|gif|ico|pdf)$",
    r"(^|/)(dist|build|node_modules|vendor)/",
)


def split_files(diff: str) -> list[tuple[str, str]]:
    """Return [(path, file_diff)] from a `git diff` output."""
    parts = re.split(r"(?m)^(?=diff --git )", diff)
    out = []
    for part in parts:
        m = re.match(r"diff --git a/(.+?) b/(.+)", part)
        if m:
            out.append((m.group(2), part))
    return out


def filter_files(files, ignore=DEFAULT_IGNORE):
    return [(p, d) for p, d in files if not any(re.search(rx, p) for rx in ignore)]


def chunk(files: list[tuple[str, str]], max_chars: int = 24_000) -> list[list[tuple[str, str]]]:
    """Group files into batches under max_chars. An oversized single file is truncated, never dropped."""
    batches, cur, size = [], [], 0
    for path, d in files:
        if len(d) > max_chars:
            d = d[:max_chars] + "\n... [truncated: file diff too large] ...\n"
        if cur and size + len(d) > max_chars:
            batches.append(cur)
            cur, size = [], 0
        cur.append((path, d))
        size += len(d)
    if cur:
        batches.append(cur)
    return batches

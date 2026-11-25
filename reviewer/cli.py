"""python -m reviewer.cli --repo owner/name --pr 12 [--dry-run]
   python -m reviewer.cli --diff-file change.diff --dry-run"""
from __future__ import annotations

import argparse
import os
import sys

from . import github
from .reviewer import anthropic_llm, review_diff, to_markdown


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--pr", type=int)
    ap.add_argument("--diff-file")
    ap.add_argument("--dry-run", action="store_true", help="print instead of commenting")
    ap.add_argument("--fail-on-high", action="store_true", help="exit 1 if any high-severity finding")
    a = ap.parse_args(argv)

    token = os.getenv("GITHUB_TOKEN", "")
    title = ""
    if a.diff_file:
        diff = open(a.diff_file).read()
    else:
        if not (a.repo and a.pr and token):
            ap.error("--repo, --pr and GITHUB_TOKEN are required unless --diff-file is used")
        diff, title = github.get_pr_diff(a.repo, a.pr, token), github.get_pr_title(a.repo, a.pr, token)

    result = review_diff(diff, anthropic_llm(), title)
    md = to_markdown(result)
    if a.dry_run or a.diff_file:
        print(md)
    else:
        github.post_comment(a.repo, a.pr, token, md)
    if a.fail_on_high and any(f.get("severity") == "high" for f in result["findings"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

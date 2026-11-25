import json

from reviewer.diff import chunk, filter_files, split_files
from reviewer.reviewer import parse_response, review_diff, to_markdown

DIFF = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
+password = "hunter2"
diff --git a/package-lock.json b/package-lock.json
+++ b/package-lock.json
@@ -1 +1 @@
+{}
diff --git a/util.py b/util.py
+++ b/util.py
@@ -1 +1 @@
+x = 1
"""


def test_split_and_filter():
    files = split_files(DIFF)
    assert [p for p, _ in files] == ["app.py", "package-lock.json", "util.py"]
    assert [p for p, _ in filter_files(files)] == ["app.py", "util.py"]


def test_chunking_never_drops_oversized_file():
    big = [("a.py", "x" * 100), ("b.py", "y" * 5000)]
    batches = chunk(big, max_chars=1000)
    flat = [p for b in batches for p, _ in b]
    assert flat == ["a.py", "b.py"]
    assert "truncated" in batches[-1][-1][1]


def test_parse_response_tolerates_garbage():
    assert parse_response("sorry, no json") == {"summary": "", "findings": []}
    ok = parse_response('Here:\n{"summary":"s","findings":[{"title":"t","severity":"high"}]}')
    assert ok["findings"][0]["title"] == "t"


def test_review_sorts_by_severity_and_renders():
    reply = json.dumps({"summary": "Looks risky.", "findings": [
        {"file": "util.py", "severity": "low", "title": "naming", "detail": "d"},
        {"file": "app.py", "severity": "high", "title": "hardcoded secret", "detail": "use env"}]})
    result = review_diff(DIFF, lambda s, u: reply)
    assert result["findings"][0]["title"] == "hardcoded secret"
    assert result["files_reviewed"] == 2
    md = to_markdown(result)
    assert "🔴" in md and "advisory" in md


def test_clean_review_message():
    result = review_diff(DIFF, lambda s, u: '{"summary":"ok","findings":[]}')
    assert "No significant issues" in to_markdown(result)

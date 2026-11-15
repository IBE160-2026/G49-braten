"""AD-1: apps depend only along the module graph, and only `ai` imports `anthropic`.

An edge A -> B means A may import from B; reachability counts, and every app reaches `core`.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

APPS = ["core", "accounts", "courses", "ai", "ingestion", "studymat", "quiz", "review", "progress", "web"]

GRAPH = {
    "web": {"progress"},
    "progress": {"quiz", "review"},
    "quiz": {"studymat"},
    "review": {"studymat"},
    "studymat": {"ai", "ingestion"},
    "ingestion": {"courses"},
    "courses": {"accounts"},
    "ai": {"accounts"},
    "accounts": {"core"},
    "core": set(),
}

# Third-party modules only one app may import.
RESTRICTED = {"anthropic": "ai"}


def reachable(app: str) -> set[str]:
    seen: set[str] = set()
    stack = list(GRAPH[app])
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(GRAPH[node])
    return seen


def imported_top_levels(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def violations(root: Path) -> list[str]:
    found = []
    for app in APPS:
        app_dir = root / app
        if not app_dir.is_dir():
            continue
        allowed = reachable(app) | {app}
        for path in sorted(app_dir.rglob("*.py")):
            rel = path.relative_to(root)
            for name in imported_top_levels(path):
                if name in GRAPH and name not in allowed:
                    found.append(f"{rel}: {app} -> {name} is not allowed by AD-1")
                if name in RESTRICTED and RESTRICTED[name] != app:
                    found.append(f"{rel}: only {RESTRICTED[name]} may import {name}")
    return found


def test_ad1_every_app_reaches_core():
    for app in APPS:
        if app != "core":
            assert "core" in reachable(app), app


def test_ad1_core_imports_no_app():
    assert reachable("core") == set()


def test_ad1_codebase_follows_the_import_graph():
    assert violations(ROOT) == []


@pytest.mark.parametrize(
    ("app", "source", "expected"),
    [
        ("studymat", "from quiz import x\n", "studymat -> quiz"),
        ("core", "import accounts.models\n", "core -> accounts"),
        ("ai", "from web.views import page\n", "ai -> web"),
        ("quiz", "import anthropic\n", "only ai may import anthropic"),
    ],
)
def test_ad1_a_forbidden_import_fails_naming_the_edge(tmp_path, app, source, expected):
    (tmp_path / app).mkdir()
    (tmp_path / app / "bad.py").write_text(source, encoding="utf-8")
    found = violations(tmp_path)
    assert len(found) == 1
    assert expected in found[0]


@pytest.mark.parametrize(
    ("app", "source"),
    [
        ("web", "from core import time\n"),
        ("quiz", "from studymat.models import Question\n"),
        ("ai", "import anthropic\n"),
        ("studymat", "from . import models\n"),
    ],
)
def test_ad1_allowed_imports_pass(tmp_path, app, source):
    (tmp_path / app).mkdir()
    (tmp_path / app / "ok.py").write_text(source, encoding="utf-8")
    assert violations(tmp_path) == []

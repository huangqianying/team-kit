"""team-check 与钩子共用的检查函数。只读：不改仓库、不落账。

口径与 `skills/team-ledger/team-ledger.py` 一致：账本按 git common-dir 定位到主工作树，
工作项只在主线最新事件为「完成」时算收口。这里按同一规则重写，不 import 账本脚本。
"""
import fnmatch
import json
import os
import re
import subprocess

LANE_RE = re.compile(r"lane/([A-Za-z0-9][A-Za-z0-9._-]*)")
LANE_GENERIC = {"worktree"}                 # 「lane/worktree」这类泛指不算登记
FLYWAY_RE = re.compile(r"^V(\d+)__.*\.sql$")
CONFIG_DOC = "docs/rules/工程配置.md"


def git(repo, *args, timeout=10):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=timeout)


def repo_root(start):
    r = git(start, "rev-parse", "--show-toplevel")
    return r.stdout.strip() if r.returncode == 0 else None


def ledger_dir(repo):
    """与 team-ledger.py 相同：TEAM_LEDGER_DIR 优先，否则主工作树下的 .team-ledger/。"""
    if os.environ.get("TEAM_LEDGER_DIR"):
        return os.environ["TEAM_LEDGER_DIR"]
    r = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return os.path.join(os.path.dirname(r.stdout.strip()), ".team-ledger")


def read_events(led):
    p = os.path.join(led, "ledger.jsonl") if led else None
    if not p or not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def closed_items(events):
    last = {}
    for e in events:
        if e.get("item") and not e.get("part"):
            last[e["item"]] = e
    return {i for i, e in last.items() if e.get("status") == "完成"}


# ─────────── scope ───────────

def commit_exists(repo, sha):
    return git(repo, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def changed_paths(repo, commits):
    paths = set()
    for c in commits:
        r = git(repo, "show", "--name-only", "--format=", c)
        if r.returncode != 0:
            raise ValueError(f"提交不存在或读不了：{c}")
        paths.update(p for p in r.stdout.splitlines() if p.strip())
    return paths


def _match(path, pattern):
    if pattern.endswith("/"):
        return path.startswith(pattern)
    return fnmatch.fnmatch(path, pattern) or path == pattern


def out_of_scope(paths, allow, deny):
    bad = []
    for p in sorted(paths):
        if any(_match(p, d) for d in deny or []):
            bad.append((p, "命中禁写范围"))
        elif not any(_match(p, a) for a in allow or []):
            bad.append((p, "不在可写范围"))
    return bad


# ─────────── migrations ───────────

def migration_dir(repo):
    p = os.path.join(repo, CONFIG_DOC)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("| 数据库迁移 |"):
                m = re.search(r"`([^`]+)`", line)
                return m.group(1) if m else None
    return None


def flyway_dupes(path):
    seen = {}
    for name in sorted(os.listdir(path)):
        m = FLYWAY_RE.match(name)
        if m:
            seen.setdefault(int(m.group(1)), []).append(name)
    return {v: names for v, names in seen.items() if len(names) > 1}


# ─────────── plan ───────────

def plan_missing(text):
    if not re.search(r"^#{1,6}\s.*并行编排", text, re.M):
        return ["并行编排"]
    return [k for k in ("线的划分", "合入顺序") if k not in text]


# ─────────── lanes ───────────

def existing_lanes(repo):
    names = set()
    r = git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/lane/")
    if r.returncode != 0:
        raise ValueError("读不了分支")
    names.update(x[len("lane/"):] for x in r.stdout.split() if x.startswith("lane/"))
    w = git(repo, "worktree", "list", "--porcelain")
    if w.returncode == 0:
        for line in w.stdout.splitlines():
            if line.startswith("branch refs/heads/lane/"):
                names.add(line[len("branch refs/heads/lane/"):])
    return names


def registered_lanes(events):
    closed = closed_items(events)
    names = set()
    for e in events:
        if e.get("item") in closed:
            continue
        for m in LANE_RE.finditer(e.get("note") or ""):
            name = m.group(1).rstrip(".")
            if name and name not in LANE_GENERIC:
                names.add(name)
    return names


def lanes(repo, events):
    """返回 (多出, 缺失)：多出 = 有分支或工作树、未收口工作项没登记；缺失 = 未收口工作项登记了、分支和工作树都不在。"""
    have = existing_lanes(repo)
    reg = registered_lanes(events)
    return sorted(f"lane/{x}" for x in have - reg), sorted(f"lane/{x}" for x in reg - have)

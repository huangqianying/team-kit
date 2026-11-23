#!/usr/bin/env python3
"""team-check 的判据。跑法：python3 skills/team-check/test_team_check.py

全程在临时目录里建 git 仓库与账本，绝不碰真实工程。
走子进程，因为被测对象包含退出码（0 通过 / 1 有问题 / 2 判不了）。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "team-check.py")
HOOK = os.path.join(HERE, "hook.py")

_fails = []


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name}" + (f"  [{detail}]" if not cond and detail else ""))
    if not cond:
        _fails.append(name)


def git(d, *a):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, check=True).stdout.strip()


def new_repo(tmp, name="repo"):
    d = os.path.join(tmp, name)
    os.makedirs(d)
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@example.invalid")
    git(d, "config", "user.name", "t")
    write(d, "README.md", "x")
    git(d, "add", ".")
    git(d, "commit", "-qm", "init")
    return d


def write(d, rel, text):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def commit(d, msg="c"):
    git(d, "add", "-A")
    git(d, "commit", "-qm", msg)
    return git(d, "rev-parse", "HEAD")


def ledger(tmp, events):
    led = os.path.join(tmp, "led")
    os.makedirs(led, exist_ok=True)
    with open(os.path.join(led, "ledger.jsonl"), "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return led


def run(args, cwd, env_extra=None):
    env = dict(os.environ, **(env_extra or {}))
    return subprocess.run([sys.executable, CHECK, *args], cwd=cwd, env=env,
                          capture_output=True, text=True)


def out(r):
    return r.stdout + r.stderr


# ───────────────────────── team-check.py ─────────────────────────

def t_scope(tmp):
    d = new_repo(tmp)
    base = git(d, "rev-parse", "HEAD")
    write(d, "src/a.py", "a")
    write(d, "docs/b.md", "b")
    c = commit(d)
    r = run(["scope", "--base", base, "--commits", c, "--allow", "src/"], d)
    check("scope 越界 → 1 并点名", r.returncode == 1 and "docs/b.md" in out(r), out(r))
    r = run(["scope", "--base", base, "--commits", c, "--allow", "src/", "docs/"], d)
    check("scope 全在可写范围 → 0", r.returncode == 0, out(r))
    r = run(["scope", "--base", base, "--commits", c, "--allow", "src/", "docs/", "--deny", "docs/"], d)
    check("scope 命中禁写 → 1", r.returncode == 1 and "docs/b.md" in out(r), out(r))
    r = run(["scope", "--base", base, "--commits", "deadbeef", "--allow", "src/"], d)
    check("scope 提交不存在 → 2", r.returncode == 2, out(r))


def t_migrations(tmp):
    d = new_repo(tmp)
    write(d, "db/mig/V3__a.sql", "")
    write(d, "db/mig/V3__b.sql", "")
    write(d, "db/mig/V4__c.sql", "")
    r = run(["migrations", "--dir", "db/mig"], d)
    check("migrations 重号 → 1 并点名 V3", r.returncode == 1 and "V3" in out(r), out(r))
    os.remove(os.path.join(d, "db/mig/V3__b.sql"))
    r = run(["migrations", "--dir", "db/mig"], d)
    check("migrations 无重号 → 0", r.returncode == 0, out(r))
    r = run(["migrations", "--dir", "nope"], d)
    check("migrations 目录不存在 → 2", r.returncode == 2, out(r))


def t_migration_dir_from_config(tmp):
    d = new_repo(tmp)
    write(d, "docs/rules/工程配置.md", "| 用途 | 位置 |\n|---|---|\n| 数据库迁移 | `db/mig/`（Flyway） |\n")
    write(d, "db/mig/V1__a.sql", "")
    write(d, "db/mig/V1__b.sql", "")
    r = run(["migrations"], d)
    check("migrations 从工程配置读目录", r.returncode == 1 and "db/mig" in out(r), out(r))
    e = new_repo(tmp, "noconf")
    r = run(["migrations"], e)
    check("migrations 读不到目录 → 2", r.returncode == 2, out(r))


def t_plan(tmp):
    d = new_repo(tmp)
    write(d, "p1.md", "# 规划\n## 并行编排\n1. 依赖图\n2. **线的划分**：a\n")
    r = run(["plan", "p1.md"], d)
    check("plan 缺「合入顺序」→ 1", r.returncode == 1 and "合入顺序" in out(r), out(r))
    write(d, "p2.md", "# 规划\n### 10.1 并行编排\n线的划分：a\n合入顺序：a→b\n")
    r = run(["plan", "p2.md"], d)
    check("plan 齐全 → 0", r.returncode == 0, out(r))
    write(d, "p3.md", "# 规划\n无\n")
    r = run(["plan", "p3.md"], d)
    check("plan 没有并行编排一节 → 1", r.returncode == 1 and "并行编排" in out(r), out(r))
    r = run(["plan", "nope.md"], d)
    check("plan 文件不存在 → 2", r.returncode == 2, out(r))


def t_lanes(tmp):
    d = new_repo(tmp)
    git(d, "branch", "lane/x")                      # 有分支、没登记 ⇒ 多出
    git(d, "branch", "lane/y2")                     # 有分支、已登记 ⇒ 一致
    led = ledger(tmp, [
        {"ts": "2026-11-23 10:00", "role": "sa", "item": "w1", "status": "交接", "to": "se",
         "note": "开线 lane/y 与 lane/y2，工作树 ../repo.lanes/y；泛指 lane/worktree 不算"},
        {"ts": "2026-11-23 10:00", "role": "sa", "item": "w2", "status": "交接", "to": "se",
         "note": "lane/z 已合入"},
        {"ts": "2026-11-23 11:00", "role": "sa", "item": "w2", "status": "完成", "note": "收口"},
    ])
    r = run(["lanes"], d, {"TEAM_LEDGER_DIR": led})
    o = out(r)
    check("lanes 不一致 → 1", r.returncode == 1, o)
    check("多出含 lane/x", "lane/x" in o.split("缺失")[0], o)
    check("缺失含 lane/y", "lane/y" in o.split("缺失")[-1] if "缺失" in o else False, o)
    check("已登记且存在的 lane/y2 不报", "lane/y2" not in o, o)
    check("已收口工作项的 lane/z 不报", "lane/z" not in o, o)
    check("lane/worktree 泛指不报", "lane/worktree" not in o, o)


ALL = [t_scope, t_migrations, t_migration_dir_from_config, t_plan, t_lanes]


def main():
    names = sys.argv[1:]
    for fn in ALL:
        if names and fn.__name__ not in names:
            continue
        print(f"\n{fn.__name__}")
        tmp = tempfile.mkdtemp(prefix="team-check-test-")
        try:
            fn(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print()
    if _fails:
        print(f"✗ {len(_fails)} 条判据不通过：")
        for name in _fails:
            print(f"    {name}")
        sys.exit(1)
    print("✓ 全部通过")


if __name__ == "__main__":
    main()

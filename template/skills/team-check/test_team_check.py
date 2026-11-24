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


# ───────────────────────── hook.py ─────────────────────────

LEDGER_SRC = os.path.join(os.path.dirname(HERE), "team-ledger", "team-ledger.py")


def kit_project(tmp, ledger_events=None):
    """装了 kit 的临时工程：.team-kit.json 记 AGENTS.md 为内核文件；账本在临时目录。"""
    d = new_repo(tmp, "proj")
    write(d, "AGENTS.md", "kernel")
    write(d, ".team-kit.json", json.dumps({"kit_version": "v0", "files": {"AGENTS.md": "x"}}))
    os.makedirs(os.path.join(d, "skills", "team-ledger"))
    shutil.copy(LEDGER_SRC, os.path.join(d, "skills", "team-ledger", "team-ledger.py"))
    led = ledger(tmp, ledger_events or [])
    return d, led


def hook(event, payload, env_extra=None, cwd=None):
    env = dict(os.environ, **(env_extra or {}))
    data = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return subprocess.run([sys.executable, HOOK, event], input=data, cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=60)


def ctx(r):
    """提醒文本：additionalContext（会话开始、写文件后）或 reason（子代理结束，decision=block）。"""
    try:
        o = json.loads(r.stdout)
    except ValueError:
        return ""
    if isinstance(o, dict) and o.get("decision") == "block":
        return o.get("reason", "")
    try:
        return o["hookSpecificOutput"]["additionalContext"]
    except (KeyError, TypeError):
        return ""


def hook_files(led):
    root = os.path.join(led, "hooks")
    return [os.path.join(a, f) for a, _, fs in os.walk(root) for f in fs] if os.path.isdir(root) else []


def t_hook_bad_input_is_silent(tmp):
    d, led = kit_project(tmp)
    env = {"TEAM_LEDGER_DIR": led}
    for ev in ("SessionStart", "PostToolUse", "SubagentStart", "SubagentStop"):
        for bad in ("", "{", json.dumps({"cwd": d})):
            r = hook(ev, bad, env, cwd=d)
            check(f"{ev} 输入「{bad[:8]}」→ 退出 0", r.returncode == 0, r.stderr)
            check(f"{ev} 输入「{bad[:8]}」→ 不输出", r.stdout.strip() == "", r.stdout)
    check("坏输入不留状态文件", hook_files(led) == [], str(hook_files(led)))


def t_session_start_injects_ledger(tmp):
    evs = [{"ts": "2026-11-23 10:00", "role": "se", "item": "条目甲", "status": "进行中", "phase": "dev"}]
    evs += [{"ts": "2026-11-23 10:00", "role": "se", "item": f"填充{i}", "status": "进行中"} for i in range(40)]
    d, led = kit_project(tmp, evs)
    r = hook("SessionStart", {"cwd": d, "session_id": "s1", "hook_event_name": "SessionStart", "source": "startup"},
             {"TEAM_LEDGER_DIR": led}, cwd=d)
    c = ctx(r)
    check("SessionStart 注入非终态项", "条目甲" in c or "填充" in c, r.stdout + r.stderr)
    check("SessionStart 注入 ≤ 2000 字符", 0 < len(c) <= 2000, str(len(c)))


def t_session_start_outside_kit_project(tmp):
    d = new_repo(tmp)
    led = ledger(tmp, [{"ts": "2026-11-23 10:00", "role": "se", "item": "x", "status": "进行中"}])
    r = hook("SessionStart", {"cwd": d, "session_id": "s1", "source": "startup"}, {"TEAM_LEDGER_DIR": led}, cwd=d)
    check("没装 kit 的仓库不注入", r.returncode == 0 and r.stdout.strip() == "", r.stdout)


def t_kernel_edit_warns_once_per_session(tmp):
    d, led = kit_project(tmp)
    env = {"TEAM_LEDGER_DIR": led}
    p = {"cwd": d, "session_id": "s9", "hook_event_name": "PostToolUse", "tool_name": "Edit",
         "tool_input": {"file_path": os.path.join(d, "AGENTS.md")}}
    r1 = hook("PostToolUse", p, env, cwd=d)
    check("改内核文件 → 提醒", "内核文件" in ctx(r1) and "AGENTS.md" in ctx(r1), r1.stdout + r1.stderr)
    r2 = hook("PostToolUse", p, env, cwd=d)
    check("同一会话同一文件只提醒一次", r2.stdout.strip() == "", r2.stdout)
    q = dict(p, tool_input={"file_path": os.path.join(d, "README.md")})
    r3 = hook("PostToolUse", q, env, cwd=d)
    check("改普通文件不提醒", r3.stdout.strip() == "", r3.stdout)


def t_codex_apply_patch_paths(tmp):
    d, led = kit_project(tmp)
    patch = (f"*** Begin Patch\n*** Update File: {d}/AGENTS.md\n@@\n-kernel\n+k2\n"
             f"*** Add File: {d}/docs/new.md\n+new\n*** End Patch")
    p = {"cwd": d, "session_id": "c1", "hook_event_name": "PostToolUse", "tool_name": "apply_patch",
         "tool_input": {"command": patch}}
    r = hook("PostToolUse", p, {"TEAM_LEDGER_DIR": led}, cwd=d)
    check("Codex apply_patch 解析出内核文件并提醒", "AGENTS.md" in ctx(r) and "docs/new.md" not in ctx(r),
          r.stdout + r.stderr)


def t_check_after_edit(tmp):
    import time
    d, led = kit_project(tmp)
    env = {"TEAM_LEDGER_DIR": led}
    p = {"cwd": d, "session_id": "k1", "hook_event_name": "PostToolUse", "tool_name": "Write",
         "tool_input": {"file_path": os.path.join(d, "README.md")}}
    write(d, ".githooks/project.conf", "HOOK_CRED_HINT='x'\nCHECK_AFTER_EDIT='sh -c \"echo bad; exit 1\"'\n")
    r = hook("PostToolUse", p, env, cwd=d)
    check("工程检查失败 → 提醒含输出", "bad" in ctx(r), r.stdout + r.stderr)
    write(d, ".githooks/project.conf", "CHECK_AFTER_EDIT='sh -c \"echo fine; exit 0\"'\n")
    r = hook("PostToolUse", p, env, cwd=d)
    check("工程检查通过 → 不提醒", r.stdout.strip() == "", r.stdout)
    write(d, ".githooks/project.conf", "CHECK_AFTER_EDIT='sh -c \"sleep 20\"'\n")
    t0 = time.time()
    r = hook("PostToolUse", p, env, cwd=d)
    check("工程检查超时 8 秒左右返回、退出 0", r.returncode == 0 and time.time() - t0 < 15, f"{time.time() - t0:.1f}s")


def t_subagent_stop_reminds_once(tmp):
    d, led = kit_project(tmp)
    env = {"TEAM_LEDGER_DIR": led}
    base = {"cwd": d, "session_id": "s1"}
    hook("SubagentStart", dict(base, hook_event_name="SubagentStart", agent_id="a1", agent_type="se"), env, cwd=d)
    stop = dict(base, hook_event_name="SubagentStop", agent_id="a1", agent_type="se", stop_hook_active=False)
    r = hook("SubagentStop", stop, env, cwd=d)
    check("SE 没落账就结束 → 提醒", "还没有落账" in ctx(r), r.stdout + r.stderr)
    r = hook("SubagentStop", dict(stop, stop_hook_active=True), env, cwd=d)
    check("stop_hook_active 时不再提醒", r.stdout.strip() == "", r.stdout)
    hook("SubagentStart", dict(base, hook_event_name="SubagentStart", agent_id="a2", agent_type="se"), env, cwd=d)
    subprocess.run([sys.executable, os.path.join(d, "skills/team-ledger/team-ledger.py"), "append",
                    "--role", "se", "--item", "w", "--status", "进行中"], cwd=d,
                   env=dict(os.environ, TEAM_LEDGER_DIR=led, TEAM_LEDGER_GIT_DIR=d), capture_output=True)
    r = hook("SubagentStop", dict(stop, agent_id="a2"), env, cwd=d)
    check("SE 落过账 → 不提醒", r.stdout.strip() == "", r.stdout)
    hook("SubagentStart", dict(base, hook_event_name="SubagentStart", agent_id="a3", agent_type="Explore"), env, cwd=d)
    r = hook("SubagentStop", dict(stop, agent_id="a3", agent_type="Explore"), env, cwd=d)
    check("非团队角色不提醒", r.stdout.strip() == "", r.stdout)
    check("结束后不留开始时间文件", [f for f in hook_files(led) if "/agents/" in f] == [], str(hook_files(led)))


def t_session_start_lanes_first(tmp):
    evs = [{"ts": "2026-11-23 10:00", "role": "pm", "item": f"等裁决很长的工作项名字{i}", "status": "阻塞",
            "blocker_role": "owner", "blocker": "等负责人裁定一段相当长的说明文字" * 12} for i in range(30)]
    d, led = kit_project(tmp, evs)
    git(d, "branch", "lane/unregistered-x")
    r = hook("SessionStart", {"cwd": d, "session_id": "s", "source": "startup"}, {"TEAM_LEDGER_DIR": led}, cwd=d)
    c = ctx(r)
    check("长账本下「未登记的线」仍在注入里", "lane/unregistered-x" in c, c[-300:])
    check("注入仍 ≤ 2000 字符", len(c) <= 2000, str(len(c)))


def t_lane_worktree_edit(tmp):
    d, led = kit_project(tmp)
    commit(d, "kit")
    wt = os.path.join(tmp, "proj.lanes", "a")
    git(d, "worktree", "add", "-q", "-b", "lane/a", wt)
    p = {"cwd": d, "session_id": "lw", "hook_event_name": "PostToolUse", "tool_name": "Edit",
         "tool_input": {"file_path": os.path.join(wt, "AGENTS.md")}, "agent_type": "se", "agent_id": "x"}
    r = hook("PostToolUse", p, {"TEAM_LEDGER_DIR": led}, cwd=d)
    check("线工作树里改内核文件也提醒", "AGENTS.md" in ctx(r), r.stdout + r.stderr)


def t_subagent_stop_continues_via_block(tmp):
    d, led = kit_project(tmp)
    env = {"TEAM_LEDGER_DIR": led}
    hook("SubagentStart", {"cwd": d, "agent_id": "b1", "agent_type": "qa"}, env, cwd=d)
    r = hook("SubagentStop", {"cwd": d, "agent_id": "b1", "agent_type": "qa", "stop_hook_active": False}, env, cwd=d)
    try:
        o = json.loads(r.stdout)
    except ValueError:
        o = {}
    check("子代理结束提醒用 decision=block + reason（两个宿主都支持）",
          o.get("decision") == "block" and "还没有落账" in o.get("reason", ""), r.stdout)


def t_migrations_refs(tmp):
    d = new_repo(tmp)
    write(d, "db/mig/V1__a.sql", "")
    commit(d, "v1")
    git(d, "checkout", "-q", "-b", "lane/a")
    write(d, "db/mig/V2__lane.sql", "")
    commit(d, "lane")
    git(d, "checkout", "-q", "-")
    write(d, "db/mig/V2__main.sql", "")
    commit(d, "main")
    main = git(d, "rev-parse", "--abbrev-ref", "HEAD")
    r = run(["migrations", "--dir", "db/mig"], d)
    check("单看集成分支查不出跨分支撞号（说明为何需要 --refs）", r.returncode == 0, out(r))
    r = run(["migrations", "--dir", "db/mig", "--refs", main, "lane/a"], d)
    check("--refs 对照两边查出 V2 撞号", r.returncode == 1 and "V2" in out(r), out(r))


def t_migrations_refs_missing_dir(tmp):
    """目录在所有分支上都不存在 ⇒ 判不了（退 2），不能报「无重复」。只在一边存在照常判。"""
    d = new_repo(tmp)
    write(d, "db/mig/V1__a.sql", "")
    commit(d, "v1")
    git(d, "branch", "lane/a")
    main = git(d, "rev-parse", "--abbrev-ref", "HEAD")
    r = run(["migrations", "--dir", "db/nope", "--refs", main, "lane/a"], d)
    check("--refs 目录都不存在 → 判不了退 2", r.returncode == 2 and "判不了" in out(r), out(r))
    git(d, "checkout", "-q", "--orphan", "lane/empty")
    git(d, "rm", "-rq", "--cached", ".")
    write(d, "x.txt", "")
    git(d, "add", "x.txt")
    commit(d, "empty")
    git(d, "checkout", "-q", "-f", main)
    r = run(["migrations", "--dir", "db/mig", "--refs", main, "lane/empty"], d)
    check("--refs 只在一边存在 → 照常判、无重复退 0", r.returncode == 0, out(r))


def t_session_start_owner_via_to(tmp):
    evs = [{"ts": "2026-11-23 10:00", "role": "sa", "item": "请负责人验收", "status": "待评审", "to": "owner"},
           {"ts": "2026-11-23 10:00", "role": "sa", "item": "等他裁", "status": "阻塞", "blocker_role": "owner",
            "blocker": "x"}]
    d, led = kit_project(tmp, evs)
    r = hook("SessionStart", {"cwd": d, "session_id": "s1", "hook_event_name": "SessionStart", "source": "startup"},
             {"TEAM_LEDGER_DIR": led}, cwd=d)
    c = ctx(r)
    check("待评审 --to owner 出现在会话注入里", "请负责人验收" in c, c)
    check("阻塞 → owner 只出现一次", c.count("等他裁") == 1, c)


def t_session_start_owner_newest_first(tmp):
    """待裁决多时，注入只放得下前几行：每项一行、最新的在前，新交给负责人的不能被老项挤掉。"""
    evs = [{"ts": f"2026-11-0{i} 10:00", "role": "sa", "item": f"老项{i}", "status": "阻塞",
            "blocker_role": "owner", "blocker": "很长的卡点" * 5} for i in range(1, 10)]
    evs.append({"ts": "2026-11-21 12:40", "role": "sa", "item": "最新交给负责人", "status": "待评审", "to": "owner"})
    d, led = kit_project(tmp, evs)
    r = hook("SessionStart", {"cwd": d, "session_id": "s1", "hook_event_name": "SessionStart", "source": "startup"},
             {"TEAM_LEDGER_DIR": led}, cwd=d)
    c = ctx(r)
    check("最新交给负责人的项在注入里", "最新交给负责人" in c, c[:600])
    check("注入里的待裁决每项一行（不带卡点行）", "卡点：" not in c, c[:600])
    check("注入里最新的排在最前", c.find("最新交给负责人") < c.find("老项9") < c.find("老项8") if "老项8" in c else False, c[:600])


def t_seen_file_corrupt_still_warns(tmp):
    d, led = kit_project(tmp)
    os.makedirs(os.path.join(led, "hooks"), exist_ok=True)
    open(os.path.join(led, "hooks", "seen-cz.json"), "w").write("[\"AGE")
    p = {"cwd": d, "session_id": "cz", "tool_name": "Edit", "tool_input": {"file_path": os.path.join(d, "AGENTS.md")}}
    r = hook("PostToolUse", p, {"TEAM_LEDGER_DIR": led}, cwd=d)
    check("状态文件写坏仍提醒", "AGENTS.md" in ctx(r), r.stdout + r.stderr)


def t_check_after_edit_trailing_comment(tmp):
    d, led = kit_project(tmp)
    write(d, ".githooks/project.conf", "CHECK_AFTER_EDIT='sh -c \"echo bad2; exit 1\"'  # 工程检查\n")
    p = {"cwd": d, "session_id": "tc", "tool_name": "Write", "tool_input": {"file_path": os.path.join(d, "README.md")}}
    r = hook("PostToolUse", p, {"TEAM_LEDGER_DIR": led}, cwd=d)
    check("CHECK_AFTER_EDIT 行尾带注释也能执行", "bad2" in ctx(r), r.stdout + r.stderr)


def t_notebook_path(tmp):
    d, led = kit_project(tmp)
    p = {"cwd": d, "session_id": "nb", "tool_name": "NotebookEdit",
         "tool_input": {"notebook_path": os.path.join(d, "AGENTS.md")}}
    r = hook("PostToolUse", p, {"TEAM_LEDGER_DIR": led}, cwd=d)
    check("NotebookEdit 的 notebook_path 也能识别", "AGENTS.md" in ctx(r), r.stdout + r.stderr)


ALL = [t_scope, t_migrations, t_migration_dir_from_config, t_plan, t_lanes,
       t_hook_bad_input_is_silent, t_session_start_injects_ledger, t_session_start_outside_kit_project,
       t_kernel_edit_warns_once_per_session, t_codex_apply_patch_paths, t_check_after_edit,
       t_subagent_stop_reminds_once, t_session_start_lanes_first, t_lane_worktree_edit,
       t_subagent_stop_continues_via_block, t_migrations_refs, t_seen_file_corrupt_still_warns,
       t_check_after_edit_trailing_comment, t_notebook_path, t_migrations_refs_missing_dir,
       t_session_start_owner_via_to, t_session_start_owner_newest_first]


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

#!/usr/bin/env python3
"""两个宿主（Claude Code、Codex）共用的钩子入口：只提醒，绝不拦截。

用法：python3 skills/team-check/hook.py <SessionStart|PostToolUse|SubagentStart|SubagentStop>
stdin 是宿主传来的 JSON；需要提醒时输出
  {"hookSpecificOutput": {"hookEventName": <事件>, "additionalContext": <文本>}}
不需要提醒时什么都不输出。任何异常都吞掉、退出码一律 0：钩子出错不能拖慢或打断会话。
宿主输入格式的实测见 docs/superpowers/specs/2026-11-23-check-mechanisms-design.md 附录 A（team-kit 仓库）。
"""
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROLES = {"pm", "ui", "se", "qa"}
SESSION_LIMIT = 2000          # 会话开始注入的总长上限（照顾 Codex 的上下文注入上限）
CHECK_LIMIT = 1500            # 工程检查输出截取长度
CHECK_TIMEOUT = 8
LEDGER_TIMEOUT = 5
PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+?)\s*$", re.M)


def emit(event, text):
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}},
                         ensure_ascii=False))


def ledger_now():
    """与 team-ledger.py 的 ts 同格式同时区（TEAM_LEDGER_UTC_OFFSET，默认 +8），便于字符串比较。"""
    try:
        off = float(os.environ.get("TEAM_LEDGER_UTC_OFFSET", "8"))
    except ValueError:
        off = 8.0
    return datetime.now(timezone(timedelta(hours=off))).strftime("%Y-%m-%d %H:%M")


def kernel_files(root):
    with open(os.path.join(root, ".team-kit.json"), encoding="utf-8") as f:
        return set(json.load(f).get("files", {}))


def state_dir(led, *sub):
    d = os.path.join(led, "hooks", *sub)
    os.makedirs(d, exist_ok=True)
    return d


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(s))[:120]


# ─────────── H1 会话开始 ───────────

def run_ledger(root, *args):
    """返回 (退出码, 输出)。stale/owner 退出码 0 = 没有要看的项。"""
    script = os.path.join(root, "skills", "team-ledger", "team-ledger.py")
    if not os.path.exists(script):
        return 0, ""
    r = subprocess.run([sys.executable, script, *args], cwd=root, capture_output=True, text=True,
                       timeout=LEDGER_TIMEOUT)
    return r.returncode, r.stdout.strip()


def head(text, n):
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) <= n:
        return lines
    return lines[:n] + [f"  …另有 {len(lines) - n} 行（完整见 team-ledger.py 对应命令）"]


def session_start(root, led, payload):
    import checks
    if not os.path.exists(os.path.join(led, "ledger.jsonl")):
        return ""
    parts = ["团队账本当前态（会话开始时由钩子自动读取，仅供参考；以 team-ledger.py 实时输出为准）："]
    rc, stale = run_ledger(root, "stale", "--hours", "0")
    if rc != 0 and stale:
        parts += head(stale, 15)
    rc, owner = run_ledger(root, "owner")
    if rc != 0 and owner:
        parts += head(owner, 10)
    try:
        extra, _ = checks.lanes(root, checks.read_events(led))
    except (ValueError, OSError, subprocess.SubprocessError):
        extra = []
    if extra:
        parts.append("有工作树或分支、但未收口工作项里没登记的线：" + "、".join(extra)
                     + "（docs/rules/并行线.md「三」：开线要落账写分支名）")
    if len(parts) == 1:
        return ""                  # 没有非终态项、待裁决或未登记的线：不注入，不刷屏
    text = "\n".join(parts)
    return text[:SESSION_LIMIT - 1] + "…" if len(text) > SESSION_LIMIT else text


# ─────────── H2 写文件后 ───────────

def edited_paths(payload, root):
    ti = payload.get("tool_input") or {}
    raw = []
    if isinstance(ti, dict):
        if isinstance(ti.get("file_path"), str):
            raw.append(ti["file_path"])
        if isinstance(ti.get("command"), str) and "*** Begin Patch" in ti["command"]:
            raw += PATCH_FILE_RE.findall(ti["command"])
    out = []
    real_root = os.path.realpath(root)
    for p in raw:
        full = p if os.path.isabs(p) else os.path.join(payload.get("cwd") or root, p)
        rel = os.path.relpath(os.path.realpath(full), real_root)
        if not rel.startswith(".."):
            out.append(rel)
    return out


def check_after_edit_cmd(root):
    p = os.path.join(root, ".githooks", "project.conf")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\s*CHECK_AFTER_EDIT=(.*)$", line)
            if m:
                parts = shlex.split(m.group(1))
                if len(parts) == 1:          # CHECK_AFTER_EDIT='cmd args' ⇒ 引号内整体是命令串
                    parts = shlex.split(parts[0])
                return parts or None
    return None


def post_tool_use(root, led, payload):
    paths = edited_paths(payload, root)
    if not paths:
        return ""
    notes = []
    kernel = kernel_files(root)
    hit = [p for p in paths if p in kernel]
    if hit:
        seen_file = os.path.join(state_dir(led), f"seen-{safe_name(payload.get('session_id', 'nosession'))}.json")
        seen = set()
        if os.path.exists(seen_file):
            with open(seen_file, encoding="utf-8") as f:
                seen = set(json.load(f))
        new = [p for p in hit if p not in seen]
        if new:
            notes.append("、".join(f"`{p}`" for p in new) + " 是 team-kit 内核文件，各工程逐字相同；"
                         "改动要报 team-kit 维护方，不在工程里直接改（AGENTS.md）。")
            with open(seen_file, "w", encoding="utf-8") as f:
                json.dump(sorted(seen | set(new)), f, ensure_ascii=False)
    cmd = check_after_edit_cmd(root)
    if cmd:
        try:
            r = subprocess.run(cmd + paths, cwd=root, capture_output=True, text=True, timeout=CHECK_TIMEOUT)
            if r.returncode != 0:
                outp = (r.stdout + r.stderr).strip()[:CHECK_LIMIT]
                notes.append(f"工程检查（.githooks/project.conf 的 CHECK_AFTER_EDIT）未通过：\n{outp}")
        except subprocess.TimeoutExpired:
            notes.append(f"工程检查（CHECK_AFTER_EDIT）超过 {CHECK_TIMEOUT} 秒未结束，已跳过。")
        except OSError:
            pass
    return "\n".join(notes)


# ─────────── H3 子代理开始与结束 ───────────

def subagent_start(led, payload):
    if payload.get("agent_type") in ROLES and payload.get("agent_id"):
        with open(os.path.join(state_dir(led, "agents"), safe_name(payload["agent_id"])), "w") as f:
            f.write(ledger_now())
    return ""


def subagent_stop(led, payload):
    role, aid = payload.get("agent_type"), payload.get("agent_id")
    if role not in ROLES or not aid:
        return ""
    start_file = os.path.join(led, "hooks", "agents", safe_name(aid))
    if not os.path.exists(start_file):
        return ""
    with open(start_file) as f:
        started = f.read().strip()
    os.remove(start_file)
    if payload.get("stop_hook_active"):
        return ""
    import checks
    logged = any(e.get("role") == role and str(e.get("ts", "")) >= started for e in checks.read_events(led))
    if logged:
        return ""
    return ("本次还没有落账。请按 skills/team-ledger/SKILL.md 落账，"
            "并按 docs/rules/派活与交付.md「二、回报」回报四项（状态、实际改动、验证、未完成与下一步）后再结束。")


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else None
    if not isinstance(payload, dict):
        return
    import checks
    root = checks.repo_root(payload.get("cwd") or os.getcwd())
    if not root or not os.path.exists(os.path.join(root, ".team-kit.json")):
        return
    led = checks.ledger_dir(root)
    if not led:
        return
    handler = {
        "SessionStart": lambda: session_start(root, led, payload),
        "PostToolUse": lambda: post_tool_use(root, led, payload),
        "SubagentStart": lambda: subagent_start(led, payload),
        "SubagentStop": lambda: subagent_stop(led, payload),
    }.get(event)
    if handler:
        emit(event, handler())


if __name__ == "__main__":
    try:
        main()
    except BaseException:      # noqa: BLE001 —— 只提醒的钩子：任何错误都不能影响会话
        pass
    sys.exit(0)

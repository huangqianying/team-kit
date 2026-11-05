#!/usr/bin/env python3
"""team-ledger.py 的判据。跑法：python3 skills/team-ledger/test_team_ledger.py

**全程用 `TEAM_LEDGER_DIR` 隔离到临时目录，绝不碰真实账本。**
不引 pytest（账本是运维工具、不该为测试拉依赖），用文件内的 check() harness，直接运行本文件即可。
每条判据都走子进程，因为被测对象**包含退出码**——值守与门禁都按退出码分支，
`sys.exit` 在同进程里测不出它真实的那一面。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "team-ledger.py")

_fails = []


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name}" + (f"  [{detail}]" if not cond and detail else ""))
    if not cond:
        _fails.append(name)


def mkenv(tmp, version="v9.9.9"):
    """隔离的账本目录 ＋ 隔离的版本真值源。"""
    if version is not None:
        with open(os.path.join(tmp, "system-version.json"), "w", encoding="utf-8") as f:
            json.dump({"version": version, "status": "in-progress"}, f)
    return dict(os.environ, TEAM_LEDGER_DIR=tmp)


def run(env, *args):
    return subprocess.run([sys.executable, LEDGER, *args],
                          capture_output=True, text=True, env=env)


def out(r):
    return r.stdout + r.stderr


def events(tmp):
    p = os.path.join(tmp, "ledger.jsonl")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def append(env, **kw):
    args = ["append"]
    for k, v in kw.items():
        if v is True:
            args.append(f"--{k.replace('_', '-')}")
        else:
            args += [f"--{k.replace('_', '-')}", str(v)]
    return run(env, *args)


# ───────────────────────── append：落账与校验 ─────────────────────────

def t_append(tmp):
    env = mkenv(tmp)
    r = append(env, role="se", item="x", status="进行中", phase="开发")
    check("落账成功", r.returncode == 0, out(r))
    evs = events(tmp)
    check("只写一行", len(evs) == 1, str(len(evs)))
    ev = evs[0] if evs else {}
    check("字段原样落盘", ev.get("role") == "se" and ev.get("item") == "x"
          and ev.get("status") == "进行中", json.dumps(ev, ensure_ascii=False))
    check("中文门名归一为 slug", ev.get("phase") == "dev", str(ev.get("phase")))
    check("版本取自 system-version.json、不自己造", ev.get("version") == "v9.9.9",
          str(ev.get("version")))


def t_version_missing(tmp):
    env = mkenv(tmp, version=None)
    r = append(env, role="sa", item="x", status="进行中")
    check("真值源缺失仍落账", r.returncode == 0, out(r))
    check("缺失时落 _infra", events(tmp)[0].get("version") == "_infra")


def t_reject(tmp):
    cases = [
        ("role 非法", dict(role="ta", item="x", status="进行中"), "role 非法"),
        ("status 非法", dict(role="se", item="x", status="在做"), "status 非法"),
        ("phase 非法", dict(role="se", item="x", status="进行中", phase="玄学"), "phase 非法"),
        ("decision 非法", dict(role="se", item="x", status="完成", decision="OK"), "decision 非法"),
        ("阻塞无卡点", dict(role="se", item="x", status="阻塞", blocker_role="sa"), "--blocker"),
        ("接续方非法", dict(role="se", item="x", status="交接", to="boss"), "取值非法"),
    ]
    for name, kw, needle in cases:
        d = tempfile.mkdtemp(dir=tmp)
        env = mkenv(d)
        r = append(env, **kw)
        check(f"硬拒：{name}", r.returncode != 0 and needle in out(r), out(r)[:120])
        check(f"硬拒后不落账：{name}", events(d) == [], "校验不通过还落账 = 账本进脏数据")


def t_successor_required(tmp):
    """不写接续方，SA 就看不出这棒该派给谁 —— 等于掉棒。"""
    for status, flag in (("交接", "--to"), ("待评审", "--to"), ("阻塞", "--blocker-role")):
        d = tempfile.mkdtemp(dir=tmp)
        env = mkenv(d)
        kw = dict(role="se", item="x", status=status)
        if status == "阻塞":
            kw["blocker"] = "等裁定"
        r = append(env, **kw)
        check(f"{status} 必须指定接续方", r.returncode != 0 and flag in out(r), out(r)[:120])


def t_owner_successor(tmp):
    env = mkenv(tmp)
    r = append(env, role="se", item="x", status="阻塞",
               blocker_role="owner", blocker="等产品负责人裁")
    check("接续方可以是 owner", r.returncode == 0, out(r))
    check("owner 落进 blocker_role", events(tmp)[0].get("blocker_role") == "owner")


# ──────────────── 同事异名硬拒：「一个 item ＝ 一条评审线」的前提 ────────────────

def t_item_clash(tmp):
    """归一键相同即判同一工作项。契约「附：状态账本」定「一个 item ＝ 一条独立的评审线」，
    轮次按 item 计（契约「评审与合入」：轮次封顶 1）；拆成两行等于把一条评审线记成两条，
    其中一条没人认领 —— 故这条是粒度判据的前提，不是洁癖。"""
    for second in ("Gate-3_Design", "gate3design", "gate3　design"):
        d = tempfile.mkdtemp(dir=tmp)
        env = mkenv(d)
        append(env, role="se", item="gate3-design", status="进行中")
        r = append(env, role="se", item=second, status="进行中")
        check(f"同事异名硬拒：{second!r}", r.returncode != 0 and "同事异名" in out(r), out(r)[:120])
        check(f"拒绝理由点出它守的是什么：{second!r}", "独立的评审线" in out(r))
        check(f"硬拒后仍只有一行：{second!r}", len(events(d)) == 1)


def t_item_clash_scope(tmp):
    """同一名字在不同角色下是两条独立的轮次线（PM 半签 / SE 半签）。"""
    env = mkenv(tmp)
    append(env, role="se", item="gate3-design", status="进行中")
    r = append(env, role="pm", item="gate3_design", status="进行中")
    check("同名硬拒只在同角色内生效", r.returncode == 0, out(r))
    check("两角色各一行", len(events(tmp)) == 2)


def t_force_new_item(tmp):
    env = mkenv(tmp)
    append(env, role="se", item="gate3-design", status="进行中")
    r = append(env, role="se", item="gate3_design", status="进行中", force_new_item=True)
    check("--force-new-item 不给理由即拒", r.returncode != 0 and "--note" in out(r), out(r)[:120])
    r = append(env, role="se", item="gate3_design", status="进行中",
               force_new_item=True, note="确属另一件事")
    check("给了理由可绕过", r.returncode == 0, out(r))
    check("绕过硬拒必须留痕", events(tmp)[-1].get("forced_new_item") is True)


# ───────────────────────── stale ─────────────────────────

def t_stale_quiet(tmp):
    env = mkenv(tmp)
    append(env, role="se", item="x", status="进行中")
    r = run(env, "stale")          # 默认 24h，刚落的账不算停滞
    check("无停滞退 0", r.returncode == 0 and "无停滞项" in r.stdout, out(r)[:120])


def t_stale_hours0(tmp):
    """`--hours 0` 是当前态视图：现算现打，不落第二份文件。"""
    env = mkenv(tmp)
    append(env, role="se", item="做着的", status="进行中")
    append(env, role="pm", item="等评审的", status="待评审", to="sa")
    append(env, role="qa", item="收了口的", status="完成")
    r = run(env, "stale", "--hours", "0")
    check("--hours 0 退 1（有非终态项）", r.returncode == 1, out(r)[:120])
    check("列出非终态项", "做着的" in r.stdout and "等评审的" in r.stdout)
    check("终态项不是停滞", "收了口的" not in r.stdout)
    check("非终态行带出接续方", "→ SA" in r.stdout, r.stdout[:200])


def t_stale_owner_tag(tmp):
    env = mkenv(tmp)
    append(env, role="se", item="等裁的", status="阻塞",
           blocker_role="owner", blocker="等产品负责人")
    r = run(env, "stale", "--hours", "0")
    check("owner 项标注为等人", "OWNER（等人裁决，不派 subagent）" in r.stdout, r.stdout[:200])


def t_stale_bad_ts(tmp):
    """判不了 ≠ 没停滞。值守按退出码分支，混成 0 会把真停滞报成全清。"""
    env = mkenv(tmp)
    with open(os.path.join(tmp, "ledger.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": "昨天", "role": "se", "item": "x",
                            "status": "进行中", "version": "v9.9.9"},
                           ensure_ascii=False) + "\n")
    r = run(env, "stale")
    check("坏时间戳退 2、不报全清", r.returncode == 2 and "无法判定" in r.stdout, out(r)[:160])


def t_bad_line(tmp):
    env = mkenv(tmp)
    with open(os.path.join(tmp, "ledger.jsonl"), "w", encoding="utf-8") as f:
        f.write("{这不是 json\n")
    r = run(env, "stale", "--hours", "0")
    check("坏行跳过、不阻塞读账", r.returncode == 0, out(r)[:160])


# ───────────────────────── owner ─────────────────────────

def t_owner(tmp):
    env = mkenv(tmp)
    append(env, role="se", item="等裁的", status="阻塞",
           blocker_role="owner", blocker="MVP 边界要他定")
    append(env, role="pm", item="等SA的", status="阻塞",
           blocker_role="sa", blocker="等裁定")
    r = run(env, "owner")
    check("有待裁决退 1", r.returncode == 1, out(r)[:120])
    check("列出卡点原文", "等裁的" in r.stdout and "MVP 边界要他定" in r.stdout)
    check("卡在 subagent 的不进待裁决清单", "等SA的" not in r.stdout)


def t_owner_closed(tmp):
    """只看当前态——否则清单会被已收口的历史项淹掉，真待裁决的项反而看不见。"""
    env = mkenv(tmp)
    append(env, role="se", item="x", status="阻塞", blocker_role="owner", blocker="等他定")
    append(env, role="se", item="x", status="完成", note="他定了")
    r = run(env, "owner")
    check("收口后不再列", r.returncode == 0 and "无待产品负责人裁决" in r.stdout, out(r)[:120])


# ───────────────────────── 并发 ─────────────────────────

def t_concurrent(tmp):
    """flock + O_APPEND：20 条并发落账一条不丢、且每行都是完整 JSON。"""
    env = mkenv(tmp)
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(lambda i: append(env, role="se", item=f"i{i}", status="进行中"), range(20)))
    evs = events(tmp)
    check("20 条并发一条不丢", len(evs) == 20, str(len(evs)))
    check("无半截行", len({e["item"] for e in evs}) == 20)


# ───────────────────── 不要的命令不许悄悄回来 ─────────────────────

def t_removed_subcommands(tmp):
    """账本只有三条命令（射程见 DESIGN.md）。这条判据钉住射程：
    谁要把某条加回来，得先改这里，而不是悄悄长回去。"""
    env = mkenv(tmp)
    for gone in ("show", "render", "log", "owed", "items", "archive",
                 "set-version", "verify-artifact", "verify-candidate"):
        r = run(env, gone)
        check(f"子命令不存在：{gone}", r.returncode != 0 and "invalid choice" in out(r), out(r)[:120])


def t_removed_anchor_flags(tmp):
    """这些锚没有核证方：产物版本与证据由契约统一规定，账本不核锚、也不派活。
    留着一个没人核的锚，和一个正确的锚在账本里长得一模一样。"""
    env = mkenv(tmp)
    for gone in ("--artifact", "--at", "--candidate", "--job"):
        r = run(env, "append", "--role", "se", "--item", "x", "--status", "进行中", gone, "随便")
        check(f"落锚参数不存在：{gone}",
              r.returncode != 0 and "unrecognized arguments" in out(r), out(r)[:120])


def t_no_md(tmp):
    """md 是 jsonl 的派生态，留着就是同一事实两个源。"""
    env = mkenv(tmp)
    append(env, role="se", item="x", status="进行中")
    check("不再渲染 ledger.md", not os.path.exists(os.path.join(tmp, "ledger.md")))


def t_ui_phase_alias(tmp):
    env = mkenv(tmp)
    for i, name in enumerate(["UI设计", "界面设计", "UI原型", "原型"]):
        r = append(env, role="ui", item=f"p{i}", status="进行中", phase=name)
        check(f"「{name}」落账成功", r.returncode == 0, out(r))
    got = [e.get("phase") for e in events(tmp)]
    check("UI 的中文门名归一到现行的 ui-proto（ui-design 只为兼容存量行）",
          got == ["ui-proto"] * 4, str(got))
    r = append(env, role="ui", item="legacy", status="进行中", phase="ui-design")
    check("显式写 ui-design 仍可落账（兼容存量）", r.returncode == 0 and events(tmp)[-1].get("phase") == "ui-design", out(r))


def t_utc_offset(tmp):
    from datetime import datetime, timedelta, timezone
    env = mkenv(tmp)
    env["TEAM_LEDGER_UTC_OFFSET"] = "0"
    r = append(env, role="se", item="tz", status="进行中")
    check("设 UTC 偏移后落账成功", r.returncode == 0, out(r))
    ts = events(tmp)[-1].get("ts", "")
    utc_now = datetime.now(timezone.utc)
    want = {(utc_now + timedelta(minutes=d)).strftime("%Y-%m-%d %H:%M") for d in (-1, 0, 1)}
    check("TEAM_LEDGER_UTC_OFFSET=0 时按 UTC 记时间", ts in want, f"{ts} not in {sorted(want)}")
    env2 = mkenv(tmp)
    r = run(env2, "stale", "--hours", "0")
    check("默认仍按 UTC+8 解读存量时间：刚记的 UTC 时间看起来是 8 小时前",
          "8.0h" in out(r) or "7.9h" in out(r) or "8.1h" in out(r), out(r))
    env3 = mkenv(tmp)
    env3["TEAM_LEDGER_UTC_OFFSET"] = "abc"
    r = append(env3, role="se", item="tz2", status="进行中")
    check("偏移值不合法时硬拒、不落账", r.returncode != 0 and len(events(tmp)) == 1, out(r))


ALL = [t_append, t_version_missing, t_reject, t_successor_required, t_owner_successor,
       t_item_clash, t_item_clash_scope, t_force_new_item,
       t_stale_quiet, t_stale_hours0, t_stale_owner_tag, t_stale_bad_ts, t_bad_line,
       t_owner, t_owner_closed, t_concurrent,
       t_removed_subcommands, t_removed_anchor_flags, t_no_md,
       t_ui_phase_alias, t_utc_offset]


def main():
    for fn in ALL:
        print(f"\n{fn.__name__}")
        tmp = tempfile.mkdtemp(prefix="ledger-test-")
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

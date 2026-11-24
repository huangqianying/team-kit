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
    # 提交号核对在 TEAM_LEDGER_GIT_DIR 指向的仓库里做；临时目录不是 git 仓库 ⇒ 判不了、只警告，不影响老判据
    return dict(os.environ, TEAM_LEDGER_DIR=tmp, TEAM_LEDGER_GIT_DIR=tmp)


def run(env, *args):
    return subprocess.run([sys.executable, LEDGER, *args],
                          capture_output=True, text=True, env=env,
                          cwd=env.get("TEAM_LEDGER_GIT_DIR"))


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


def t_owner_via_to(tmp):
    """非阻塞状态用 --to owner 交给负责人（如 SA 落「待评审 --to owner」请负责人验收），也在等人。
    stale 把它标成「→ OWNER」，owner 清单也得列它，否则两边都不出现在会话开始的注入里。"""
    env = mkenv(tmp)
    append(env, role="sa", item="等验收的", status="待评审", to="owner", note="请负责人验收")
    append(env, role="sa", item="交给SE的", status="待评审", to="se", note="x")
    append(env, role="sa", item="已交接的", status="交接", to="owner", note="终态")
    r = run(env, "owner")
    check("待评审 --to owner 进待裁决清单", r.returncode == 1 and "等验收的" in r.stdout, out(r)[:200])
    check("--to 其他角色的不进", "交给SE的" not in r.stdout, out(r)[:200])
    check("终态（交接）的不进", "已交接的" not in r.stdout, out(r)[:200])


def t_handoff_to_owner_warns(tmp):
    """交接是终态：交接 --to owner 不进 owner、不进 stale。缺 --to 的报错不能对交接许诺「进待裁决清单」，
    真这样落了要警告。"""
    env = mkenv(tmp)
    r = append(env, role="sa", item="x", status="交接")
    check("交接缺 --to：报错不许诺进待裁决清单", r.returncode != 0 and "待裁决清单" not in out(r).split("交接是终态")[0]
          and "交接是终态" in out(r), out(r)[:300])
    r = append(env, role="sa", item="y", status="交接", to="owner", note="待负责人验收")
    check("交接 --to owner 照常落账", r.returncode == 0, out(r)[:200])
    check("交接 --to owner 警告不进待裁决清单", "警告" in r.stderr and "阻塞 --blocker-role owner" in r.stderr, r.stderr[:300])
    r = append(env, role="sa", item="z", status="待评审", to="owner", note="请验收")
    check("待评审 --to owner 不警告", "警告" not in r.stderr, r.stderr[:200])


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


# ───────────────────────── 收口与子产物 ─────────────────────────

def t_handoff_does_not_fold(tmp):
    """反向判据：主线进行中 ＋ 另一角色在同一工作项上落「交接」，主线仍须出现在 stale 里。"""
    env = mkenv(tmp)
    append(env, role="se", item="I5", status="进行中")
    append(env, role="pm", item="I5", status="交接", to="se", note="澄清完了交回 SE")
    r = run(env, "stale", "--hours", "0")
    check("交接不折叠整项：主线 SE 的「进行中」仍在 stale 里",
          r.returncode == 1 and " se " in out(r) and "I5" in out(r) and "已收口" not in out(r), out(r))


def t_complete_still_folds(tmp):
    env = mkenv(tmp)
    append(env, role="se", item="Y", status="待评审", to="sa")
    append(env, role="sa", item="Y", status="完成", decision="APPROVED")
    r = run(env, "stale", "--hours", "0")
    check("「完成」仍让整项收口：被评方停在待评审的那行折叠", r.returncode == 0 and "已收口" in out(r), out(r))


def t_part_rows(tmp):
    env = mkenv(tmp)
    append(env, role="se", item="I5", status="进行中")
    r = append(env, role="pm", item="I5", part="澄清A", status="进行中")
    check("--part 落账成功并记下 part 字段", r.returncode == 0 and events(tmp)[-1].get("part") == "澄清A", out(r))
    r = run(env, "stale", "--hours", "0")
    check("子产物单独成行，显示为「工作项/子产物」", "I5/澄清A" in out(r) and "2 非终态项" in out(r), out(r))
    append(env, role="pm", item="I5", part="澄清A", status="完成")
    r = run(env, "stale", "--hours", "0")
    check("子产物「完成」只收它自己那一行，主线照常可见",
          "I5/澄清A" not in out(r) and "1 非终态项" in out(r) and "已收口" not in out(r), out(r))
    append(env, role="ui", item="I5", part="图标", status="进行中")
    append(env, role="se", item="I5", status="完成")
    r = run(env, "stale", "--hours", "0")
    check("主线「完成」：整项收口，没人回来置终态的子产物行一并折叠",
          r.returncode == 0 and "已收口" in out(r), out(r))


def t_part_owner_and_validation(tmp):
    env = mkenv(tmp)
    r = append(env, role="ui", item="I6", part="  ", status="进行中")
    check("--part 为空白时硬拒、不落账", r.returncode != 0 and not events(tmp), out(r))
    append(env, role="ui", item="I6", part="配色", status="阻塞", blocker_role="owner", blocker="等定色")
    r = run(env, "owner")
    check("待裁决清单按「工作项/子产物」列出", r.returncode == 1 and "I6/配色" in out(r), out(r))


# ───────────────────────── 提交号硬拒 R1–R3 ─────────────────────────

def _git(d, *a):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, check=True).stdout.strip()


def _repo(tmp):
    """临时 git 仓库：提交 A 在主线，提交 B 只在分支 lane/x（挂成工作树）。返回 (env, A, B)。"""
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    open(os.path.join(repo, "a.txt"), "w").write("a")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "A")
    a = _git(repo, "rev-parse", "HEAD")
    wt = os.path.join(tmp, "wt")
    _git(repo, "worktree", "add", "-q", "-b", "lane/x", wt)
    open(os.path.join(wt, "b.txt"), "w").write("b")
    _git(wt, "add", ".")
    _git(wt, "commit", "-qm", "B")
    b = _git(wt, "rev-parse", "HEAD")
    led = os.path.join(tmp, "led")
    os.makedirs(led)
    env = mkenv(led)
    env["TEAM_LEDGER_GIT_DIR"] = repo
    return env, a, b


def t_r1_review_needs_commit_and_path(tmp):
    env, a, _ = _repo(tmp)
    r = append(env, role="se", item="w", status="待评审", to="sa", note=f"{a[:8]} docs/x.md")
    check("R1 提交号＋路径 → 通过", r.returncode == 0, out(r))
    r = append(env, role="se", item="w", status="待评审", to="sa", note=f"{a[:8]}")
    check("R1 只有提交号没路径 → 拒", r.returncode != 0 and "路径" in out(r), out(r))
    r = append(env, role="se", item="w", status="待评审", to="sa", note="deadbee docs/x.md")
    check("R1 提交号不存在 → 拒", r.returncode != 0 and "不存在" in out(r), out(r))


def t_r1_sa_exempt(tmp):
    env, _, _ = _repo(tmp)
    r = append(env, role="sa", item="w", status="待评审", to="pm", note="合评输入就绪")
    check("R1 SA 不适用", r.returncode == 0, out(r))


def t_r2_done_needs_commit(tmp):
    env, a, _ = _repo(tmp)
    r = append(env, role="qa", item="w", status="完成", note="报告已出")
    check("R2 完成无提交号 → 拒", r.returncode != 0 and "--no-commit" in out(r), out(r))
    r = append(env, role="qa", item="w", status="完成", note=f"报告 {a[:10]}")
    check("R2 带存在的提交号 → 通过", r.returncode == 0, out(r))
    r = append(env, role="qa", item="w2", status="完成", no_commit="只读排查")
    check("R2 --no-commit 写理由 → 通过", r.returncode == 0, out(r))
    check("事件记下 no_commit", events(env["TEAM_LEDGER_DIR"])[-1].get("no_commit") == "只读排查",
          json.dumps(events(env["TEAM_LEDGER_DIR"])[-1], ensure_ascii=False))
    r = append(env, role="pm", item="w3", status="交接", to="sa", note="已澄清")
    check("R2 交接无提交号 → 拒", r.returncode != 0, out(r))


def t_r2_no_commit_blank_rejected(tmp):
    env, _, _ = _repo(tmp)
    r = append(env, role="qa", item="w", status="完成", no_commit="  ")
    check("R2 --no-commit 空白 → 拒", r.returncode != 0, out(r))


def t_r3_dev_dispatch_needs_base(tmp):
    env, a, _ = _repo(tmp)
    r = append(env, role="sa", item="w1", status="交接", to="se", phase="dev", note="派开发")
    check("R3 首次开发派活无 --base → 拒", r.returncode != 0 and "--base" in out(r), out(r))
    r = append(env, role="sa", item="w1", status="交接", to="se", phase="dev", base=a[:8], note="派开发")
    check("R3 带存在的 --base → 通过", r.returncode == 0, out(r))
    check("事件记下 base", events(env["TEAM_LEDGER_DIR"])[-1].get("base") == a[:8],
          json.dumps(events(env["TEAM_LEDGER_DIR"])[-1], ensure_ascii=False))
    r = append(env, role="sa", item="w1", status="交接", to="se", phase="dev", note="返工")
    check("R3 同一(工作项,主线)再派不必再带 --base", r.returncode == 0, out(r))
    r = append(env, role="sa", item="w9", status="交接", to="se", phase="dev", base="deadbee", note="派开发")
    check("R3 --base 不存在 → 拒", r.returncode != 0 and "不存在" in out(r), out(r))


def t_r3_only_dev_phase(tmp):
    env, _, _ = _repo(tmp)
    r = append(env, role="sa", item="w", status="交接", to="se", phase="spec", note="写 spec")
    check("R3 非 dev 派活不要求 --base", r.returncode == 0, out(r))


def t_r3_per_part(tmp):
    env, a, _ = _repo(tmp)
    append(env, role="sa", item="w", status="交接", to="se", phase="dev", base=a[:8], note="主线")
    r = append(env, role="sa", item="w", part="b", status="交接", to="se", phase="dev", note="b 线")
    check("R3 子产物各自记起点：b 无 --base → 拒", r.returncode != 0 and "--base" in out(r), out(r))


def t_commit_on_lane_branch_counts(tmp):
    env, _, b = _repo(tmp)
    r = append(env, role="se", item="w", status="完成", note=f"线上提交 {b[:9]}")
    check("线分支上的提交算存在", r.returncode == 0, out(r))


def t_commit_check_unjudgeable_warns(tmp):
    led = os.path.join(tmp, "led")
    os.makedirs(led)
    env = mkenv(led)           # TEAM_LEDGER_GIT_DIR=led，不是 git 仓库
    r = append(env, role="se", item="w", status="完成", note="x")
    check("判不了只警告、照常落账", r.returncode == 0 and "判不了" in out(r), out(r))


def t_stale_shows_base(tmp):
    env, a, _ = _repo(tmp)
    append(env, role="sa", item="w", status="交接", to="se", phase="dev", base=a, note="派开发")
    append(env, role="se", item="w", status="进行中", phase="dev")
    r = run(env, "stale", "--hours", "0")
    check("stale 显示起点提交", f"起点 {a[:8]}" in out(r), out(r))


def t_commit_checked_in_ledger_repo(tmp):
    """提交号在账本所在仓库（主工作树）核对，不随调用方当前目录漂移。"""
    env0, a, _ = _repo(tmp)
    repo = env0["TEAM_LEDGER_GIT_DIR"]
    os.makedirs(os.path.join(repo, "skills", "team-ledger"))
    shutil.copy(LEDGER, os.path.join(repo, "skills", "team-ledger", "team-ledger.py"))
    script = os.path.join(repo, "skills", "team-ledger", "team-ledger.py")
    elsewhere = os.path.join(tmp, "elsewhere")
    os.makedirs(elsewhere)
    env = {k: v for k, v in env0.items() if k != "TEAM_LEDGER_GIT_DIR"}
    def ap(note):
        return subprocess.run([sys.executable, script, "append", "--role", "se", "--item", "w",
                               "--status", "完成", "--note", note], cwd=elsewhere, env=env,
                              capture_output=True, text=True)
    r = ap("abcdef1234 伪造")
    check("当前目录在仓库外：伪造提交号仍被拒", r.returncode != 0 and "不存在" in out(r), out(r))
    r = ap(f"{a[:8]} 真实")
    check("当前目录在仓库外：真实提交号通过", r.returncode == 0, out(r))


def t_r3_exempt_if_dev_dispatched_before(tmp):
    env, _, _ = _repo(tmp)
    led = env["TEAM_LEDGER_DIR"]
    with open(os.path.join(led, "ledger.jsonl"), "a", encoding="utf-8") as f:   # 升级前的存量派活：没有 base
        f.write(json.dumps({"ts": "2026-11-20 10:00", "role": "sa", "item": "old", "phase": "dev",
                            "status": "交接", "to": "se", "version": "v9.9.9"}, ensure_ascii=False) + "\n")
    r = append(env, role="sa", item="old", status="交接", to="se", phase="dev", note="返工再派")
    check("R3 升级前已派过开发的不要求补记 --base", r.returncode == 0, out(r))


def t_r2_error_hints_separator(tmp):
    env, _, _ = _repo(tmp)
    r = append(env, role="se", item="w", status="完成", note="fixed3e445987")
    check("R2 提交号贴着字母 → 报错提示用空格或标点隔开", r.returncode != 0 and "隔开" in out(r), out(r))


ALL = [t_append, t_version_missing, t_reject, t_successor_required, t_owner_successor,
       t_item_clash, t_item_clash_scope, t_force_new_item,
       t_stale_quiet, t_stale_hours0, t_stale_owner_tag, t_stale_bad_ts, t_bad_line,
       t_owner, t_owner_via_to, t_handoff_to_owner_warns, t_owner_closed, t_concurrent,
       t_removed_subcommands, t_removed_anchor_flags, t_no_md,
       t_ui_phase_alias, t_utc_offset,
       t_handoff_does_not_fold, t_complete_still_folds, t_part_rows, t_part_owner_and_validation,
       t_r1_review_needs_commit_and_path, t_r1_sa_exempt, t_r2_done_needs_commit,
       t_r2_no_commit_blank_rejected, t_r3_dev_dispatch_needs_base, t_r3_only_dev_phase,
       t_r3_per_part, t_commit_on_lane_branch_counts, t_commit_check_unjudgeable_warns,
       t_stale_shows_base, t_commit_checked_in_ledger_repo, t_r3_exempt_if_dev_dispatched_before,
       t_r2_error_hints_separator]


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

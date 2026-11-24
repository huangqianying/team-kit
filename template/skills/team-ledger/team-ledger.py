#!/usr/bin/env python3
"""团队协作状态账本（三条命令）。

事实源 = 追加式事件流 `.team-ledger/ledger.jsonl`（每次落账一行，`flock` + `O_APPEND` 原子）。

  team-ledger.py append --role se --item X --status 进行中 [--phase dev] [--round N]
                   [--decision APPROVED|CR] [--review 路径]
                   [--to pm|ui|se|qa|sa|owner] [--blocker-role ...] [--blocker ...]
                   [--note ...] [--version <版本>|_infra]
  team-ledger.py stale [--hours N]    # 非终态且停滞 ≥ N 小时；--hours 0 = 全部非终态（当前态视图）
  team-ledger.py owner                # 卡在产品负责人手上、只能等人的项

**不要往回加这些命令**：`verify-artifact` / `verify-candidate` / `show` / `render` /
`owed` / `items` / `archive` / `set-version` / `log`。不要它们的理由见同目录 `DESIGN.md`，
**不要重新发明**。

射程、形态与字段约定见同目录 `DESIGN.md`。
"""
import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

ROLES = {"pm", "sa", "se", "qa", "ui"}  # ui：Web UI 原型，见契约「角色」
STATUSES = {"进行中", "待评审", "评审中", "阻塞", "完成", "交接"}
# phase 锚定契约「标准链路」的各阶段/步骤，确保「走到哪一步」可统计
PHASES = {"requirement", "design", "ui-design", "ui-proto", "spec", "plan",
          "dev", "ui-review", "test-design", "test-case", "test", "accept",
          "review", "deploy"}
# ui-proto：阶段 1 的 UI Web 原型。
# ui-design：存量账本行可能锚在它上面，保留以兼容，不要删。
DECISIONS = {"APPROVED", "CR"}
TERMINAL = {"完成", "交接"}
# 能让整个工作项收口的只有「完成」：「交接」只是一棒传了出去，整件事未必结束
# （如 PM 澄清完交回、主线 SE 仍在跑）。按「交接」收口会把主线的「进行中」一并折叠掉。
ITEM_CLOSING = {"完成"}
# 「球在别人半场」的状态：落账只记接续方、不派活，棒由 SA 读账本后主动派出——
# 不指定接续方，SA 就看不出这一棒该给谁，等于掉棒。
PENDING_STATUSES = {"交接", "待评审", "阻塞"}
OWNER_ROLE = "owner"               # 产品负责人：不是 subagent，只打标记进待裁决清单
# `_` 前缀 = sentinel 版本：无版本归属，常驻活跃。`_infra`（基建）属此类。
INFRA_VERSION = "_infra"

# 输入归一：契约中文门名 → 规范 slug
PHASE_ALIAS = {
    "需求": "requirement",
    "设计": "design", "系统设计": "design",
    # UI 的中文门名一律归到现行的 ui-proto（UI 只做 Web 原型）；ui-design 只为兼容存量行，须显式写 slug
    "UI设计": "ui-proto", "ui设计": "ui-proto", "界面设计": "ui-proto",
    "UI原型": "ui-proto", "ui原型": "ui-proto", "原型": "ui-proto",
    "UI走查": "ui-review", "ui走查": "ui-review", "界面走查": "ui-review",
    "测试设计": "test-design",
    "用例": "test-case", "测试用例": "test-case",
    "测试": "test", "qa": "test",
    "验收": "accept",
    "开发": "dev", "development": "dev", "implementation": "dev",
    "部署": "deploy", "deployment": "deploy",
    "评审": "review",
}


def _norm_phase(p):
    """中文门名 / 脏值 → 规范 slug；已是规范值或空则原样返回。"""
    return PHASE_ALIAS.get(p, p) if p else p


# `realpath` 而非 `abspath`：`.claude/skills` 是指向 `skills/` 的软链，两条路径都会被用来调用本脚本。
# 用 abspath 时 `.claude/skills/team-ledger/team-ledger.py` 要往上数 4 层、`skills/team-ledger/team-ledger.py` 只需 3 层，
# 写死任一层数都会让另一条调用路径的 _REPO 落错目录（只在 git 解析失败的回落路径上生效，不易察觉）。
# realpath 先解开软链，两条调用路径算出同一个仓库根。
_SELF = os.path.realpath(__file__)


def _resolve_common_worktree():
    """账本必须落唯一主工作树，不随调用者所在 worktree 漂移。

    git worktree 共享同一对象库，但 `.team-ledger/` 是 gitignore 的工作区目录、每棵 worktree 各一份；
    若按脚本所在 worktree（`__file__`）定位，agent 从各自 worktree 落账就分叉成多本账。
    故解析 git common-dir（全体 worktree 共享的那个 .git）的父目录 = 主工作树根。
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=os.path.dirname(_SELF),
            capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    common = out.stdout.strip()
    return os.path.dirname(common) if common else None  # <主工作树>/.git → <主工作树>


_REPO = os.path.dirname(os.path.dirname(os.path.dirname(_SELF)))   # skills/team-ledger/x.py → 仓库根
_LEDGER_ROOT = _resolve_common_worktree() or _REPO
LEDGER_DIR = os.environ.get("TEAM_LEDGER_DIR") or os.path.join(_LEDGER_ROOT, ".team-ledger")
EVENTS = os.path.join(LEDGER_DIR, "ledger.jsonl")
LOCK = os.path.join(LEDGER_DIR, "ledger.lock")
# 版本真值源：受 git 跟踪。`.team-ledger/` 整个被 gitignore，版本号放那里只存在于本机。
SYSVER = os.environ.get("TEAM_LEDGER_SYSTEM_VERSION") or os.path.join(
    LEDGER_DIR if os.environ.get("TEAM_LEDGER_DIR") else _LEDGER_ROOT, "system-version.json")

# 账本 ts 是不带时区的本地时间字符串，统一按一个固定 UTC 偏移写和读。
# 默认 UTC+8；工程不在东八区时设 TEAM_LEDGER_UTC_OFFSET（小时，可带小数，如 0 / -5 / 5.5）。
# 注意：改偏移会改变**存量行**的解读（停滞时长整体平移），一个账本从头到尾只用一个偏移。
def _ledger_tz():
    raw = os.environ.get("TEAM_LEDGER_UTC_OFFSET", "8")
    try:
        hours = float(raw)
    except ValueError:
        hours = None
    if hours is None or not -12 <= hours <= 14:
        sys.exit(f"[team-ledger] TEAM_LEDGER_UTC_OFFSET 不合法：{raw!r}（须是 -12 到 14 之间的小时数）")
    return timezone(timedelta(hours=hours))


CST = _ledger_tz()


def _now():
    return datetime.now(CST).strftime("%Y-%m-%d %H:%M")


def _hours_since(ts):
    """距今小时数；ts 不可解析返回 None（判不了 ≠ 没停滞）。"""
    try:
        t = datetime.strptime(ts, "%Y-%m-%d %H:%M").replace(tzinfo=CST)
    except (TypeError, ValueError):
        return None
    return (datetime.now(CST) - t).total_seconds() / 3600


@contextmanager
def _locked():
    """整体互斥锁：序列化并发 append，防丢事件。"""
    os.makedirs(LEDGER_DIR, exist_ok=True)
    fd = os.open(LOCK, os.O_WRONLY | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _read_events():
    if not os.path.exists(EVENTS):
        return []
    out = []
    with open(EVENTS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # 容错：坏行跳过，不阻塞读账
    return out


def _current(events):
    """每个 (role, item, part) 取最新事件 = 当前态；没有 part 的是主线，part 为空串。"""
    latest = {}
    for e in events:
        latest[(e.get("role"), e.get("item"), e.get("part") or "")] = e
    return latest


def _label(item, part):
    """显示名：子产物行显示为「工作项/子产物」。"""
    return f"{item}/{part}" if part else item


def _closed_items(events):
    """已收口的工作项：该 item **主线**的最新一条事件为「完成」。

    收口语义落在 item 上，不落在行上 —— 行按 `(role, item, part)` 独立存活，而「完成」通常
    只由收口方落一行，被评审方那一行会一直停在 `待评审`。按行判会把它当成停滞。
    只在主线最新事件为「完成」时折叠（含该项下的子产物行）：重新开工（完成后再落非终态）即恢复逐行可见。
    「交接」不收口（见 ITEM_CLOSING）；带 `--part` 的子产物事件只管自己那一行，不参与整项收口。
    """
    last = {}
    for e in events:
        if e.get("item") and not e.get("part"):
            last[e["item"]] = e
    return {i for i, e in last.items() if e.get("status") in ITEM_CLOSING}


def _item_key(item):
    """工作项归一键：大小写 / 空白 / 连字符 / 下划线 / 全角差异不算不同工作项。

    只做**确定性**归一——中英互译、增删词这类语义重复判不了（实测真实重复项
    difflib 相似度 0.49，而合法的不同工作项高达 0.90，模糊阈值必然误伤）。
    那一类靠契约：工作项标识由派活方在 ask 里指定，接活方原样沿用。
    """
    s = unicodedata.normalize("NFKC", item or "").lower()
    return re.sub(r"[\s\-_·:：/]+", "", s)


def _existing_items(events, role):
    """该 role 已有的工作项原名，按最近出现排序。"""
    out = []
    for e in events:
        if e.get("role") == role and e.get("item") not in out:
            out.append(e.get("item"))
    return out[::-1]


def _current_version():
    """版本取自真值源 `system-version.json`；读不出就落 `_infra` 并告警。"""
    try:
        with open(SYSVER, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and str(d.get("version", "")).strip():
            return str(d["version"]).strip()
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError) as e:
        print(f"[team-ledger] ⚠️ system-version.json 读不出（{e}）——本次按 {INFRA_VERSION} 落账，"
              f"版本 tag 不可信。", file=sys.stderr)
        return INFRA_VERSION
    return INFRA_VERSION


# ───── 提交号核对（R1–R3）：落账引用的提交必须真实存在 ─────
ARTIFACT_ROLES = {"pm", "ui", "se", "qa"}          # R1/R2 只管产出角色；SA 的登记、裁定、合入不在此列
_SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{7,40}(?![0-9a-fA-F])")
_PATH_RE = re.compile(
    r"[\w\u4e00-\u9fff.\-]+/[\w\u4e00-\u9fff./\-]*"
    r"|[\w\u4e00-\u9fff\-]+\.(?:md|py|java|ts|vue|sql|json|sh|yml|yaml|toml|html|js|css|txt|jsonl)\b")


def _shas(note):
    return [m.lower() for m in _SHA_RE.findall(note or "")]


def _has_path(note):
    return bool(_PATH_RE.search(note or ""))


def _git_repo():
    """提交号在账本所在仓库（主工作树）核对，不随调用方当前目录漂移；
    各工作树共用对象库，线分支上的提交也查得到。TEAM_LEDGER_GIT_DIR 可覆盖（测试用）。"""
    return os.environ.get("TEAM_LEDGER_GIT_DIR") or _LEDGER_ROOT


def _repo_judgeable(repo):
    """仓库能不能用来核提交号：是 git 仓库且 git 可用。"""
    try:
        return subprocess.run(["git", "-C", repo, "rev-parse", "--git-dir"],
                              capture_output=True, text=True, timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _commit_exists(sha, repo):
    """True/False；None = 判不了（不是 git 仓库、没有 git）。判不了 ≠ 不存在。"""
    if not _repo_judgeable(repo):
        return None
    try:
        r = subprocess.run(["git", "-C", repo, "cat-file", "-e", f"{sha}^{{commit}}"],
                           capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return None


def _any_commit_exists(shas, repo):
    """有一个存在即 True；全不存在 False；判不了 None。"""
    if not _repo_judgeable(repo):
        return None
    if not shas:
        return False
    results = [_commit_exists(s, repo) for s in shas]
    if any(x is True for x in results):
        return True
    if any(x is None for x in results):
        return None
    return False


def _warn_unjudgeable(what):
    print(f"[team-ledger] 警告：{what}判不了（{_git_repo()} 不是 git 仓库或 git 不可用），本次照常落账", file=sys.stderr)


def cmd_append(a):
    if a.role not in ROLES:
        sys.exit(f"role 非法：{a.role}（须 ∈ {sorted(ROLES)}）")
    if a.status not in STATUSES:
        sys.exit(f"status 非法：{a.status}（须 ∈ {sorted(STATUSES)}）")

    # 非终态 = 球在别人半场。落账只记接续方、不派活；SA 靠 stale 读出待派的棒。
    successor, flag = ("", "")
    if a.status in PENDING_STATUSES:
        successor, flag = ((a.blocker_role, "--blocker-role") if a.status == "阻塞"
                           else (a.to, "--to"))
        if not successor:
            owner_hint = (f"交接是终态，写 --to {OWNER_ROLE} 也不进待裁决清单、不进 stale；"
                          f"要等产品负责人处理，改落 `阻塞 --blocker-role {OWNER_ROLE}` 或 `待评审 --to {OWNER_ROLE}`。"
                          if a.status == "交接" else
                          f"接续方是产品负责人（不是 subagent）时写 {flag} {OWNER_ROLE}，"
                          f"该项会进待裁决清单（`team-ledger.py owner`）。")
            sys.exit(f"status={a.status} 必须用 {flag} 指定接续方——"
                     f"落账不派活，接续方是给 SA 看的状态标记；不写 SA 就不知道这棒该派给谁。\n{owner_hint}")
        if successor != OWNER_ROLE and successor not in ROLES:
            sys.exit(f"{flag} 取值非法：{successor}（须 ∈ {sorted(ROLES)} 或 {OWNER_ROLE}）")
        if a.status == "交接" and successor == OWNER_ROLE:
            print(f"[team-ledger] 警告：交接是终态，交接 --to {OWNER_ROLE} 不进待裁决清单、不进 stale，"
                  f"负责人和 SA 都不会再看到它。要等负责人处理（验收、裁定），"
                  f"改落 `阻塞 --blocker-role {OWNER_ROLE}` 或 `待评审 --to {OWNER_ROLE}`。本次照常落账", file=sys.stderr)
    phase = _norm_phase(a.phase)
    if phase and phase not in PHASES:
        sys.exit(f"phase 非法：{a.phase}（须 ∈ 链路阶段 {sorted(PHASES)}；中文阶段名会自动归一）")
    if a.decision and a.decision not in DECISIONS:
        sys.exit(f"decision 非法：{a.decision}（须 ∈ {sorted(DECISIONS)}）")
    if a.status == "阻塞" and not a.blocker:
        sys.exit("status=阻塞 时必须给 --blocker（卡在谁/什么）")
    part = (a.part or "").strip()
    if a.part is not None and not part:
        sys.exit("--part 不能为空白（省略即为主线）")
    version = a.version.strip() if a.version else ""
    if a.version and not version:
        sys.exit("--version 不能为空白（省略即用 system-version.json 的版本）")
    no_commit = (a.no_commit or "").strip()
    if a.no_commit is not None and not no_commit:
        sys.exit("--no-commit 必须写理由（这次为什么没有产物提交）")
    repo = _git_repo()
    if a.role in ARTIFACT_ROLES and a.status in ("待评审", "完成", "交接") and not no_commit:
        found = _any_commit_exists(_shas(a.note), repo)
        rule = "R1" if a.status == "待评审" else "R2"
        if found is None:
            _warn_unjudgeable("提交号是否存在")
        elif not found:
            sys.exit(f"{rule}：{a.role} 落「{a.status}」须在 --note 里写一个仓库里存在的提交号"
                     f"（{'没找到提交号' if not _shas(a.note) else '提交号在仓库里不存在'}）。\n"
                     f"提交号前后请用空格或标点隔开（如 `fixed 3e445987`），紧贴字母会被连成一串。\n"
                     f"确实没有产物（只读排查、运维、咨询）时用 --no-commit '理由' 写明。")
        if a.status == "待评审" and found is True and not _has_path(a.note):
            sys.exit("R1：待评审须在 --note 里指认被评产物的路径（提交号之外再写一个路径，如 docs/x.md）。\n"
                     "确实没有产物时用 --no-commit '理由' 写明。")
    base = (a.base or "").strip()
    if a.base is not None:
        if not _SHA_RE.fullmatch(base):
            sys.exit(f"--base 须是提交号（7–40 位十六进制）：{a.base}")
        ok = _commit_exists(base.lower(), repo)
        if ok is None:
            _warn_unjudgeable("起点提交是否存在")
        elif not ok:
            sys.exit(f"--base 提交在仓库里不存在：{base}")

    with _locked():
        _events = _read_events()
    _existing = _existing_items(_events, a.role)
    if a.force_new_item and not (a.note or "").strip():
        sys.exit("--force-new-item 必须在 --note 里写明理由——"
                 "绕过同名硬拒后，账本上看不出这次是有意另起还是手滑。")
    if not a.force_new_item:
        _key = _item_key(a.item)
        _clash = next((x for x in _existing if _item_key(x) == _key and x != a.item), None)
        if _clash:
            sys.exit(
                f"工作项同事异名：{a.role} 已有「{_clash}」，本次写成「{a.item}」。\n"
                f"当前态按 (role,item) 归并——换个写法就会拆成两行，其中一行永远收不了口。\n"
                f"**一个 item ＝ 一条独立的评审线（契约「附：状态账本」）**，"
                f"拆成两行等于把一条线记成两条，其中一条没人认领。\n"
                f"请原样沿用「{_clash}」；确属另一件事则加 --force-new-item。")

    if (a.role == "sa" and a.status == "交接" and a.to == "se" and phase == "dev" and not base
            and not any(e.get("item") == a.item and (e.get("part") or "") == part
                        and (e.get("base") or (e.get("role") == "sa" and e.get("status") == "交接"
                                               and e.get("to") == "se" and e.get("phase") == "dev"))
                        for e in _events)):    # 已记过起点，或升级前已派过开发（不追溯补记）
        sys.exit(f"R3：给 SE 派开发活（--phase dev）须带 --base <起点提交>——"
                 f"「{_label(a.item, part)}」还没记过起点提交。起点 = SE 开工所基于的集成分支（或线）提交，"
                 f"「先失败再通过」和旧失败分类都以它为准（docs/rules/派活与交付.md「一」）。")

    ev = {"ts": _now(), "role": a.role, "item": a.item, "phase": phase,
          "status": a.status, "version": version or _current_version()}
    if part:
        ev["part"] = part                 # 子产物：只管自己那一行，不参与整项收口
    if a.force_new_item:
        ev["forced_new_item"] = True      # 留痕：这条是显式绕过同名硬拒建的
    if successor:
        ev["blocker_role" if a.status == "阻塞" else "to"] = successor
    if a.round is not None:
        ev["round"] = a.round
    for k, v in (("decision", a.decision), ("review", a.review),
                 ("blocker", a.blocker), ("note", a.note),
                 ("base", base), ("no_commit", no_commit)):
        if v:
            ev[k] = v
    line = json.dumps(ev, ensure_ascii=False) + "\n"
    with _locked():
        fd = os.open(EVENTS, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    print(f"[team-ledger] {ev['role']} · {_label(ev['item'], part)} · {ev['status']} @ {ev['ts']}")
    if a.item not in _existing and _existing:
        _show = "、".join(_existing[:5])
        _more = f"（另有 {len(_existing) - 5} 项）" if len(_existing) > 5 else ""
        print(f"[team-ledger] 新建工作项。{a.role} 现有：{_show}{_more}"
              f"\n         若这其实是上面某项的另一种叫法，请改用原名——同事异名会拆成两行。")


def cmd_stale(a):
    """非终态且停滞 ≥ --hours 的工作项 —— 值守巡检用，也是唯一的当前态视图。

    `--hours 0` 列出**全部非终态项**，即当前态视图：现算现打，不落第二份文件。
    只看非终态：`完成`/`交接` 已经把球交出去了，停着不算停滞。
    退出码：0=确无停滞  1=有停滞  2=有项判不了（ts 不可解析），不能报全清。
    """
    with _locked():
        events = _read_events()
    closed = _closed_items(events)
    bases = {}
    for e in events:
        if e.get("base"):
            bases[(e.get("item"), e.get("part") or "")] = e["base"]
    rows, unknown, folded = [], [], 0
    for (role, item, part), e in _current(events).items():
        if e.get("status") in TERMINAL:
            continue
        if item in closed:
            folded += 1          # item 已收口，这一行只是没人回来置终态
            continue
        age = _hours_since(e.get("ts", ""))
        if age is None:
            unknown.append((role, _label(item, part), e))
        elif age >= a.hours:
            rows.append((age, role, _label(item, part), e))

    def _tail(e):
        """接续方 ＋ 卡点：非终态行的意义全在「棒在谁手里」。"""
        who = _successor(e)
        bits = []
        if who:
            bits.append("→ OWNER（等人裁决，不派 subagent）" if who == OWNER_ROLE
                        else f"→ {who.upper()}")
        if e.get("blocker"):
            bits.append(f"卡在 {e['blocker']}")
        if e.get("round") not in (None, ""):
            bits.append(f"r{e['round']}")
        b = bases.get((e.get("item"), e.get("part") or ""))
        if b:
            bits.append(f"起点 {b[:8]}")
        return ("  " + " · ".join(bits)) if bits else ""

    if rows:
        rows.sort(key=lambda r: r[:3], reverse=True)
        label = "非终态项" if a.hours == 0 else f"项停滞 ≥ {a.hours}h"
        print(f"[team-ledger] {len(rows)} {label}：")
        for age, role, item, e in rows:
            print(f"  {age:5.1f}h  {role:3} {e.get('status','')}  {item}{_tail(e)}")
    if unknown:
        print(f"[team-ledger] {len(unknown)} 项无法判定（ts 不可解析，未必没停滞）：")
        for role, item, e in sorted(unknown, key=lambda r: r[:2]):
            print(f"    ts={e.get('ts','')!r}  {role:3} {e.get('status','')}  {item}{_tail(e)}")
    if folded:
        print(f"[team-ledger] 另有 {folded} 行归属于已收口的工作项，不计入停滞")
    if rows:
        sys.exit(1)
    if unknown:
        sys.exit(2)
    print(f"[team-ledger] 无停滞项（阈值 {a.hours}h）")


def _successor(e):
    """接续方：阻塞看 blocker_role，其余看 to（与 append 的校验口径一致）。"""
    return e.get("blocker_role") if e.get("status") == "阻塞" else e.get("to")


def cmd_owner(a):
    """待裁决清单：当前仍卡在产品负责人手上的项。

    接续方是产品负责人（`阻塞 --blocker-role owner`，或其他非终态 `--to owner`，口径同 stale 的「→ OWNER」）：
    不是 subagent，只能等人。
    只列**当前态**仍非终态者——已收口的不再列，否则清单会被历史项淹掉。

    退出码：0=无待裁决  1=有待裁决
    """
    with _locked():
        events = _read_events()
    closed = _closed_items(events)
    rows = [(e.get("ts", ""), role, _label(item, part), e)
            for (role, item, part), e in _current(events).items()
            if _successor(e) == OWNER_ROLE
            and e.get("status") not in TERMINAL and item not in closed]
    if not rows:
        print("[team-ledger] 无待产品负责人裁决的项")
        return
    rows.sort(key=lambda r: r[:3])
    print(f"[team-ledger] {len(rows)} 项待你裁决——这些项的接续方是产品负责人，不是 subagent，只能等人：")
    for ts, role, item, e in rows:
        age = _hours_since(ts)
        aged = f"（挂 {age:.0f}h）" if age is not None else ""
        print(f"  {ts}  {role}  {item}{aged}")
        if e.get("blocker"):
            print(f"      卡点：{e['blocker']}")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="团队协作状态账本（append / stale / owner）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    apd = sub.add_parser("append", help="追加一条状态变更事件")
    apd.add_argument("--role", required=True)
    apd.add_argument("--item", required=True)
    apd.add_argument("--part", default=None,
                     help="子产物名：同一工作项内并行推进的子产物（如主线开发时 PM 澄清其中一份）。"
                          "只管自己那一行，交接 / 完成都不让整项收口；stale 显示为「工作项/子产物」")
    apd.add_argument("--status", required=True)
    apd.add_argument("--phase", default="")
    apd.add_argument("--round", type=int, default=None,
                     help="评审轮次。契约「评审与合入」：每份产物最多一轮评审（封顶 1）")
    apd.add_argument("--decision", default="", help="APPROVED | CR")
    apd.add_argument("--review", default="", help="存量评审记录索引；新工作项不用（契约「评审与合入」：结论只落账本）")
    apd.add_argument("--to", default="", help="交接/待评审 的接续方")
    apd.add_argument("--blocker-role", dest="blocker_role", default="",
                     help="阻塞 的被卡方；写 owner 则进待裁决清单")
    apd.add_argument("--blocker", default="")
    apd.add_argument("--note", default="")
    apd.add_argument("--base", default=None, help="起点提交：给 SE 派开发活（--phase dev）首次必填")
    apd.add_argument("--no-commit", dest="no_commit", default=None,
                     help="没有产物提交时写明理由（pm/ui/se/qa 落 待评审/完成/交接 时替代提交号）")
    apd.add_argument("--version", default="", help="省略即用 system-version.json 的版本")
    apd.add_argument("--force-new-item", dest="force_new_item", action="store_true",
                     help="绕过同名硬拒（须同时给 --note 理由）")
    apd.set_defaults(fn=cmd_append)

    stp = sub.add_parser("stale", help="非终态且停滞的项；--hours 0 = 全部非终态（当前态）")
    stp.add_argument("--hours", type=float, default=24.0)
    stp.set_defaults(fn=cmd_stale)

    sub.add_parser("owner", help="待产品负责人裁决的项").set_defaults(fn=cmd_owner)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

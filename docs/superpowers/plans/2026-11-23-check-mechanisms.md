# 检查机制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现第二轮检查机制，发 v0.10.0 并同步到 vista、prism。包括三部分：账本对三类不合格落账硬拒（R1–R3）；Claude Code 与 Codex 的三个只提醒钩子（H1–H3）；SA 手动运行的 `team-check` 检查命令。

**Architecture:**
- 账本规则加在 `team-ledger.py` 的 `append` 里。
- 钩子与检查命令放进新的内核 skill `skills/team-check/`：
  - `hook.py`：两个宿主共用的唯一钩子入口；
  - `team-check.py`：手动检查命令；
  - 两者共用 `checks.py` 里的函数。
- 两个宿主的配置只写入口命令，不写逻辑：`.claude/settings.json` 加 `hooks`；新增 `.codex/hooks.json`。

**Tech Stack:** Python 3 标准库、git、Claude Code 2.1.330 与 Codex 0.167.0 的钩子、中文 Markdown 规则。

**Spec:** `docs/superpowers/specs/2026-11-23-check-mechanisms-design.md`（方案 A；判断 C1–C11）。

## Global Constraints

- **钩子只提醒、绝不拦截**：
  - 任何异常都捕获，退出码一律 0；
  - 不用写文件前的钩子；不返回 `decision: block`、`permissionDecision: deny`；
  - 配置里每个钩子的 `timeout` 为 10 秒。
- **注入的输出格式**：`{"hookSpecificOutput": {"hookEventName": <事件名>, "additionalContext": <文本>}}`。不需要注入时不输出任何内容。
- **H1 注入总长不超过 2,000 字符。** H2 工程检查的输出截取前 1,500 字符，执行超时 8 秒。
- **提交号正则**：`(?<![0-9a-fA-F])[0-9a-fA-F]{7,40}(?![0-9a-fA-F])`。
- **「存在」的判定**：`git -C <仓库> cat-file -e <sha>^{commit}`。判不了（不是 git 仓库、没有 git）时只警告、不拒（C3）。
- **路径的判定**：含 `/` 的片段，或者以 `.md .py .java .ts .vue .sql .json .sh .yml .yaml .toml .html .js .css .txt .jsonl` 结尾的文件名。
- **R1、R2 只对角色 `pm`、`ui`、`se`、`qa` 生效**，SA 不适用（C9）。
- **R3 的条件**：`--role sa --status 交接 --to se --phase dev`，且这个（工作项，子产物）还没有记过 `base`。
- **新参数**：
  - `--base <sha>` 记进事件的 `base` 字段；
  - `--no-commit '<理由>'`：理由为空白时拒绝；记进事件的 `no_commit` 字段。
- **H3 只认** `agent_type` ∈ {pm, ui, se, qa}。
- **钩子状态文件**放在账本目录（`TEAM_LEDGER_DIR`，或主工作树的 `.team-ledger/`）下的 `hooks/`。不入库。
- **工程检查挂载点**：只解析 `.githooks/project.conf` 里 `CHECK_AFTER_EDIT=` 这一行（`shlex.split`），不 source 整个文件。
- **新增内核文件**：`.codex/hooks.json`；目录 `skills/team-check/` 整个进 `MANIFEST`。
- **版本号** v0.10.0。
- **提交与推送**：
  - kit 内一律带路径提交；只推送 team-kit；
  - 工程里只做带路径的本地提交，不推送；
  - 推送和同步之前先做整体审阅。

## Review Focus

1. **工程的账本目录不在 git 仓库里，或者 `git` 不可用。** 预期：R1–R3 只警告、照常落账。测试 `test_commit_check_unjudgeable_warns`（Task 2）。
2. **在并行线工作树里落账，提交只存在于线分支上。** 预期：提交存在的判定在调用方所在仓库进行；各工作树共用同一个对象库，线分支上的提交能查到，判为存在。测试 `test_commit_on_lane_branch_counts`（Task 2）。
3. **钩子收到空 stdin、非法 JSON，或者缺字段。** 预期：退出 0、不输出、不留下半截状态文件。测试 `test_hook_bad_input_is_silent`（Task 4）。
4. **H1 在一个没装 kit 的仓库里运行**（例如 team-kit 自身）。预期：什么都不注入。测试 `test_session_start_outside_kit_project`（Task 4）。
5. **同一会话里反复改同一个内核文件。** 预期：只提醒一次。测试 `test_kernel_edit_warns_once_per_session`（Task 4）。

---

### Task 1：实测两个宿主的钩子输入（一次性试探，不留代码）

**Files:**
- Modify: `docs/superpowers/specs/2026-11-23-check-mechanisms-design.md`：文末加「附录 A：钩子实测」。

- [ ] **Step 1：搭临时仓库**

在 scratchpad 建一个 git 仓库：
- 一个打印钩子：把 stdin 原样追加到仓库外的日志文件；
- 两份配置：`.claude/settings.json` 和 `.codex/hooks.json`，挂 `SessionStart`、`PostToolUse`（Claude matcher `Write|Edit`；Codex matcher 分别试 `apply_patch` 和 `Edit|Write`）、`SubagentStart`、`SubagentStop`；
- 两个宿主各定义一个名为 `se` 的子代理：Claude `.claude/agents/se.md`，Codex `[agents.se]`。

- [ ] **Step 2：分别跑一次 Claude Code 和 Codex 的非交互模式**

- Claude：`claude -p '...' --permission-mode bypassPermissions`；
- Codex：`codex exec`。Codex 在非交互模式下如果跳过未信任的钩子，就加 `--dangerously-bypass-hook-trust`，并在附录里写明。

两个宿主都做同样两件事：主会话写一个文件；派 `se` 子代理写另一个文件。

- [ ] **Step 3：把实测结论写进附录 A**

逐条回答：
- Codex 文件编辑的 `tool_name` 是什么，哪个 matcher 能命中，`tool_input` 里补丁文本的字段名和格式；
- 两个宿主在子代理里写文件时，输入有没有带 `agent_id`、`agent_type`，`agent_type` 的值是什么；
- 两个宿主的 `SessionStart` 输入带不带 `source` 字段，取值是什么；`SubagentStop` 输入带不带 `stop_hook_active`。

Expected：附录 A 每一问都有一条实测结论，并附日志中的一行输入为证。

- [ ] **Step 4：提交**

```bash
git commit -m "Design appendix: measured hook inputs on Claude Code and Codex" -- docs/superpowers/specs/2026-11-23-check-mechanisms-design.md
```

如果实测结果推翻了设计里的某条假设，在执行台账里记一条 Ruling，按最小改动调整 Task 4 的解析方式。

---

### Task 2：账本硬拒 R1–R3

**Files:**
- Modify: `template/skills/team-ledger/team-ledger.py`：`cmd_append`（第 232 行起）、参数（第 399–416 行）、`cmd_stale`（第 310 行起）
- Test: `template/skills/team-ledger/test_team_ledger.py`

**Interfaces:**
- Produces（Task 3、4 会用到）：
  - `_shas(note: str) -> list[str]`：note 里所有提交号，转成小写；
  - `_has_path(note: str) -> bool`；
  - `_commit_exists(sha: str, repo: str) -> bool | None`：`None` 表示判不了；
  - `_git_repo() -> str`：取环境变量 `TEAM_LEDGER_GIT_DIR`，没有就用 `os.getcwd()`；
  - 事件新字段 `base`、`no_commit`。

- [ ] **Step 1：让现有测试在不是 git 仓库的目录里运行**

把 `run()` 改成 `subprocess.run(..., cwd=tmp)`：`mkenv` 的临时目录作为 `cwd`，并设置 `TEAM_LEDGER_GIT_DIR=tmp`。这样现有用例的 note 不带提交号也不会被拒。

运行 `python3 template/skills/team-ledger/test_team_ledger.py`，Expected：全过（84 项）。

- [ ] **Step 2：写失败测试**（新增函数 `test_commit_rules()`，并在 `main` 里调用）

测试里自建临时 git 仓库：两个提交 `A`、`B`，`B` 在分支 `lane/x` 上，用 `git worktree add` 挂出来。`TEAM_LEDGER_GIT_DIR` 指向这个仓库。

| 用例 | 断言 |
|---|---|
| `test_r1_review_needs_commit_and_path` | `--role se --status 待评审 --to sa --note "A docs/x.md"` 成功；note 只写 `"A"` 时退出码 ≠ 0，输出含「路径」；note 写不存在的 `deadbee docs/x.md` 时退出码 ≠ 0，输出含「不存在」 |
| `test_r1_sa_exempt` | `--role sa --status 待评审 --to pm --note "合评输入就绪"` 成功 |
| `test_r2_done_needs_commit` | `--role qa --status 完成 --note "报告已出"` 退出码 ≠ 0；note 带 `A` 的提交号时成功；`--no-commit "只读排查"` 时成功，事件含 `no_commit` |
| `test_r2_no_commit_blank_rejected` | `--no-commit "  "` 退出码 ≠ 0 |
| `test_r3_dev_dispatch_needs_base` | `--role sa --status 交接 --to se --phase dev --item w1` 不带 `--base` 时拒，输出含「--base」；带 `--base A` 时成功，事件含 `base`；同一个（w1，主线）再派一次不带 `--base` 时成功 |
| `test_r3_only_dev_phase` | `--phase spec` 的派活不带 `--base` 时成功 |
| `test_r3_per_part` | w1 主线已经有 `base` 后，`--part b` 的开发派活不带 `--base` 时拒 |
| `test_commit_on_lane_branch_counts` | note 写 `B` 的提交号时 R2 通过 |
| `test_commit_check_unjudgeable_warns` | `TEAM_LEDGER_GIT_DIR` 指向一个不是 git 仓库的目录：`--role se --status 完成 --note "x"` 成功，输出含「判不了」 |
| `test_stale_shows_base` | 有 `base` 的工作项在 `stale --hours 0` 的输出里含 `起点 ` 加上 `A` 的前 8 位 |

- [ ] **Step 3：运行，看它失败**

运行同上。Expected：新用例全部 ✗，旧的 84 项仍然 ✓。

- [ ] **Step 4：实现**

- **参数**：加 `--base` 和 `--no-commit`（`dest="no_commit"`）。
- **校验顺序**：
  1. 放在现有校验之后、读取事件之前；
  2. R3 需要已有事件，等 `_read_events()` 之后再判。
- **判不了时**：同一次落账只打印一行警告，内容含「判不了」。
- **stale**：按（工作项，子产物）取最近一个带 `base` 的事件，在该行末尾追加 `· 起点 <sha[:8]>`。

- [ ] **Step 5：运行，看它全过，然后提交**

运行同上。Expected：全过，数量为 84 加新增的断言数。

```bash
git commit -m "Ledger: reject entries without real commits; record the start commit" -- template/skills/team-ledger/team-ledger.py template/skills/team-ledger/test_team_ledger.py
```

---

### Task 3：`team-check` 的检查函数与手动命令

**Files:**
- Create: `template/skills/team-check/checks.py`
- Create: `template/skills/team-check/team-check.py`
- Create: `template/skills/team-check/test_team_check.py`：沿用账本测试的 `check()` 写法，走子进程，用临时 git 仓库
- Modify: `MANIFEST`：在 `skills/team-ledger/` 之后加 `skills/team-check/`

**Interfaces:**
- Produces（`checks.py`）：
  - `changed_paths(repo: str, commits: list[str]) -> set[str]`：逐个执行 `git show --name-only --format= <c>`，取并集；
  - `out_of_scope(paths, allow: list[str], deny: list[str]) -> list[str]`：用 `fnmatch`；`dir/` 形式的模式按前缀匹配；
  - `migration_dir(repo: str) -> str | None`：读 `docs/rules/工程配置.md` 里以 `| 数据库迁移 |` 开头那一行的第一个反引号路径；
  - `flyway_dupes(path: str) -> dict[int, list[str]]`：按 `^V(\d+)__.*\.sql$` 取版本号；
  - `plan_missing(text: str) -> list[str]`：没有含「并行编排」的标题时返回 `["并行编排"]`；有的话，返回「线的划分」「合入顺序」中没出现的那几项；
  - `lanes(repo: str, events: list[dict]) -> tuple[list[str], list[str]]`，返回（多出，缺失）：
    - 已有的线 = `git for-each-ref refs/heads/lane/` 加上 `git worktree list --porcelain` 中的 `lane/*` 分支；
    - 登记的线 = 未收口工作项的 note 里匹配 `lane/[A-Za-z0-9][A-Za-z0-9._-]*` 的短名，排除 `lane/worktree`；
    - 未收口的判定复用账本的 `_closed_items` 口径：在 `checks.py` 里按同一规则重写，只看「完成」，不 import 账本脚本。
- `team-check.py`：子命令 `scope`、`migrations`、`plan`、`lanes`，参数与退出码照设计 §5.3。`lanes` 的账本路径按 `team-ledger.py` 的规则解析：`TEAM_LEDGER_DIR`，否则取主工作树。

- [ ] **Step 1：写失败测试**

| 用例 | 断言 |
|---|---|
| `test_scope` | 提交改了 `src/a.py` 和 `docs/b.md`，`--allow src/` 时退出码 1，输出含 `docs/b.md`；`--allow src/ docs/` 时退出码 0；`--deny docs/` 时退出码 1 |
| `test_migrations` | 目录里有 `V3__a.sql`、`V3__b.sql` 时退出码 1，输出含 `V3`；目录不存在时退出码 2 |
| `test_migration_dir_from_config` | 工程配置里写 `| 数据库迁移 | \`db/mig/\`（Flyway） |` 时，读出 `db/mig/` |
| `test_plan` | 有「## 并行编排」、缺「合入顺序」时退出码 1；三项都有时退出码 0；文件不存在时退出码 2 |
| `test_lanes` | 有分支 `lane/x`、账本没登记时，「多出」含 `lane/x`；未收口工作项登记了 `lane/y` 但分支不存在时，「缺失」含 `lane/y`；已收口工作项登记的 `lane/z` 不报；`lane/worktree` 不报 |

- [ ] **Step 2：运行，看它失败**

`python3 template/skills/team-check/test_team_check.py`，Expected：全部 ✗（模块不存在）。

- [ ] **Step 3：按 Interfaces 实现 `checks.py` 和 `team-check.py`**

- [ ] **Step 4：运行，看它全过；再跑 kit 测试，然后提交**

`python3 template/skills/team-check/test_team_check.py && python3 bin/test_kit.py`。Expected：两套都全过；kit 的安装测试已覆盖新目录。

```bash
git add -- template/skills/team-check
git commit -m "team-check: scope, migrations, plan and lanes checks" -- template/skills/team-check MANIFEST
```

---

### Task 4：钩子入口 `hook.py`

**Files:**
- Create: `template/skills/team-check/hook.py`
- Modify: `template/skills/team-check/test_team_check.py`

**Interfaces:**
- Consumes：Task 3 的 `lanes`；账本的 `stale --hours 0`、`owner` 通过子进程调用 `skills/team-ledger/team-ledger.py`。
- Produces：`python3 skills/team-check/hook.py <SessionStart|PostToolUse|SubagentStart|SubagentStop>`，stdin 是宿主的 JSON。
- 内部：`edited_paths(payload) -> list[str]`：
  - Claude 取 `tool_input.file_path`；
  - Codex 按附录 A 的结论解析补丁里的 `*** Add/Update/Delete File:` 行；
  - 取到的路径都转成相对工程根的路径。
- 工程根：`git rev-parse --show-toplevel`，在 `payload["cwd"]` 下执行，没有 `cwd` 就在当前目录下执行。

- [ ] **Step 1：写失败测试**（每条都用子进程把构造的 JSON 喂给 stdin，在临时工程里运行。临时工程是 git 仓库，有 `.team-kit.json`，`files` 里含 `AGENTS.md`，账本放在临时目录）

| 用例 | 断言 |
|---|---|
| `test_hook_bad_input_is_silent` | stdin 为空、为 `{`、或为缺字段的 JSON 时，退出码 0，stdout 为空，`hooks/` 下没有新文件 |
| `test_session_start_injects_ledger` | 账本有一条非终态项时，输出 JSON 的 `additionalContext` 含该项名；总长 ≤ 2000 |
| `test_session_start_outside_kit_project` | 没有 `.team-kit.json` 时 stdout 为空 |
| `test_kernel_edit_warns_once_per_session` | 同一个 `session_id` 对 `AGENTS.md` 发两次 `PostToolUse`：第一次 `additionalContext` 含「内核文件」，第二次 stdout 为空；改普通文件时 stdout 为空 |
| `test_codex_apply_patch_paths` | 用附录 A 记录的补丁输入格式，能解析出两个路径，其中的内核文件触发提醒 |
| `test_check_after_edit` | `project.conf` 写 `CHECK_AFTER_EDIT='sh -c "echo bad; exit 1"'` 时，提醒含 `bad`；脚本退出 0 时不注入；有 `sleep 20` 的命令在 8 秒左右返回，不报错 |
| `test_subagent_stop_reminds_once` | `SubagentStart`（se，id `a1`）之后没有 se 的落账，`SubagentStop` 注入含「还没有落账」；`stop_hook_active: true` 时 stdout 为空；SE 落账之后再 `SubagentStop`，stdout 为空；`agent_type` 为 `Explore` 时 stdout 为空 |

- [ ] **Step 2：运行，看它失败**

同 Task 3 的测试命令。Expected：新用例 ✗。

- [ ] **Step 3：实现 `hook.py`**

- 最外层用 `try/except BaseException` 包住，最后一律 `sys.exit(0)`；
- 子进程调用都设 `timeout`：账本 5 秒，工程检查 8 秒；
- 状态文件：
  - `hooks/seen-<session_id>.json` 记已提醒的内核文件；
  - `hooks/agents/<agent_id>` 记子代理开始时间（ISO 格式，与账本的 `ts` 可比）；
  - `SubagentStop` 时删除对应文件。

- [ ] **Step 4：运行，看它全过，然后提交**

```bash
git add -- template/skills/team-check/hook.py
git commit -m "team-check: advisory hook entry for session start, edits and subagents" -- template/skills/team-check/hook.py template/skills/team-check/test_team_check.py
```

---

### Task 5：接上两个宿主的配置，改规则文字

**Files:**
- Modify: `template/.claude/settings.json`：加 `hooks`
- Create: `template/.codex/hooks.json`；`MANIFEST` 在 `.codex/config.toml` 之后加 `.codex/hooks.json`
- Create: `template/skills/team-check/SKILL.md`
- Modify: 设计 §5.4 表里列出的规则文件：
  - `team-ledger/SKILL.md`、`DESIGN.md`；
  - 契约「附：状态账本」；
  - `派活与交付.md`「一」「二」；
  - `sa-review/SKILL.md`「四」（顺带补上 `docs/rules/` 路径）；
  - `并行线.md`「八」；
  - `AGENTS.md`；
  - `双端协作与交接.md`；
  - `.githooks/pre-commit` 头注。
- Test: `bin/test_kit.py`

- [ ] **Step 1：写失败测试**（`bin/test_kit.py`）

```python
def t_hooks_wired():
    import json
    s = json.load(open(os.path.join(kit.TEMPLATE, ".claude/settings.json"), encoding="utf-8"))
    c = json.load(open(os.path.join(kit.TEMPLATE, ".codex/hooks.json"), encoding="utf-8")) \
        if os.path.exists(os.path.join(kit.TEMPLATE, ".codex/hooks.json")) else {"hooks": {}}
    for name, cfg in (("claude", s), ("codex", c)):
        hooks = cfg.get("hooks", {})
        for ev in ("SessionStart", "PostToolUse", "SubagentStart", "SubagentStop"):
            cmds = [h["command"] for g in hooks.get(ev, []) for h in g.get("hooks", [])]
            ok(any("skills/team-check/hook.py" in x and ev in x for x in cmds), f"{name} 挂了 {ev}")
            ok(all(h.get("timeout") == 10 for g in hooks.get(ev, []) for h in g.get("hooks", [])), f"{name} {ev} 超时 10 秒")
    pt = [g.get("matcher", "") for g in s.get("hooks", {}).get("PostToolUse", [])]
    ok(any("Write" in m and "Edit" in m for m in pt) and not any("MultiEdit" in m for m in pt), "claude PostToolUse matcher 为 Write|Edit|NotebookEdit，无 MultiEdit")
    ok(".codex/hooks.json" in kit.kernel_files()[0], ".codex/hooks.json 在内核清单里")
```

- [ ] **Step 2：运行，看它失败**

运行 `python3 bin/test_kit.py`。Expected：`t_hooks_wired` 的各项 ✗。

- [ ] **Step 3：写配置和规则文字**

- **Claude 的命令**：`python3 "$CLAUDE_PROJECT_DIR/skills/team-check/hook.py" <事件>`。
- **Codex 的命令**：`sh -c 'python3 "$(git rev-parse --show-toplevel)/skills/team-check/hook.py" <事件>'`。实际写法以附录 A 的实测为准。
- **matcher**：
  - Claude：`SessionStart` 用 `startup|resume|clear|compact`，`PostToolUse` 用 `Write|Edit|NotebookEdit`；
  - Codex：用附录 A 的结论。
- **规则文字**：按设计 §5.4 逐条改。
- **SKILL.md**：写明三个钩子各做什么、四个子命令怎么用、退出码的含义。

- [ ] **Step 4：跑全部测试，然后提交**

```bash
python3 bin/test_kit.py && python3 template/skills/team-ledger/test_team_ledger.py \
  && python3 template/skills/team-check/test_team_check.py && bash template/.githooks/tests/hooks.test.sh
```

Expected：四套全过。

```bash
git add -- template/.codex/hooks.json template/skills/team-check/SKILL.md
git commit -m "Wire advisory hooks on Claude Code and Codex; rules mention the checks" -- template/.claude/settings.json template/.codex/hooks.json template/skills/team-check/SKILL.md MANIFEST bin/test_kit.py template/skills/team-ledger/SKILL.md template/skills/team-ledger/DESIGN.md template/docs/rules/团队协作契约.md template/docs/rules/派活与交付.md template/skills/sa-review/SKILL.md template/docs/rules/并行线.md template/AGENTS.md template/docs/rules/双端协作与交接.md template/.githooks/pre-commit
```

---

### Task 6：真机冒烟、文档、整体审阅、发版、同步

- [ ] **Step 1：真机冒烟**

在 scratchpad 里新建一个 git 仓库，执行 `bin/kit install`，造一条非终态账本项。然后：
1. 用 `claude -p` 跑一次：确认会话开始时注入了这一项，改 `AGENTS.md` 后收到内核提醒；
2. 用 `codex exec` 跑一次，做同样两件事。

Expected：两个宿主各有一次注入、一次提醒，日志为证。结果写进附录 A 的「冒烟」一节。

- [ ] **Step 2：更新文档并提交**

- `docs/交接说明.md`：
  - §八 新增「v0.10.0」一节；
  - §六 的验证命令里加上 `team-check` 的测试和计数；
  - §3.1 的内核文件数改为实际数。
- `README.md` 的「测试」一节加上 `team-check` 的测试命令。
- 设计文档的状态行改为「已批准，v0.10.0 实施」。

- [ ] **Step 3：整体审阅**

派独立审阅代理，读本计划的 Review Focus、设计、附录 A 和 diff（范围 `8abf58d..HEAD`）。修完重要问题再继续。

- [ ] **Step 4：打标签、推送、同步**

1. `git tag -a v0.10.0`，然后 `git push origin main --tags`；
2. 对 vista、prism 分别执行：
   - 先确认工作树里没有别人暂存的内容；
   - `bin/kit sync`；
   - 新文件先 `git add --`，再按 sync 打印的命令带路径提交，提交信息沿用各工程的惯例；
   - `bin/kit check`。

Expected：
- 两个工程 `check` 都退出 0；
- 内核文件三处 sha256 一致；
- 两个工程都不推送；
- 发版说明里写明：Codex 要在每个工程里用 `/hooks` 信任一次。

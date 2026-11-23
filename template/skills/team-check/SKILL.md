---
name: team-check
description: Use when SA checks a returned report for out-of-scope edits, duplicate Flyway migration versions before merging a lane, whether an iteration plan has its 并行编排 section, or whether worktrees match the lanes registered in the ledger. Also documents the advisory runtime hooks (session start, file edits, subagent stop) that run on Claude Code and Codex.
---

# team-check：检查命令与运行时钩子

**只读、只提醒。** 这里的命令不改仓库、不落账；钩子不拦截任何写入或停止，出错一律放行。真正会拒绝的检查在账本脚本里（`skills/team-ledger/SKILL.md`「提交号硬拒」）。

## 一、手动检查命令（SA 用）

```bash
python3 skills/team-check/team-check.py scope --base <起点提交> --commits <提交…> --allow <可写…> [--deny <禁写…>]
python3 skills/team-check/team-check.py migrations [--dir <迁移目录>]
python3 skills/team-check/team-check.py plan <迭代规划文件>
python3 skills/team-check/team-check.py lanes
```

| 命令 | 什么时候用 | 看什么 |
|---|---|---|
| `scope` | 收回报时（`docs/rules/派活与交付.md`「二」） | 这些提交改动的路径是否全在可写范围内、没碰禁写范围。`dir/` 按前缀匹配，其余按通配符匹配 |
| `migrations` | 合入并行线前（`docs/rules/并行线.md`「五」） | Flyway 迁移版本号（`V<n>__*.sql`）有没有重复。不给 `--dir` 时，从工程配置「目录」表的「数据库迁移」一行读 |
| `plan` | 评迭代规划、巡检第 3 步 | 有没有「并行编排」一节，「线的划分」「合入顺序」是否写了 |
| `lanes` | 巡检、恢复会话 | `lane/*` 分支和工作树，与**未收口**工作项的 note 里登记的 `lane/<短名>` 是否一致。列「多出」（开了没登记）和「缺失」（登记了却不在） |

**退出码**：0 通过；1 有问题；**2 判不了——判不了 ≠ 通过**，要看输出里的原因。

## 二、运行时钩子（两个宿主自动运行）

入口只有一个：`skills/team-check/hook.py <事件>`。Claude Code 配在 `.claude/settings.json`，Codex 配在 `.codex/hooks.json`；两份配置都只写这个入口，逻辑全在脚本里（改逻辑不改配置，Codex 就不用重新信任）。

| 事件 | 做什么 |
|---|---|
| 会话开始（含恢复、清空、压缩后） | 有非终态项、待负责人裁决的事、或有工作树没登记时，把它们注入上下文（≤ 2,000 字符）；都没有就不注入 |
| 写文件后 | 改到 `.team-kit.json` 记录的内核文件时提醒一次（同一会话同一文件只一次）；`.githooks/project.conf` 有 `CHECK_AFTER_EDIT` 时执行它，非 0 退出才把输出注入为提醒 |
| 子代理开始 / 结束 | 只对 pm / ui / se / qa：开始时记时间；结束时若这个角色从开始以来没落过账，提醒它落账并按「二、回报」回报后再结束（只提醒一次） |

**覆盖范围的边界（如实说）**：
- 通过 shell 命令写文件（`sed`、重定向、`printf >`）不触发写文件后的钩子。Codex 常这样写文件。内核文件的改动在提交时还有 `.githooks/pre-commit` 兜底提醒。
- 子代理落账提醒只看「这个角色有没有落过账」，同时开了两个同角色实例时，一个落了账，另一个也会被放过。

**Codex 第一次在本工程使用前**，要在 Codex 里执行 `/hooks` 审阅并信任本工程的钩子；`.codex/hooks.json` 内容不变就不用再信任。Claude Code 在接受工作区信任后即运行。

**工程检查挂载点**：在 `.githooks/project.conf` 加一行，例如

```bash
CHECK_AFTER_EDIT='python3 scripts/check_invariants.py'
```

被改文件的路径（相对工程根）会追加在命令后面；8 秒超时；退出 0 不提醒。只解析这一行，不 source 整个文件。

钩子的状态文件在账本目录下的 `hooks/`（`.team-ledger/hooks/`，不入库）。

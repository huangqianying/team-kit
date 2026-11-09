# team-kit · 团队基建内核

一套可以整套拷进任何工程的 AI 协作基建：SA（值守会话）＋ PM / UI / SE / QA（subagent）五角色契约、Claude Code 与 Codex 双端入口、状态账本、方法类 skill、提交钩子。

**原则：内核在所有工程逐字相同；工程专属的东西只放三份文件。**

背景、需求、已完成的工作与已知缺口见 [`docs/交接说明.md`](docs/交接说明.md)。

| 放哪 | 内容 |
|---|---|
| 内核（`template/`，清单见 `MANIFEST`） | `AGENTS.md`、`CLAUDE.md`、团队协作契约、双端协作与交接、UI 设计规范（通用规则）与演示页、四份角色、两端入口与配置、内核 skill、`.githooks/` 通用脚本 |
| 工程配置 `docs/rules/工程配置.md` | 产品名、目录、命令、分支与发布、部署、项目规范、本工程补充规则（内核用「见工程配置「节名」」引用它） |
| UI 规范本工程实例 `docs/rules/UI设计规范-本工程实例.md` | 本产品的 UI 取值（产品名、启用的登录方式、各身份顶栏件数、大屏与否等），按 UI 设计规范节号对应 |
| 钩子配置 `.githooks/project.conf` | 本工程的测试路径、配置文件路径、业务标识符白名单等 |

工程自己的部署 skill、端到端测试 skill、系统设计规范、错误码规范等不进内核，在工程配置里登记即可。

## 用法

```bash
# 新工程：安装内核，生成工程配置与钩子配置模板
bin/kit install /path/to/project
# 然后填写 docs/rules/工程配置.md、docs/rules/UI设计规范-本工程实例.md 与 .githooks/project.conf，核对后在工程里提交

# 内核有更新：同步到工程（工程里改过内核文件会被拒绝，先把改进收回 kit）
bin/kit sync /path/to/project

# 核对工程是否与内核一致（不一致退出 1）
bin/kit check /path/to/project

# 看工程里对内核做了什么改动
bin/kit diff /path/to/project [路径 …]

# 把工程里改过的内核文件收回 kit 的 template/（不提交）
bin/kit adopt /path/to/project [路径 …] [--force]
```

`install` / `sync` 会：拷内核文件（保留可执行位）、建 `.claude/skills` 与 `.codex/skills` → `../skills` 软链、缺工程配置时生成模板（之后不再覆盖）、在 `.gitignore` 补 `.team-ledger/`、执行 `.githooks/install.sh` 设置 `core.hooksPath`、写 `.team-kit.json`（kit 版本号、提交号与各内核文件摘要）。它们**不提交**，由工程侧核对后自行提交。

工程里的内核文件有未提交改动时，`install` / `sync` 一律拒绝（`--allow-dirty` 明确放行）。工程里已有与内核同名、但 kit 从没接管过的文件（比如内核新增了一个文件，而工程里原本就有一份自己的）且内容不同时，也拒绝，先把本工程专属内容移走、通用改进收回 kit，再 `--force` 覆盖。

## 改内核的流程

1. 在 kit 的 `template/` 里改，跑 `python3 bin/test_kit.py`、`python3 template/skills/team-ledger/test_team_ledger.py`、`bash template/.githooks/tests/hooks.test.sh`。
2. 在 kit 提交，打版本标签（见下），推送提交与标签。
3. 对每个工程 `bin/kit sync <工程>`，在工程里**带路径**提交（`sync` 会打印现成的 `git commit -m "…" -- <路径>` 命令；同一工作树里可能有别人暂存的改动，不带路径会一并提交走）。
4. `bin/kit check <工程>` 退出 0。

## 版本

kit 用附注标签 `v<大>.<中>.<小>` 发版：改了内核里角色、流程、规范的口径升「中」位，只修错字、修工具缺陷升「小」位，内核结构不兼容地改动（工程配置节名变化、工程专属文件增删）升「大」位（`v1` 之前按「中」位处理）。

```bash
git tag -a v0.3.0 -m "<这一版改了什么>"
git push origin main --tags
```

`sync` 前先打标签，`.team-kit.json` 才会记成整版本号；标签之后又有提交时记成 `v0.3.0-2-g<提交>`。`kit check` 输出当前 kit 版本与工程记录的版本。

工程里先改了内核文件（比如值守时顺手修了契约）：提交时 `pre-commit` 会打一行提醒（只提醒不拦；与 `.team-kit.json` 记录一致的 kit 同步改动不提醒）。之后在 kit 执行 `bin/kit adopt <工程>` 收回 → 按上面流程测试、提交 kit、同步回所有工程。

`adopt` 的保护：该文件在这个工程上次同步之后 kit 也改过时，以上次同步时的 kit 版本为基线做三方合并——两边改的不是同一处就合并收回（输出「合并」，请核对结果）；改到同一处或取不到基线时拒绝收回（避免冲掉 kit 的新改动），用 `bin/kit diff` 对照后人工合并，或 `--force` 用工程版覆盖；kit 的 `template/` 里要收回的文件有未提交改动时也拒绝；工程里删掉的内核文件不会在 kit 里删，只提示。

## 新工程首次落地后要做的

- 填 `docs/rules/工程配置.md` 每一节，不适用写「无」；节名不要改（`kit check` 会核）。「并行线」一节不填，本工程就不开并行线（`kit check` 只警告）。
- 填 `docs/rules/UI设计规范-本工程实例.md`（本产品的 UI 取值；不适用的节写「不适用」并给依据）。
- 填 `.githooks/project.conf`，跑一次 `bash .githooks/tests/hooks.test.sh`。
- 准备 `system-version.json`（`{"version": "...", "status": "in-progress", "updated": "YYYY-MM-DD HH:MM"}`）。
- 新克隆的仓库要先执行 `bash .githooks/install.sh`，否则钩子不生效。

## 测试

```bash
python3 bin/test_kit.py
python3 template/skills/team-ledger/test_team_ledger.py
bash template/.githooks/tests/hooks.test.sh
```

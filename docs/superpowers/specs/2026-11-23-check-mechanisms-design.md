# 检查机制设计（借鉴 HelixHarness 第二轮）

> 状态：草案，待产品负责人审阅。审过之前不改内核。
> 日期：2026-11-23
> 范围：team-kit 内核（`template/`、`MANIFEST`、`bin/`）。

## 1. 为什么要做

team-kit 现在的纪律大多靠模型读规则后自觉执行。典型的几条：
- SA 每回合先读账本再派活（`team-ledger` skill「每回合三步」）；
- 待评审产物以 `commit:path` 指认（契约 §五）；
- 不在工程里改内核文件（`AGENTS.md`）；
- 回报不越出可写范围（`派活与交付.md`「二」）。

运行时钩子一个都没有，只有 git 提交前钩子（查凭据、提醒改了内核）。

HelixHarness 的做法是让脚本把关：
- 状态推进看校验脚本，不看模型自报；
- 运行时钩子注入上下文、在写文件后执行检查；
- 只提醒的钩子出错一律放行，要拦截的钩子范围窄、出错按拦截处理。

产品负责人 2026-11-23 认可把这一套借过来，作为借鉴的第二轮，并选定**方案 A：钩子只提醒，账本脚本硬拒**。

## 2. 目标、不做、反目标

**目标**
- 账本脚本对三类不合格落账直接拒绝（§5.1）。
- Claude Code 和 Codex 都装上三个只提醒的钩子：会话开始注入状态；写文件后提醒；子代理结束前提醒落账（§5.2）。
- 提供 SA 手动运行的检查命令：越界、迁移编号、并行编排、工作树与线（§5.3）。

**不做**
- 钩子不拦截任何写入或停止（方案 A）。写文件前的钩子不用。
- 不设阶段关口（方案 C 被否）。评审仍是建议级、一轮。
- 不追溯已有账本：新规则只拦新的落账；`stale`、`owner` 读存量照旧。
- 不替工程写检查命令。工程挂载点只负责执行工程自己登记的命令。

**反目标**（技术上做到了，但出现下面任一情况就算失败）
- 钩子出错、超时或刷屏，拖慢或打断会话。
- **有产物**的正常落账被硬拒。没有产物的工作（只读排查、运维、咨询）用 `--no-commit '理由'` 写明，这是正常用法，不算绕开。
- 每次发版都要请负责人在两个工程里重新信任一遍 Codex 钩子。

## 3. 约束（2026-11-23 核实）

**Claude Code**（官方文档 `code.claude.com/docs/en/hooks`、`sub-agents`、`tools-reference`）
- 项目钩子写在 `.claude/settings.json` 的 `hooks` 下。这个文件是内核文件，两个工程逐字相同。各层设置里的钩子合并执行。
- 只有在接受工作区信任之后，钩子才会运行；`-p` 模式视为已信任。
- 会话开始（`SessionStart`，matcher 取 `startup` / `resume` / `clear` / `compact`）用 JSON `hookSpecificOutput.additionalContext` 注入上下文，上限 10,000 字符。
- 写文件后（`PostToolUse`）：
  - 改文件的工具名是 `Write`、`Edit`、`NotebookEdit`，**没有 `MultiEdit`**；
  - 输入带 `tool_input.file_path`，还带通用字段 `agent_id`、`agent_type`；
  - 不阻塞的提醒用 `hookSpecificOutput.additionalContext`，纯文本 stdout 不会进入模型上下文。
- 通过 Bash 写文件不会触发上面的 matcher。
- 子代理结束（`SubagentStop`）：
  - 输入带 `agent_id`、`agent_type`、`stop_hook_active`、`last_assistant_message`；
  - 返回 `additionalContext` 会让子代理继续一轮；
  - 连续继续最多 8 次；
  - 用 `stop_hook_active` 防止重复触发。
- 子代理开始（`SubagentStart`）会触发，带 `agent_id`、`agent_type`。
- 钩子出错（非 0/2 退出、缺脚本、输出无效）默认放行。默认超时 600 秒，每个钩子可以单独设 `timeout`。
- `$CLAUDE_PROJECT_DIR` 是会话启动时的项目根目录，进入工作树后不变。

**Codex**（本机 `codex-cli 0.167.0`；文档 `learn.chatgpt.com/docs/hooks`、`config-advanced`）
- 项目钩子写在 `.codex/hooks.json`，格式与 Claude Code 相同：事件 → matcher 分组 → handler。也可以写在 `.codex/config.toml` 的 `[hooks]` 表里，同一层两种都写时会给出警告。
- 项目要被信任，`.codex/` 里的钩子才会加载。另外，非托管钩子要用 `/hooks` 审阅并信任，**信任与钩子内容的哈希绑定，内容一改就要重新信任**。
- 事件包括 `SessionStart`（`source`：startup / resume / clear / compact / fork）、`PostToolUse`、`SubagentStart`、`SubagentStop`（带 `agent_id`、`agent_type`、`stop_hook_active`）。
- 文件编辑报告的工具名是 `apply_patch`。文档没有说清 matcher 写 `Edit` / `Write` 能不能匹配到它，**要实测**。
- 文档没有说明写文件后的钩子在子代理里是否带 `agent_id`，**要实测**。
- 上下文注入默认上限约 2,500 tokens。

**team-kit 现状**
- 账本脚本 `team-ledger.py` 已经对一些落账硬拒，例如非终态没写接续方、同一件事起了不同名字（`cmd_append`，第 232 行起）。现有测试 84 项。
- `.githooks/project.conf` 是工程自有的 bash 变量文件，kit 同步不覆盖，vista、prism 都有。
- 内核目录型条目（如 `skills/team-check/`）整目录同步。

**两个工程 2026-11-01 以来的账本实况**（2026-11-23 用 `git cat-file -e` 逐条回放；「存在的提交号」指 note 里至少有一个在仓库里真实存在的提交号）：

| 落账 | 角色 | vista | prism |
|---|---|---|---|
| 「待评审」：存在的提交号 ＋ 一个路径 | PM / QA / UI | 10/10、10/10、19/19 | 3/3、16/16、3/3 |
| 同上 | SE | 45/49 | 22/32 |
| 同上 | SA | 7/25 | 2/2 |
| 「待评审」：严格写成 `<提交号>:<路径>` | SE / UI / SA | 27/49、7/20、2/28 | — |
| 「交接」：存在的提交号 | PM / QA / SE / UI | 144/145、113/113、163/167、35/39 | 41/51、72/96、69/87、2/2 |
| 「完成」：存在的提交号 | PM / QA / SE / UI | 53/53、45/45、23/29、11/11 | 58/66、40/54、67/97、5/5 |

- **严格的 `<提交号>:<路径>` 写法误伤很多。** UI 常写 `commit:a8849c84 prototypes/v0.0.8/`，SE 常写 `96c615af（lane/x）：docs/...`。放宽为「存在的提交号 ＋ 一个路径」后，绝大多数能过。
- **SA 的「待评审」常常不是在指认单个产物。** 比如一次给多个工作项落账、记「合评输入就绪」，或者用 `--to owner` 记「待报维护方」。
- **prism 有约三成的「完成」「交接」没有提交号。** 大多是只读排查、运维，或者 11 月中旬以前「未提交、交 SA 串行提交」的老做法。
- **SA 派活给 SE 时，`--phase` 多数不是 dev。** vista 11-10 以来：spec 16、requirement 5、review 3、design 2、dev 6。也就是说，一个工作项第一次交给 SE，常常不是开发。
- **账本 note 里历史上出现过的 `lane/<短名>`**：vista 约 40 个、prism 6 个；两个工程现在都只有主工作树。

## 4. 方案比较（负责人选了 A）

| 方案 | 做法 | 取舍 |
|---|---|---|
| **A. 钩子只提醒，账本脚本硬拒（选定）** | 钩子只注入和提醒；账本对不合格落账直接拒绝 | 不会被钩子误判卡住；越界写入只能事后发现 |
| B. 在 A 的基础上，越界写入当场拦 | 账本加机器可读的可写范围，写文件前的钩子拒绝越界写入 | 派活要多填一个精确字段；Bash 写入仍拦不到；Codex 能否做到要实测 |
| C. 每个阶段都设脚本关口 | 像 HelixHarness 一样，不过就不能往下走 | 与「评审只建议、一轮封顶」冲突 |

## 5. 设计

### 5.1 账本硬拒（`skills/team-ledger/team-ledger.py` 的 `append`）

新增三条规则。拒绝时退出码与现有拒绝一致，并打印原因和改法。

| # | 条件 | 要求 | 例外 |
|---|---|---|---|
| R1 | `--role` 为 pm、ui、se、qa，且 `--status 待评审` | note 里至少有一个在仓库里存在的提交号，**并且**至少有一个路径（含 `/` 的片段，或带常见扩展名的文件名）。不要求两者紧挨着 | `--no-commit '<理由>'`（同 R2） |
| R2 | `--role` 为 pm、ui、se、qa，且 `--status` 为 `完成` 或 `交接` | note 里至少有一个在仓库里存在的提交号（7–40 位十六进制） | `--no-commit '<理由>'`：理由不能为空，记进事件。**没有产物的工作用它写明，属于正常用法** |
| R3 | `--role sa`、`--status 交接`、`--to se`、`--phase dev`，且这个（工作项，子产物）还没有记过起点提交 | 必须带 `--base <提交号>`，这个提交在仓库里存在；值记进事件的 `base` 字段 | 无 |

- **SA 不适用 R1、R2**：SA 的「待评审」多是多项合评、输入就绪这类登记，「完成」多是裁定和合入（§3 实况）。契约 §五「被评产物以 `commit:path` 指认」照旧是规则，只是不由脚本硬拒（§9 C9）。
- **R3 只认 `--phase dev`**：开发派活必须写 `--phase dev`，这一点写进账本 SKILL 和「派活与交付」「一」。SE 写 spec、做评审、澄清需求的派活不记起点，否则会把起点锁在开发之前的一个早期提交上（§9 C5）。
- **起点按（工作项，子产物）分别记**：并行线下，同一个工作项的两条线起点不同（例如 vista `mcp-service` 的 `lane/mcp` 和 `lane/mcp-b`）。

- **「提交存在」的判定**：在账本所在仓库执行 `git cat-file -e <sha>^{commit}`。`git` 不可用，或者不在 git 仓库里时，**不拒，打印一行警告**。账本里已经有「判不了 ≠ 全清」的处理口径，这里同样不能因为环境问题把落账卡死。
- **提交号的识别**：
  - 正则 `(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])`，大小写不敏感；`commit:path` 就是在它后面紧跟 `:` 和路径。
  - 一条 note 里有多个提交号时，只要其中一个存在就算通过（§9 C2）。
- **`stale` 的显示**：工作项有起点提交的，`stale` 在这一行后面显示 `起点 <sha 前 8 位>`，换端接班时不用翻 note 也能看到。

### 5.2 钩子（只提醒，出错一律放行）

**共用入口**：`skills/team-check/hook.py <事件名>`。从 stdin 读宿主传来的 JSON，输出宿主要求的 JSON。
- 任何异常都捕获，退出码一律 0，不输出任何内容；
- 每个钩子设 `timeout` 为 10 秒，宿主侧超时同样放行；
- 两个宿主的配置只写这一个入口，不写具体逻辑。以后改逻辑只改 `hook.py`，Codex 钩子配置的内容不变，不用重新信任（反目标 3）。

**H1 会话开始**（Claude Code `SessionStart`，matcher `startup|resume|clear|compact`；Codex `SessionStart`）

注入一段事实陈述，**总长不超过 2,000 字符**（照顾 Codex 的上限）：
- 非终态项：`team-ledger.py stale --hours 0` 的前 15 行，超出写「另有 N 项」；
- 待裁决：`team-ledger.py owner` 的前 10 行；
- 工作树与线：只写「多出」的一类，即存在 `lane/*` 工作树或分支、却没有登记在任何未收口工作项里的。没有就不写（§9 C10）。

账本不存在、工程没装 kit（没有 `.team-kit.json`）时，什么都不注入。

**H2 写文件后**（Claude Code `PostToolUse`，matcher `Write|Edit|NotebookEdit`；Codex `PostToolUse`，matcher 写 `apply_patch`，实测后定，见 §8）

1. **内核文件提醒**：被改的路径在 `.team-kit.json` 记录的内核文件里时，注入：「`<路径>` 是 team-kit 内核文件，各工程逐字相同；改动要报 team-kit 维护方，不在工程里直接改（`AGENTS.md`）。」
   - 同一会话里，同一个文件只提醒一次。记录放在 `.team-ledger/hooks/`，按会话 ID 分开。
2. **工程检查挂载点**：`.githooks/project.conf` 里有 `CHECK_AFTER_EDIT='<命令>'` 时执行它：
   - 把被改的路径作为参数传入，超时 8 秒；
   - 退出码非 0 时，把输出的前 1,500 字符注入为提醒；退出码 0 时不注入；
   - 没有这个变量就跳过。

   读取方式：只解析 `CHECK_AFTER_EDIT=` 这一行，按 shell 引号规则拆分，**不 source 整个文件**。

Codex 的 `apply_patch` 一次可能改多个文件，路径从 `tool_input` 里的补丁文本解析：`*** Add File:`、`*** Update File:`、`*** Delete File:` 行。实际格式以实测为准（§8）。

**H3 子代理开始与结束**（两个宿主都挂 `SubagentStart` 和 `SubagentStop`）

只对 `agent_type` 为 `pm`、`ui`、`se`、`qa` 的子代理生效。
- **开始时**：在 `.team-ledger/hooks/agents/<agent_id>` 记下开始时间，不注入任何内容。
- **结束时**：
  - `stop_hook_active` 为真时直接放行，防止循环；
  - 从开始时间到现在，账本里没有这个角色的任何事件时，注入一次：「本次还没有落账。请按 `skills/team-ledger/SKILL.md` 落账，并按 `docs/rules/派活与交付.md`「二、回报」回报四项后再结束。」
  - 有事件，或者开始时间文件不存在（比如钩子是会话中途才装上的），就放行。
  - 结束后删除开始时间文件。

只用开始时间判断，所以并行的同角色实例可能「借」到别的实例的落账而被放行。这是只提醒的代价，可以接受（§9 C4）。

### 5.3 SA 手动运行的检查命令（`skills/team-check/team-check.py`）

| 子命令 | 做什么 | 退出码 |
|---|---|---|
| `scope --base <sha> --commits <sha>... --allow <glob>... [--deny <glob>...]` | 列出这些提交改动的全部路径，标出不在 allow 里、或命中 deny 的路径 | 0 无越界 / 1 有越界 / 2 判不了 |
| `migrations [--dir <目录>]` | 迁移目录里的 Flyway 版本号（`V<n>__*.sql`）有没有重复。目录默认从工程配置「目录」表的「数据库迁移」一行读取 | 0 / 1 有重复 / 2 读不到目录 |
| `plan <迭代规划文件>` | 文件里有没有「并行编排」一节；有的话，「线的划分」「合入顺序」两项是否出现 | 0 / 1 缺 / 2 文件不存在 |
| `lanes` | 对照 `lane/*` 工作树和分支，与**未收口工作项**的 note 里登记的 `lane/<短名>`（只认符合短名格式的，`lane/`、`lane/worktree` 这类泛指不算）。列两类：**多出**，即有工作树或分支、没登记；**缺失**，即未收口工作项登记了、分支和工作树都不在。已收口工作项里出现过的线一律不看 | 0 一致 / 1 不一致 / 2 判不了 |

- 退出码沿用账本的口径：**2 表示判不了，不等于通过**。
- 这些命令只读，不改仓库，也不落账。
- `lanes` 怎么从 note 里认出「登记的线」：未收口工作项的 note 中出现 `lane/<短名>` 就算登记（`并行线.md`「三」规定落账写分支名）。非 `lane/*` 的工作树（例如工具自建的）不报，与 `并行线.md`「八」「不认账本以外的工作树」一致。

### 5.4 规则文字要跟着改的地方

| 文件 | 改什么 |
|---|---|
| `template/skills/team-ledger/SKILL.md`、`DESIGN.md` | 写明 R1–R3、`--no-commit`、`--base`；`stale` 显示起点提交 |
| `template/docs/rules/团队协作契约.md`「附：状态账本」 | 命令格式里加上 `[--base <提交>] [--no-commit '理由']` |
| `template/docs/rules/派活与交付.md`「一」 | 起点提交改为「派活落账时用 `--base` 记录」 |
| `template/skills/sa-review/SKILL.md`「四」 | 收回报核越界时可以用 `team-check scope`（顺带修复 v0.9.0 遗留的次要问题：引用补上 `docs/rules/` 路径） |
| `template/docs/rules/并行线.md`「八」 | 巡检第 3 步可以用 `team-check plan`、`lanes`；合入前可以用 `migrations` |
| `template/AGENTS.md` | 一句话说明两个宿主装了只提醒的钩子，以及 Codex 首次要用 `/hooks` 信任 |
| `template/docs/rules/双端协作与交接.md` | 换端时，Codex 第一次在本工程使用要先 `/hooks` 信任 |
| `.githooks/pre-commit` 头注 | 说明 `project.conf` 新增的可选变量 `CHECK_AFTER_EDIT` |
| `template/.claude/settings.json` | 加 `hooks`：`SessionStart`、`PostToolUse`、`SubagentStart`、`SubagentStop` |
| 新增 `template/.codex/hooks.json` | 同样四个事件，进 `MANIFEST` |
| 新增 `template/skills/team-check/` | `SKILL.md`、`hook.py`、`team-check.py`、测试 |

发版号 v0.10.0。

## 6. 对工程的影响

- **两个工程同步后：**
  - Claude Code 下钩子立即生效（工作区早已信任）；
  - Codex 下，负责人或值守的人要在每个工程里执行一次 `/hooks` 信任。之后只要 `.codex/hooks.json` 不变，就不用再信任。
- **新的落账规则**只拦新的落账。已经在推进的工作项，下一次落账时开始适用：
  - SE 交接要带提交号，绝大多数已经满足；
  - SA 给 SE 派开发活要写 `--phase dev` 并带 `--base`，这是新要求。已经派过开发的（工作项，子产物）不要求补记（§9 C5）。
- prism 约三成的「完成」「交接」以后要么带提交号，要么用 `--no-commit` 写明理由。
- `.githooks/project.conf` 里的 `CHECK_AFTER_EDIT` 由各工程按需填写。不填就不执行。

## 7. 依据

- HelixHarness `hosts/claude-code/hooks.json`、`project-hooks.json`、`hook_entry.py:72-74`、`skills/d-d2c/SKILL.md` 的技能级钩子。
- Claude Code 与 Codex 的官方文档（§3 列出的页面），2026-11-23 读取。
- 两个工程 11 月以来账本的统计（§3）。

## 8. 交给实施者决定或实测的事

- **Codex 实测**（实施的第一步，作为一次性的试探）：在临时仓库里装一个打印输入的钩子，用 `codex exec` 跑一次改文件、一次子代理。确认三件事：
  - `PostToolUse` 的工具名和 matcher 写法；
  - `apply_patch` 的 `tool_input` 格式；
  - 子代理里的写文件事件带不带 `agent_id`。
  
  实测结果写进设计附录，再定 H2 在 Codex 上的写法。如果 Codex 在非交互模式下跳过未信任的钩子，就改用 `--dangerously-bypass-hook-trust` 做这一次实测，并在附录里说明。
- Claude Code 同样做一次打印输入的实测，确认 `agent_type` 在子代理里是 frontmatter 的 `name`（`pm` / `ui` / `se` / `qa`）。
- `hook.py`、`team-check.py` 的内部结构和输出措辞。
- 测试：`hook.py` 用构造的 stdin JSON 测输出；`team-check.py` 用临时 git 仓库测；账本 R1–R3 加进 `test_team_ledger.py`。

## 9. 维护方的判断（请审阅时重点看）

| # | 判断 | 理由 |
|---|---|---|
| C1 | R1 认「存在的提交号 ＋ 一个路径」，不要求严格的 `<提交号>:<路径>`；R2 只要求存在的提交号 | 回放实况：严格写法误伤近一半，放宽后非 SA 角色绝大多数能过；提交号必须真实存在，这条不放松 |
| C2 | 一条 note 里有多个提交号时，只要一个存在就通过 | note 里常同时引用依据版本和产物提交，逐个核对容易被历史引用误伤 |
| C3 | git 不可用时只警告、不拒 | 环境问题不能卡死落账，与账本「判不了 ≠ 全清」的口径一致 |
| C4 | 子代理结束提醒只按「开始以来这个角色有没有落账」判断，接受并行实例互相借过的漏报 | 只提醒的机制，宁可漏报，不能误拦；精确判断要给账本加实例 ID，成本高 |
| C5 | R3 只在 `--phase dev` 的开发派活上要求，按（工作项，子产物）记；已派过开发的不补记 | 第一次交给 SE 常常不是开发；起点记早了，「先失败再通过」和旧失败分类都会错 |
| C6 | 工程检查挂载点放在 `.githooks/project.conf`，不新开文件 | 它已经是工程自有、kit 不覆盖的配置文件，两个工程都有 |
| C7 | 钩子配置只写一个入口，逻辑全在 `hook.py` | 避免每次发版都要重新信任 Codex 钩子（反目标 3） |
| C8 | H1 注入的内容总长不超过 2,000 字符 | 照顾 Codex 约 2,500 tokens 的上限，也避免每次会话开始都刷屏（反目标 1） |
| C9 | SA 不适用 R1、R2 | SA 的「待评审」「完成」多是登记、裁定、合入，回放只过 7/25；硬拒会让 SA 天天用 `--no-commit` |
| C10 | `lanes` 只看未收口工作项；H1 只注入「多出」 | 历史上出现过约 40 个线名，都看会天天报「缺失」刷屏；「多出」才说明有人开了线没登记，最需要提醒 |
| C11 | 没有产物的工作用 `--no-commit '理由'` 是正常用法 | prism 约三成落账没有提交号，大多是只读、运维类；让它们写明「没有产物」正是这条规则要的效果 |

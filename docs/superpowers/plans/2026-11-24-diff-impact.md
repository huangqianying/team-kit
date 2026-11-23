# 改动影响分析 skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增内核 skill `skills/diff-impact/`（静态影响分析方法），在契约 §二.1、`并行线.md`「五」「六」、`manage-docs` 各加一处引用，发 v0.11.0，同步 vista、prism。

**Architecture:**
- 新 skill 只有一个 `SKILL.md`，没有脚本。方法沿用 HelixHarness `git-diff-impact`（源码 `5bde4b3`），按 team-kit 两个工程（Java 21 Spring Boot ＋ Vue 3 TypeScript ＋ Flyway）改写。
- 规则文件只加「可以用」的推荐句，不加任何强制步骤（方案 A）。
- 用 kit 测试核三件事：skill 进了内核清单；SKILL.md 有固定的几节和关键口径；三处规则文字引用了它。

**Tech Stack:** 中文 Markdown；Python 3 标准库（`bin/test_kit.py`）；git。

**Spec:** `docs/superpowers/specs/2026-11-23-diff-impact-design.md`

## Global Constraints

- **内核逐字相同。** 只改 `template/`、`MANIFEST`、`bin/test_kit.py` 和 kit 自己的文档；工程侧只有 `bin/kit sync` 生成的改动。
- **不强制**：规则文字一律写「可以用」，不写「须」「必须跑」。
- **不加脚本**，不改账本脚本、`team-check`、钩子。
- **固定口径（照抄设计）**：
  - 报告覆盖边界里写「静态分析，未运行测试」；
  - 风险等级与证据确定性分开标；
  - 存档路径 `docs/tests/<版本>/影响分析-<工作项>.md`，账本 note 用 `commit:path` 引用；
  - 线的基准 `git merge-base <集成分支> lane/<短名>`；
  - 迁移检查引用 `team-check migrations --refs`；断点引用 `UI设计规范.md` §4.1。
- **措辞**：简体中文、短句；规则文件不写变更由来。
- **提交与推送**：kit 内带路径提交；只推送 team-kit；工程只做本地带路径提交，不推送。
- **版本**：v0.11.0。

## Review Focus

1. **复杂度判断时往往还没有改动**：契约 §二.1 那句话不能暗示「没有 diff 也能分析」。只在已有可分析的改动时推荐（例如 BUG 由某次提交引入，或已有修复草稿）。Task 2 的引用测试核这句话带有这个限定。
2. **线的改动与「两个提交直接对比」混淆**：用 `<集成分支>..lane/<短名>` 直接对比，会把集成分支上别的线的改动当成本线的反向改动。SKILL.md 必须写明线的模式以 merge-base 为基准，并记录实际基准 sha。Task 1 测试核 `git merge-base` 出现在「输入与范围」一节。
3. **未提交模式漏掉新文件**：`git diff HEAD` 不含未跟踪文件。SKILL.md 写明用 `git ls-files --others --exclude-standard` 单列。Task 1 测试核这条命令。
4. **模型自动调用被关掉**：HelixHarness 原文带 `disable-model-invocation: true`，照抄后 SA（主会话）无法按判断自行调用。frontmatter 不带这一项。Task 1 测试核。
5. **报告被当成评审结论或测试证据**：SKILL.md 单列「不是什么」，写明它不替代 SA 评审、QA 测试和 `派活与交付.md`「四」的证据。Task 1 测试核。

---

### Task 1：新建 `skills/diff-impact/SKILL.md` 并进内核清单

**Files:**
- Create: `template/skills/diff-impact/SKILL.md`
- Modify: `MANIFEST`（在 `skills/team-check/` 之后加 `skills/diff-impact/`）
- Test: `bin/test_kit.py`

**Interfaces:**
- Produces: 常量 `DIFF_IMPACT = "skills/diff-impact/SKILL.md"`（Task 2 的引用测试也用）；SKILL.md 七节的节名（Task 2 的规则文字按节名引用「六、落位」）。

- [ ] **Step 1：写失败的测试** `t_diff_impact_in_kernel`

```python
DIFF_IMPACT = "skills/diff-impact/SKILL.md"

def t_diff_impact_in_kernel():
    files, _ = kit.kernel_files()
    ok(DIFF_IMPACT in files, "diff-impact 在内核清单里")
    p = os.path.join(kit.TEMPLATE, DIFF_IMPACT)
    text = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    head = text.split("\n---", 1)[0]
    ok("name: diff-impact" in head, "frontmatter name 为 diff-impact")
    ok("disable-model-invocation" not in head, "不关模型自动调用")
    for sec in ["一、输入与范围", "二、方法", "三、兼容性", "四、分级",
                "五、报告", "六、落位", "七、不是什么"]:
        ok(f"## {sec}" in text, f"diff-impact 有「{sec}」一节")
    scope = text.split("## 一、输入与范围", 1)[-1].split("\n## ", 1)[0]
    for s in ["git merge-base", "git ls-files --others --exclude-standard",
              "git show <sha>:<path>", "rev-parse --verify"]:
        ok(s in scope, f"「输入与范围」写了 {s}")
    for s in ["静态分析，未运行测试", "证据确定性", "team-check migrations --refs",
              "§4.1", "docs/tests/<版本>/影响分析-<工作项>.md", "commit:path"]:
        ok(s in text, f"diff-impact 写了「{s}」")
```

`kit.kernel_files()` 已按 MANIFEST 展开目录，返回的路径相对工程根。

- [ ] **Step 2：跑测试，确认失败**

Run: `python3 bin/test_kit.py 2>&1 | tail -5`
Expected: `✗ diff-impact 在内核清单里` 等若干条失败，退出码 1。

- [ ] **Step 3：写 SKILL.md，改 MANIFEST**

frontmatter：
- `name: diff-impact`
- `description`（英文，与 `team-check`、`sa-review` 同风格）：Use when SA or a role needs a static impact analysis of a change — uncommitted edits, a commit range, or what a lane brings in — e.g. judging blast radius for complexity triage, before merging a lane, or deciding retest scope after an acceptance fix. Read-only; the report is advice, not a review verdict or test evidence.

正文七节，节名照测试。每节写什么：
- **一、输入与范围**：四种模式的表（不给引用 / 一个引用 / 两个引用 / 某条线）。
  - 未提交：`git status --short`、`git diff --no-ext-diff --no-textconv HEAD --`，未跟踪文件用 `git ls-files --others --exclude-standard` 单列，只读明确属于本次范围的；范围混杂先列候选路径、问清再分析。
  - 提交对比：`git rev-parse --verify --end-of-options '<ref>^{commit}'` 解析成完整 sha，之后只用 sha。
  - 线：基准取 `git merge-base <集成分支> lane/<短名>`，目标取 `lane/<短名>` 的 sha，报告写明两个 sha；不能直接对比两个分支头（会把集成分支上别的线的改动算进来）。
  - 只读：`git show <sha>:<path>`、`git grep <模式> <sha> --` 读对应版本；不切分支、不 reset、不用工作区代替历史版本；不读凭据和被忽略的目录；删除项用基准 sha 并标明。
  - 无效引用、未解决的冲突：说明后停止。没有范围内改动：直接结束，不出「通过」结论。
- **二、方法**：设计里的 5 步。第 1 步读 `AGENTS.md`、`docs/rules/工程配置.md`「项目规范」里与改动相关的规范，有工作项时读它的需求说明或 spec+plan。第 3 步注明 Spring 依赖注入、事件、AOP、反射、MyBatis 映射文件、前端路由与动态组件是文本搜索的盲区，找不到引用 ≠ 没有调用方。改动太大时先列覆盖计划和优先级。
- **三、兼容性**：五类，每类 2～3 个检查点：
  - 对外接口与错误码：参数、返回字段、空值语义、默认值、错误码（工程有错误码规范时按它核）；
  - 配置与环境变量：新增必填项、改名、默认值变化对部署的影响（对照工程配置「部署」）；
  - 数据库迁移：已执行脚本不得修改；新旧版本并存时旧数据能不能读；跨线撞号用 `python3 skills/team-check/team-check.py migrations --refs <集成分支> lane/<短名>`；
  - 前端：浏览器范围先从 `package.json`、browserslist、Vite 配置确认，不臆造；新语法或 API 区分转译与 polyfill；布局变化按 `docs/rules/UI设计规范.md` §4.1 的断点档逐档看；
  - 依赖版本：JDK、Spring Boot、Node、前端框架大版本；提高环境门槛的列出。
  - 环境范围查不到时写成待验证项。
- **四、分级**：高 / 中 / 低的定义照 HelixHarness 原文；证据确定性三档：已确认（有代码位置）、推断、待验证。两项分开写；已有的守卫、降级分支计入判断；不因「只是新增」就判低。
- **五、报告**：先在对话给主要发现，再给报告。报告六部分照设计：范围、改动概览、影响清单、兼容性、建议重测范围、覆盖边界（必须有「静态分析，未运行测试」一句）。
- **六、落位**：默认不存文件，账本 note 一句结论加风险等级；用来定复测范围时存 `docs/tests/<版本>/影响分析-<工作项>.md`，带路径提交，账本 note 用 `commit:path` 引用。同名已存在时先读再决定续写或加后缀，不覆盖。
- **七、不是什么**：不是评审结论（不替代 `sa-review` / `technical-review`）；不是测试证据（不替代 `docs/rules/派活与交付.md`「四」）；不改代码、不生成测试、不落评审状态。

- [ ] **Step 4：跑测试，确认通过**

Run: `python3 bin/test_kit.py 2>&1 | tail -3`
Expected: `✓ 全部通过`，退出码 0。

- [ ] **Step 5：提交**

```bash
git add template/skills/diff-impact/SKILL.md
git commit -m "Add diff-impact skill to the kernel" -- template/skills/diff-impact/SKILL.md MANIFEST bin/test_kit.py
```

### Task 2：三处规则文字引用 diff-impact

**Files:**
- Modify: `template/docs/rules/团队协作契约.md`（§2.1「复杂度判据」段落之后）
- Modify: `template/docs/rules/并行线.md`（「五」的「前提」段之后；「六」的「验收不通过」第 3 条）
- Modify: `template/skills/manage-docs/SKILL.md`（第 45 行归类规则、第 75 行表格）
- Test: `bin/test_kit.py`

**Interfaces:**
- Consumes: Task 1 的 `DIFF_IMPACT` 常量和「六、落位」节名。

- [ ] **Step 1：写失败的测试** `t_diff_impact_referenced`

```python
def _section(text, start, stop="\n## "):
    return text.split(start, 1)[-1].split(stop, 1)[0] if start in text else ""

def t_diff_impact_referenced():
    rd = lambda rel: open(os.path.join(kit.TEMPLATE, rel), encoding="utf-8").read()
    c = _section(rd("docs/rules/团队协作契约.md"), "### 2.1", "\n### ")
    ok("skills/diff-impact" in c, "契约 §2.1 引用 diff-impact")
    ok("已有" in c.split("skills/diff-impact", 1)[0].rsplit("\n", 1)[-1], "契约那句限定在已有改动时")
    lanes = rd("docs/rules/并行线.md")
    ok("skills/diff-impact" in _section(lanes, "## 五、合入集成分支"), "并行线「五」引用 diff-impact")
    six = _section(lanes, "## 六、测试服与验收")
    ok("skills/diff-impact" in six and "影响分析" in six, "并行线「六」引用 diff-impact 并说存报告")
    md = rd("skills/manage-docs/SKILL.md")
    ok("影响分析" in md and "skills/diff-impact" in md, "manage-docs 写了影响分析的落位")
```

- [ ] **Step 2：跑测试，确认失败**

Run: `python3 bin/test_kit.py 2>&1 | tail -5`
Expected: 上面 5 条失败，退出码 1。

- [ ] **Step 3：改规则文字（照抄下面的句子）**

契约 §2.1，「复杂度判据」段落之后另起一段：

> 判影响面时，**已有改动可分析的**（例如 BUG 由某次提交引入，或已有修复草稿），SA 可以用 `skills/diff-impact` 做影响分析，结论写进账本 note。

`并行线.md`「五」，「**前提**」段之后另起一段：

> **合入前可以先看波及面**：用 `skills/diff-impact` 分析这条线带进来的改动（以 `git merge-base <集成分支> lane/<短名>` 为基准），看会波及哪些代码、和已合入的线有没有交叉。结论写进合入落账的 note。

`并行线.md`「六」，「验收不通过」第 3 条改为：

> - 是否只跑受影响的测试、QA 是否复测，由 SA 按改动范围定；可以用 `skills/diff-impact` 分析修复线的改动来定，这时报告按该 skill「六、落位」存为 `docs/tests/<版本>/影响分析-<工作项>.md`；

`manage-docs`：
- 第 45 行括号内加「影响分析」：`测试与验收文档（测试设计、测试用例、测试报告、验收报告、功能清单、影响分析）`；
- 第 75 行表格 `docs/tests/{版本号}/` 一行同样加「影响分析」，紧接着加一条归类规则：`- 改动影响分析报告（用来定复测范围时才存）→ docs/tests/{版本号}/影响分析-{工作项}.md，规则见 skills/diff-impact/SKILL.md「六、落位」。`

- [ ] **Step 4：跑测试，确认通过**

Run: `python3 bin/test_kit.py 2>&1 | tail -3`
Expected: `✓ 全部通过`，退出码 0。

- [ ] **Step 5：提交**

```bash
git commit -m "Rules point to diff-impact at triage, lane merge, and retest scope" -- template/docs/rules/团队协作契约.md template/docs/rules/并行线.md template/skills/manage-docs/SKILL.md bin/test_kit.py
```

### Task 3：真实试跑、文档、整体审阅、发版、同步

**Files:**
- Modify: `docs/交接说明.md`（§3.1 内核文件数与 skill 列表、§六 kit 测试项数、§八 加 v0.11.0）
- Modify: `docs/superpowers/specs/2026-11-23-diff-impact-design.md`（状态行改「已批准（2026-11-24）」，附录记试跑结果）

- [ ] **Step 1：子代理试跑**。派一个 sonnet 子代理，只给它 `template/skills/diff-impact/SKILL.md` 的路径和任务：「按这份 skill，以两个引用模式分析 team-kit 的 `4faab13^..4faab13`（team-check 检查函数那次提交），只在对话输出，不存文件」。核对它的产出：六部分齐全；影响清单的调用方有路径和行号且能在 `4faab13` 上用 `git show` 对上；有「静态分析，未运行测试」；没有切分支、没有写文件（`git status` 干净）。
  Expected: 全部满足。不满足的地方回到 SKILL.md 改清楚，再跑 Task 1 的测试。
- [ ] **Step 2：写文档**。试跑结论写进设计文档附录（命令、被分析提交、核对结果、改了 SKILL.md 哪里）；交接说明按上面三处更新，测试项数照实际输出填。
- [ ] **Step 3：整体审阅**。`review-package` 生成审阅包，派 opus 子代理审，带上 spec、plan、本节 Review Focus、账本的 Ruling 行。Critical / Important 一轮修完，每条先写失败的测试；Minor 记进交接说明 §5.1。
- [ ] **Step 4：发版**

Run（依次）：
- `python3 bin/test_kit.py`、`python3 template/skills/team-ledger/test_team_ledger.py`、`python3 template/skills/team-check/test_team_check.py`、`bash template/.githooks/tests/hooks.test.sh`
  Expected: 全部通过。
- `git tag -a v0.11.0 -m "v0.11.0: diff-impact skill"`，`git push origin main v0.11.0`
- 对 `../vista`、`../prism` 各执行：`bin/kit sync <工程>`；`git -C <工程> add -- skills/diff-impact`；带路径提交（vista：`chore(infra): sync team-kit v0.11.0 — diff-impact skill (_infra)`；prism：`Sync team-kit v0.11.0: diff-impact skill`），路径只含 sync 改动的文件；`bin/kit check <工程>`。
  Expected: check 退出 0；三个仓库全部内核文件 sha256 一致；工程不推送。
- [ ] **Step 5：记账**。交接说明 §八 补发版验证结果，带路径提交并推送 team-kit。

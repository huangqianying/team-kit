# 派活与交付规范 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 HelixHarness 第一轮借鉴的 8 条规则写进 team-kit 内核，新增 `docs/rules/派活与交付.md`，发 v0.9.0，并同步到 vista、prism。

**Architecture:**
- 共用格式（派活单、回报、spec+plan 必含项、证据、旧失败）集中写进新内核文件，契约、四个角色文件、`双端协作与交接.md` 只引用它（设计方案 B）。
- 只有单一读者的规则就地改：需求访谈改 `requirements-analysis`，写规则要有出处改 `AGENTS.md` 和工程配置模板头注，旧失败清单的落位改 `manage-docs`，评审核对点改 `sa-review`。
- 用 kit 测试核两件事：新文件已进内核；该引用它的地方都引用了。

**Tech Stack:** 中文 Markdown 规则文件；Python 3 标准库（`bin/test_kit.py`）；git。

**Spec:** `docs/superpowers/specs/2026-11-23-dispatch-delivery-design.md`（决定 D0–D3，维护方判断 C1–C10）。

## Global Constraints

- **内核逐字相同。** 只改 `template/`、`profile/`、`MANIFEST`、`bin/test_kit.py`、kit 自己的文档。不手改 vista、prism，sync 生成的除外。
- **新文件**：`docs/rules/派活与交付.md`，五节名照抄：
  - 「一、派活单」
  - 「二、回报」
  - 「三、spec+plan 必须写明」
  - 「四、证据」
  - 「五、旧失败」
- **固定取值（照抄设计）：**
  - 回报状态：`完成` / `阻塞` / `失败`。「失败」和「阻塞」落账都记为 `阻塞`（C7）。
  - 快速链路派活单只填 4 个字段：目标与预期产物、工作依据、工作项、验证方式（C2）。
  - 「先失败再通过」：每条 AC 至少一条，修 BUG 的回归测试每个一条。不规定先写测试还是先写实现（C3）。
  - 测试落点按建议级处理（C4）。
  - 不稳定的判定：改动前、改动后的提交上各重跑最多 3 次，结果不一致（C9）。
  - 旧失败清单路径 `docs/tests/已知旧失败.md`，由 QA 维护，只有负责人确认过的条目才能进（D1）。
- **不做：**
  - 不定文档骨架，不加模板文件；
  - 不改 `insight-discovery`（D2）；
  - 不改账本脚本；
  - 存量文档不追溯。
- **措辞**：简体中文、短句、关键约束加粗；规则文件不写变更由来。
- **提交与推送：**
  - kit 内提交一律带路径；
  - 只推送 team-kit；
  - 工程里只做带路径的本地提交，不推送；
  - 推送和同步之前，先做整体审阅。

## Review Focus

1. **快速链路的派活单被写得和增量链路一样长**（反目标 1）。预期：「一」里写明快速链路只填 4 个字段。Task 1 第 3 步用 grep 核。
2. **契约 §三 原有约束在改写中丢失**：「独立评审不预设结论」「可附必要背景和已批准的约束」，以及同角色并行的「派活说明另写…」。预期：都还在，或者被新文件「一」完整承接。Task 2 第 4 步用 grep 核。
3. **规则被读成强制 TDD 的先后顺序**（C3）。预期：「四」明写「不规定先写测试还是先写实现」。Task 1 第 3 步用 grep 核。
4. **误改了 `insight-discovery`**（D2）。预期：它的 diff 为空。Task 3 第 3 步用 git diff 核。
5. **新发现的旧失败让工作停下**（D1 明确不停）。预期：「五」写「工作照常推进，不停下等负责人」，不出现 `--blocker-role owner`。Task 1 第 3 步用 grep 核。

---

### Task 1: 新增 `派活与交付.md` 并进内核

**Files:**
- Create: `template/docs/rules/派活与交付.md`
- Modify: `MANIFEST`：在 `docs/rules/并行线.md` 后加一行 `docs/rules/派活与交付.md`
- Test: `bin/test_kit.py`

**Interfaces:**
- Produces：文件路径和五个节名（见 Global Constraints），Task 2、3 按这些名字引用。

- [ ] **Step 1：写失败测试**（加在 `t_kernel_config_refs_are_profile_sections` 之后）

```python
def t_dispatch_rule_in_kernel():
    files, _ = kit.kernel_files()
    ok("docs/rules/派活与交付.md" in files, "派活与交付.md 在内核清单里")
    text = open(os.path.join(kit.TEMPLATE, "docs/rules/派活与交付.md"), encoding="utf-8").read() \
        if os.path.exists(os.path.join(kit.TEMPLATE, "docs/rules/派活与交付.md")) else ""
    for sec in ["一、派活单", "二、回报", "三、spec+plan 必须写明", "四、证据", "五、旧失败"]:
        ok(f"## {sec}" in text, f"派活与交付.md 有「{sec}」一节")
```

- [ ] **Step 2：跑测试，看它失败**

Run: `python3 bin/test_kit.py 2>&1 | grep -E "派活与交付|全部通过|有失败"`
Expected: 6 条 ✗，末行「✗ 有失败」。

- [ ] **Step 3：写正文，改 MANIFEST**

- 文件头照契约格式写两行：只定规范、不记由来；只定必须包含的内容、不定骨架，已有文档不追溯。
- 五节的内容逐条照设计 §5.1「一」到「五」写，包括 D1、C1–C10 中落在本文件的规定。
- 写完运行：

```bash
grep -c "快速链路" template/docs/rules/派活与交付.md          # ≥1，且该处列出 4 个字段
grep -c "不规定先写测试还是先写实现" template/docs/rules/派活与交付.md   # 1
grep -c "不停下等负责人" template/docs/rules/派活与交付.md       # 1
grep -c "blocker-role owner" template/docs/rules/派活与交付.md   # 0
grep -c "已知旧失败.md" template/docs/rules/派活与交付.md        # ≥1
```

- [ ] **Step 4：跑全部 kit 测试**

Run: `python3 bin/test_kit.py`
Expected: 全过，通过数为 57 + 6 = 63。

- [ ] **Step 5：提交**

```bash
git add -- template/docs/rules/派活与交付.md
git commit -m "Kernel: add the dispatch and delivery rule" -- template/docs/rules/派活与交付.md MANIFEST bin/test_kit.py
```

---

### Task 2: 契约、角色、换端交接改为引用

**Files:**
- Modify: `template/docs/rules/团队协作契约.md`
  - 头注：在「多份工作同时推进时…」一行后加一行引用；
  - §三「派活说明」：第 97–103 行；
  - §三「交付」：第 129 行起。
- Modify: `template/docs/rules/roles/{pm,ui,se,qa}.md`：「动手前必读」清单和「交付」一节。
- Modify: `template/docs/rules/双端协作与交接.md:30`
- Test: `bin/test_kit.py`

**Interfaces:**
- Consumes：Task 1 的节名「一、派活单」「二、回报」「三、spec+plan 必须写明」「四、证据」「五、旧失败」。

- [ ] **Step 1：写失败测试**

```python
def t_dispatch_rule_referenced():
    need = ["docs/rules/团队协作契约.md", "docs/rules/双端协作与交接.md",
            "docs/rules/roles/pm.md", "docs/rules/roles/ui.md",
            "docs/rules/roles/se.md", "docs/rules/roles/qa.md"]
    for rel in need:
        text = open(os.path.join(kit.TEMPLATE, rel), encoding="utf-8").read()
        ok("派活与交付.md" in text, f"{rel} 引用了派活与交付.md")
```

- [ ] **Step 2：跑测试，看它失败**

Run: `python3 bin/test_kit.py 2>&1 | grep -E "引用了派活与交付|有失败"`
Expected: 6 条 ✗。

- [ ] **Step 3：改写**

| 位置 | 改成 |
|---|---|
| 契约「派活说明」 | 「派活说明按 `docs/rules/派活与交付.md`「一、派活单」填写（快速链路只填 4 项）。」后面保留「可附必要背景和已批准的约束；独立评审不预设结论。」 |
| 契约「交付」 | 改为按「二、回报」回报；加上 SA 核对「实际改动 ⊆ 可写范围、未碰禁写范围」，越界的只记录、交给路径负责方核对，不自动回退；派活落账时在 note 写一行可写和禁写范围（C10）。原有「状态变更按 team-ledger 落账，需要其他角色接手时写明交给 SA」保留 |
| 四个角色「动手前必读」 | 末尾加一项 `docs/rules/派活与交付.md` —— 回报格式见「二」。SE 加「三」「四」「五」，QA 加「四」「五」 |
| 四个角色「交付」 | 首段改为「在本次调用内按 `docs/rules/派活与交付.md`「二、回报」回报」；各角色原有的特殊要求（SE 并行线条款、QA 分路隔离、UI 原型记录、「需 X 角色做 Y」、不自行派活）原样保留 |
| se.md | 「交付」前加两句：spec+plan 按「三」写测试落点和每个任务的「覆盖」「依赖」；研发自测证据按「四」「五」记，写进 spec+plan 文档的一节，快速链路只写回报里的运行记录 |
| qa.md | 加一句：测试报告按「四」「五」记；旧失败对照 `docs/tests/已知旧失败.md`，清单由你维护，只收负责人确认过的条目 |
| 双端协作 :30 | 「再追加契约 §三的目标与范围、工作树、`commit:path` 和原 item 名」改为「再按 `docs/rules/派活与交付.md`「一、派活单」追加各字段」 |

- [ ] **Step 4：核约束仍在**

```bash
grep -c "独立评审不预设结论" template/docs/rules/团队协作契约.md   # 1
grep -c "派活说明另写" template/docs/rules/团队协作契约.md        # 1（同角色并行一条原样保留）
grep -rc "不要尝试派活\|不得自行调用" template/docs/rules/roles/pm.md template/docs/rules/roles/se.md template/docs/rules/roles/qa.md   # 各 ≥1
```

- [ ] **Step 5：跑测试，然后提交**

Run: `python3 bin/test_kit.py`
Expected: 全过，69 项。

```bash
git commit -m "Contract and roles use the dispatch and delivery rule" -- template/docs/rules/团队协作契约.md template/docs/rules/双端协作与交接.md template/docs/rules/roles/pm.md template/docs/rules/roles/ui.md template/docs/rules/roles/se.md template/docs/rules/roles/qa.md bin/test_kit.py
```

---

### Task 3: 需求访谈、写规则要有出处、旧失败清单落位、SA 评审

**Files:**
- Modify: `template/skills/requirements-analysis/SKILL.md`：「访谈流程」一节，第 56–60 行
- Modify: `template/AGENTS.md`：UI 设计规范那段（第 92 行）之后
- Modify: `profile/docs/rules/工程配置.md`：头注第 3–4 行
- Modify: `template/skills/manage-docs/SKILL.md`：`docs/tests` 的说明，第 45、74 行
- Modify: `template/skills/sa-review/SKILL.md`：「三、与并行编排对账」之后

- [ ] **Step 1：改写**

| 文件 | 改成 |
|---|---|
| requirements-analysis | 「访谈流程」开头加「访谈前先读洞见账本」：决策追溯表里已定的列为「已承接」请确认，不再提问；欠账清单优先提问（D3）。「每个阶段一次性提出 3-5 个问题」后加：每题附推荐答案和一句理由；能从账本推出的注明出处，否则标「PM 的推荐」；不得与账本已定结论冲突，觉得结论有问题就作为问题提出；没把握的不给推荐（D2） |
| AGENTS.md | 加一条「写规则要有出处」：工程配置、本工程实例、项目规范里的硬约束须有出处（已有规约、产品负责人确认、现有测试或接口契约）；「代码现在是这样」不算；没有出处的写「待确认」并在账本挂工作项 |
| 工程配置模板头注 | 加同义一句（供新工程） |
| manage-docs | `docs/tests/` 下加一行：`docs/tests/已知旧失败.md`，不分版本，由 QA 维护，规则见 `docs/rules/派活与交付.md`「五」 |
| sa-review | 新增一节「四、spec+plan 与回报的核对」（原「四」「五」顺延）：评 spec+plan 时核测试落点和每个任务的「覆盖」「依赖」；收回报时核实际改动是否越出可写范围（`派活与交付.md`「二」） |

- [ ] **Step 2：核内核引用仍完整**

Run: `python3 bin/test_kit.py`
Expected: 全过，69 项。`t_kernel_config_refs_are_profile_sections` 也在其中。

- [ ] **Step 3：核没有误改**

```bash
git diff --stat -- template/skills/insight-discovery/   # 无输出（D2）
grep -rn "sa-review.\{0,10\}「[四五]" template | head          # 无输出，或核对后都指向新编号
```

- [ ] **Step 4：跑三套测试，然后提交**

Run: `python3 bin/test_kit.py && python3 template/skills/team-ledger/test_team_ledger.py && bash template/.githooks/tests/hooks.test.sh`
Expected: 三套全过。

```bash
git commit -m "Interviews read the insight ledger; rules need a source; known-failures list" -- template/skills/requirements-analysis/SKILL.md template/AGENTS.md profile/docs/rules/工程配置.md template/skills/manage-docs/SKILL.md template/skills/sa-review/SKILL.md
```

---

### Task 4: 文档、整体审阅、发 v0.9.0、同步

**Files:**
- Modify: `docs/交接说明.md`：
  - §八新增「v0.9.0（2026-11-23，产品负责人需求）」，写明问题、D0–D3、改动、对工程的影响；
  - §六更新测试计数和「39 个内核文件」。
- Modify: `README.md`：只在描述内核文件的地方需要时更新。
- Modify: 设计文档的状态行，改为「已批准，v0.9.0 实施」。

- [ ] **Step 1：改文档，跑三套测试，提交**

Run: 三套测试命令（同 Task 3 第 4 步）。
Expected: 全过。

```bash
git commit -m "Docs for v0.9.0 dispatch and delivery" -- docs/交接说明.md README.md docs/superpowers/specs/2026-11-23-dispatch-delivery-design.md docs/superpowers/plans/2026-11-23-dispatch-delivery.md
```

- [ ] **Step 2：整体审阅**：在打标签和推送之前完成。派一个独立审阅代理，读本计划的 Review Focus、设计和 diff（范围 `28e6b36..HEAD`）。修完重要问题后再继续。

- [ ] **Step 3：打标签、推送 team-kit**

```bash
git tag -a v0.9.0 -m "Dispatch and delivery rules: dispatch fields, report format, evidence, known failures"
git push origin main --tags
```

Expected: `git ls-remote --tags origin v0.9.0` 有输出。

- [ ] **Step 4：同步 vista、prism**

对每个工程：
1. 先核对工作树，确认没有别人的暂存内容；
2. 运行 `bin/kit sync ../<工程>`；
3. `git add -- docs/rules/派活与交付.md`，再按 sync 打印的命令带路径提交。提交信息沿用各工程的惯例：
   - vista：`chore(infra): sync team-kit v0.9.0 — … (_infra)`
   - prism：`Sync team-kit v0.9.0: …`

Expected:
- `bin/kit check` 退出 0；
- 三处的 39 个内核文件 sha256 一致；
- `git show --stat HEAD` 里只有 kit 管理的路径；
- 两个工程都不推送。

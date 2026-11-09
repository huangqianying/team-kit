# 并行线落地 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把「并行线」（每条写代码的线一个工作树 + 分支，SA 合入，测试服排队累加验收）写进 team-kit 内核，发 v0.8.0 并同步到 vista、prism。

**Architecture:**
- 规则正文新立一份内核文件 `docs/rules/并行线.md`，承载设计 §5.1–§5.6.1。契约只改链路步骤、同角色并行和合入条款，并引用这份文件。这是设计 §8 交给实施者的选择：契约现在 170 行，全并进去就看不全了。
- 工程取值放进 `工程配置.md` 新增的「并行线」一节，`kit check` 把它当作软节：缺失只警告。
- 另加一条测试，保证内核里每一处「工程配置「X」」都能在 profile 里找到对应的节。

**Tech Stack:** Python 3 标准库（`bin/kit`、`bin/test_kit.py`），中文 Markdown 规则文件，git。

**Spec:** `docs/superpowers/specs/2026-11-09-parallel-dispatch-design.md`（决定 D1–D6，维护方判断 C1–C11，C8 已被 D6 取代）。

## Global Constraints

- **内核文件在所有工程逐字相同。** 只改 `template/`、`profile/`、`MANIFEST`、`bin/`、kit 自己的文档。不手改 vista / prism 的任何文件，sync 生成的除外。
- **工程取值的默认值写在内核里，并写明工程可以另设：**
  - 最多并行线数默认 **3**（D6）；
  - 测试服验收槽位数默认 **1**。
- **固定名称（全部照抄）：**

  | 对象 | 名称 |
  |---|---|
  | 线分支 | `lane/<短名>` |
  | 修复线 | `lane/<短名>-fix<N>` |
  | 工作树默认位置 | `../<工程目录名>.lanes/<短名>` |
  | 迭代规划里的必填节 | 「并行编排」 |
  | 增量链路的编排工作项 | `并行编排-<日期>` |
  | 测试服账本工作项 | `测试服验收`（槽位数大于 1 时为 `测试服验收-<槽位>`） |
  | 工程配置新节 | `## 并行线` |
  | 工程侧的待办工作项 | `parallel-lanes-adopt` |

- **内核不写死 `develop`**，一律写「集成分支（工程配置「分支与发布」里的日常开发分支）」（C11）。
- **兜底**：工程配置里没有「并行线」一节时，不开并行线，按原规则执行（C9）。
- **快速链路工作项默认不开线**（C10）。
- **措辞风格**：
  - 跟现有内核一致：简体中文，短句，关键约束加粗；
  - 不写变更由来（契约头注「本文只定规范，不记变更由来」）。
- **提交与推送**：
  - kit 内提交一律带路径：`git commit -m … -- <路径>`；
  - 只推送 team-kit；
  - 工程里只做带路径的本地提交，不推送。

## Review Focus

1. **工程还没补「并行线」一节就同步了内核。** 预期：`kit check` 退出 0，只给一条警告；契约写明此时不开线。测试 `t_check_soft_section_missing_only_warns`（Task 1）。
2. **内核里引用了「工程配置「并行线」」，但 profile 节名拼写不一致。** 预期：测试失败并点名。测试 `t_kernel_config_refs_are_profile_sections`（Task 1）。
3. **「每回合两步」改名为三步后，有地方还留着旧名，SA 照旧名找不到节。** 预期：内核里 `每回合两步` 零命中。Task 4 第 3 步用 grep 核。
4. **SA 照「同一工作树内协作」的旧条文，在主工作树里写代码线。** 预期：AGENTS 和契约里不再有「都在同一工作树内」这个前置条件。Task 3、Task 4 用 grep 核。
5. **新规则文件没进 MANIFEST，工程同步后缺这个文件。** 预期：`kit install` 后文件存在，`check` 无错。Task 2 第 2 步。

---

### Task 1: 工程配置新增「并行线」软节，加上引用一致性测试

**Files:**
- Modify: `profile/docs/rules/工程配置.md`：在「## 命令」节之后、「## 分支与发布」之前插入 `## 并行线`。删掉「命令」节末尾那行「**并行测试的隔离参数**」，它的内容并入新节。
- Modify: `bin/kit`：在 `PROFILE_DOC` 定义附近加常量；改第 141–147 行缺节判断。
- Test: `bin/test_kit.py`

**Interfaces:**
- Produces: `kit.SOFT_SECTIONS: set[str]`，值为 `{"## 并行线"}`。缺软节时的警告文字含 `缺节「并行线」`。

- [ ] **Step 1: 写失败测试**（加在 `t_check_profile_sections` 之后）

```python
def t_check_soft_section_missing_only_warns():
    d = new_repo()
    run("install", d)
    p = os.path.join(d, kit.PROFILE_DOC)
    s = open(p, encoding="utf-8").read()
    i = s.index("## 并行线\n"); j = s.index("\n## ", i + 1)
    open(p, "w", encoding="utf-8").write(s[:i] + s[j + 1:])
    errors, warns = kit.check(d, quiet=True)
    ok(not any("并行线" in e for e in errors), f"缺「并行线」不算错（{errors}）")
    ok(any("缺节「并行线」" in w for w in warns), "缺「并行线」给出警告")
    rc, _ = run("check", d)
    ok(rc == 0, "只缺软节时 check 退出 0")
    shutil.rmtree(d)


def t_kernel_config_refs_are_profile_sections():
    import re
    have = {s[3:] for s in kit.profile_sections()}
    files, _ = kit.kernel_files()
    missing = set()
    for rel in files:
        if rel.endswith(".md"):
            for name in re.findall(r"工程配置「([^」]+)」", open(os.path.join(kit.TEMPLATE, rel), encoding="utf-8").read()):
                if name not in have:
                    missing.add(f"{rel}: {name}")
    ok(not missing, f"内核引用的工程配置节都在 profile 里（缺：{sorted(missing)}）")
```

`kernel_files()` 已经把 MANIFEST 里以 `/` 结尾的目录展开成文件（`bin/kit:51`），`skills/**` 会被扫到。

- [ ] **Step 2: 跑测试，确认按预期失败**

Run: `python3 bin/test_kit.py`
Expected:
- 运行在 `t_check_soft_section_missing_only_warns` 中断，报 `ValueError: substring not found`（profile 里还没有「## 并行线」；测试运行器不捕获异常）；
- 先单独确认另一条测试能过：
  `python3 -c "import runpy,sys; m=runpy.run_path('bin/test_kit.py'); m['t_kernel_config_refs_are_profile_sections']()"`
  输出 `✓ 内核引用的工程配置节都在 profile 里`。

- [ ] **Step 3: 写 profile 的「## 并行线」节**

每行都用 `<例：…>` 开头，现有的占位检测（`"<例" in text`）才能认出没填的情况：

```markdown
## 并行线

> 本节缺失或未填时，本工程**不开并行线**，按原规则执行（同一工作树、带路径提交）。规则见 `docs/rules/并行线.md`。

- **最多并行线数**：<例：默认（即 3）；或写具体数字>
- **工作树位置**：<例：默认（即 `../<工程目录名>.lanes/<短名>`）；或写具体位置，不得放在工程目录内>
- **工作树初始化**：<例：新工作树里要补的被忽略文件及命令（依赖安装、本地配置链接）；无则写「无」>
- **线内测试环境**：<例：每条线的系统测试环境怎么隔离：端口、数据库、compose 项目名、临时目录、浏览器 profile；可在本机，也可在测试服上加前缀并排部署>
- **测试服验收槽位数**：<例：默认（即 1）；大于 1 时写各槽位的环境名与部署参数>
```

- [ ] **Step 4: 在 `bin/kit` 加 `SOFT_SECTIONS = {"## 并行线"}`，改缺节判断**

缺失的节如果在 `SOFT_SECTIONS` 里，就加进 `warns`，文字为：
`工程配置 缺节「并行线」（未填时本工程不开并行线，按原规则执行）`
其余缺节仍加进 `errors`，原文不变。

- [ ] **Step 5: 跑三套测试，全部通过**

Run: `python3 bin/test_kit.py && python3 template/skills/team-ledger/test_team_ledger.py && bash template/.githooks/tests/hooks.test.sh`
Expected:
- kit 套件通过数为 53 + 本任务新增的断言数（4），失败为 0；
- 账本 84 项、钩子 102 项照旧全过。

- [ ] **Step 6: 提交**

```bash
git commit -m "kit: add the 并行线 config section as a soft section" -- profile/docs/rules/工程配置.md bin/kit bin/test_kit.py
```

---

### Task 2: 新增内核规则文件 `docs/rules/并行线.md`

**Files:**
- Create: `template/docs/rules/并行线.md`
- Modify: `MANIFEST`：在 `docs/rules/ui-demo.html` 之后加一行 `docs/rules/并行线.md`。

**Interfaces:**
- Consumes: Task 1 的节名「并行线」。正文里引用一律写「工程配置「并行线」」。
- Produces: 供后续任务引用的节名：
  - `并行线.md`「一、何时判并行」
  - 「二、并行编排」
  - 「三、线的创建与收尾」
  - 「四、线内测试」
  - 「五、合入集成分支」
  - 「六、测试服与验收」
  - 「七、进 main」
  - 「八、SA 的职责」

  Task 3–5 按这些名字引用，编号和名字不能改。

- [ ] **Step 1: 写正文**

文件头照契约的头注格式写两行：本文只定规范，不记变更由来；工程取值见工程配置「并行线」，缺失时不开线。

各节必须写进的规则按下表（数值、名称照 Global Constraints 抄）：

| 节 | 必须写进的规则（出处） |
|---|---|
| 一 | 设计 §5.1 的表格和判据；默认并行，选串行要落账写理由；快速链路默认不开线（C10） |
| 二 | 设计 §5.2 的六项；增量链路简版写四项 |
| 三 | 设计 §5.3 全部：分支名、工作树位置（C1）、初始化、什么提交在线分支上、谁进工作树、不 rebase 也不 squash（C2）、收尾前先读目标 |
| 四 | 设计 §5.4；测试报告写明被测提交 |
| 五 | 设计 §5.5 的五步；`阻断` 先在线内修（C3）；`git merge-tree --write-tree` 预检，冲突退回线内（C5）；迁移在合入前改成下一个空号，合入后不得再改；暂存区不干净就稍后重试，不替别人取消暂存；合入后由线的 SE 跑「构建 + 研发自测全量」（C4） |
| 六 | 设计 §5.6；`测试服验收` 账本用法：部署时落 `进行中`，等验收时落 `阻塞 --blocker-role owner`，没有待验收内容时落 `完成` |
| 七 | 设计 §5.6.1（D5） |
| 八 | 设计 §5.8：有线在跑时 SA 不写产品代码；巡检第 3 步；最多并行线数 |

- [ ] **Step 2: 核文件已进内核**

Run: `python3 bin/test_kit.py`
Expected:
- 全部通过；
- `t_install_then_check_clean` 里「内核文件全部就位」覆盖了新文件；
- `t_kernel_config_refs_are_profile_sections` 通过（新文件引用的「工程配置「并行线」」在 profile 里有对应的节）。

再跑：`grep -c "develop" template/docs/rules/并行线.md`
Expected: `0`（C11：只写「集成分支」）。

- [ ] **Step 3: 提交**

```bash
git add -- template/docs/rules/并行线.md
git commit -m "Kernel: add the parallel lanes rule" -- template/docs/rules/并行线.md MANIFEST
```

---

### Task 3: 契约改链路、同角色并行与合入条款

**Files:**
- Modify: `template/docs/rules/团队协作契约.md`

**Interfaces:**
- Consumes: Task 2 的节名。

- [ ] **Step 1: 逐处改写**

| 位置 | 改成 |
|---|---|
| 头注第三段（「本工程的产品、目录…见工程配置」那行）之后 | 加一行：多条线并行时的工作树、合入与测试服验收见 `docs/rules/并行线.md` |
| §二.2 第 4 步「合入」 | 产品负责人一句话后，SA 合入集成分支；进 `main` 按 `并行线.md`「七、进 main」 |
| §二.3 第 5 步「合入」 | 同上 |
| §二.3 表格之后 | 加一段「多项同时进行」：两个以上增量项同时开工时，先按 `并行线.md`「二、并行编排」写简版，再派活 |
| §二.4 阶段 2 | 迭代规划的内容里加上「**并行编排**（必填，见 `并行线.md`「二」）」 |
| §二.4 阶段 3 | 「逐轮执行」改为「按并行编排推进，可并行的迭代各开一条线（`并行线.md`）；每个迭代各自验收」；下一步的描述随之改 |
| 3.3 迭代验收 | 加：部署对象是集成分支上的提交，按合入顺序排队，累加部署；验收不通过就在集成分支上修，不回退（`并行线.md`「六」） |
| §三「同角色并行」 | 四个前置条件改成设计 §5.7 的四条；「有一条不满足就串行」改成「不满足的部分串行，其余仍然并行」；最后一条「同一工作树内的各实例…」改成：只写文档的实例在主工作树里带路径提交，写代码的线各在自己的工作树里 |
| §五「合入决定权」 | 加：线合入集成分支是 SA 的集成动作；集成分支进 `main` 要等已合入的各项都验收通过（`并行线.md`「七」） |

- [ ] **Step 2: 核残留**

Run: `grep -n "都在同一工作树内\|逐轮执行" template/docs/rules/团队协作契约.md`
Expected: 无输出。

Run: `grep -c "并行线.md" template/docs/rules/团队协作契约.md`
Expected: 至少 `5`。

- [ ] **Step 3: 跑 kit 测试，然后提交**

Run: `python3 bin/test_kit.py`，Expected: 全部通过。

```bash
git commit -m "Contract: parallel by default, lanes, per-iteration acceptance" -- template/docs/rules/团队协作契约.md
```

---

### Task 4: AGENTS、账本巡检、换端交接

**Files:**
- Modify: `template/AGENTS.md`：第 65 行的引用名；第 117–120 行「同一工作树内协作」。
- Modify: `template/skills/team-ledger/SKILL.md`：第 50 行起。
- Modify: `template/skills/team-ledger/DESIGN.md:78`
- Modify: `template/docs/rules/双端协作与交接.md`：第 28 行；「额度耗尽或切换工具」第 2 步、第 5 步。

- [ ] **Step 1: 改 `team-ledger` SKILL**

把「SA 值守的每回合两步」改名为「SA 值守的每回合三步」，加第 3 步：

> 3. 对照进行中版本的「并行编排」：已满足开工条件却还没派出的线；已有 QA 报告却还没合入的线；没写理由就串行的项。逐条派出、合入或补理由（`docs/rules/并行线.md`「八」）。

- [ ] **Step 2: 改引用与 AGENTS**

- AGENTS:65、DESIGN.md:78、双端协作:28 里的「每回合两步」改为「每回合三步」。
- AGENTS「同一工作树内协作」整节改名为「工作树分工」，改写为三点：
  - 文档类工作在主工作树里，按上面的提交纪律；
  - 写代码的并行线各在自己的工作树和分支上（`docs/rules/并行线.md`）；
  - 评审和取证不另建工作树：各工作树共用一个对象库，按 `commit:path` 读。
- AGENTS「多角色同 worktree 下的提交纪律」标题不改（有引用），首句前补一句：每棵工作树都适用。

- [ ] **Step 3: 改换端交接**

- 第 2 步「核对 … `git worktree list`」之后补：与账本里登记的线逐条对上；不认账本以外的工作树，例如工具自建的。
- 第 5 步补：未合入的线按原分支、原工作树续派，不新开线。

- [ ] **Step 4: 核残留**

Run: `grep -rn "每回合两步\|同一工作树内协作" template`
Expected: 无输出。

- [ ] **Step 5: 跑账本与 kit 测试，然后提交**

Run: `python3 template/skills/team-ledger/test_team_ledger.py && python3 bin/test_kit.py`
Expected: 账本 84 项全过；kit 全过。

```bash
git commit -m "SA routine gains a lane check; worktree split in AGENTS" -- template/AGENTS.md template/skills/team-ledger/SKILL.md template/skills/team-ledger/DESIGN.md template/docs/rules/双端协作与交接.md
```

---

### Task 5: 角色正文与 SA 评审

**Files:**
- Modify: `template/docs/rules/roles/se.md:33`
- Modify: `template/docs/rules/roles/qa.md:34`
- Modify: `template/docs/rules/roles/pm.md:17`
- Modify: `template/skills/sa-review/SKILL.md`：在「二、关键引用的一致性」之后新增「三、与并行编排对账」，原「三」「四」顺延成「四」「五」。

- [ ] **Step 1: 改写**

**se.md** 第 33 行之后补一段：
- 派活单写明你所在的线时，只在该线的工作树里改动、提交到线分支；
- 合入冲突由你在线内合入集成分支后解决；
- 迁移脚本在合入前改成集成分支上的下一个空号；
- 合入后由你在合并提交上跑「构建 + 研发自测全量」；
- 详见 `docs/rules/并行线.md`「三」「五」。

**qa.md** 第 34 行：
- 「本工程的隔离参数见工程配置「命令」」改为「见工程配置「并行线」」，这是线内测试环境的位置；
- 补：测试某条线时在该线的工作树和隔离环境里测，报告写明被测提交，测试产物提交到线分支。

**pm.md** 第 17 行之后补一条：评迭代规划时，也核「并行编排」有没有把一条 AC 拆到两条线却没有一方负责。

**sa-review** 新增的「三、与并行编排对账」写一条：评 spec+plan 时，核本线的改动路径、迁移数量、共享文件，与并行编排的归属一致；越界按发现定级。

- [ ] **Step 2: 核残留并跑测试**

Run: `grep -rn "工程配置「命令」" template/docs/rules/roles/qa.md`
Expected: 只剩与隔离参数无关的命中，或无输出。

Run: `python3 bin/test_kit.py`
Expected: 全过，`t_kernel_config_refs_are_profile_sections` 也在其中。

- [ ] **Step 3: 提交**

```bash
git commit -m "Roles and sa-review follow the lanes rule" -- template/docs/rules/roles/se.md template/docs/rules/roles/qa.md template/docs/rules/roles/pm.md template/skills/sa-review/SKILL.md
```

---

### Task 6: 文档、发版 v0.8.0、同步两个工程

**Files:**
- Modify: `README.md`：「新工程首次落地后要做的」第一条补：「并行线」一节不填就不开线。
- Modify: `docs/交接说明.md`：
  - §八 新增「v0.8.0（2026-11-09，产品负责人需求）」：问题、决定 D1–D6、改了哪些文件、对工程的影响；
  - §六 的测试计数更新为实际数；
  - §5.2 记两个工程的 `parallel-lanes-adopt`。
- Modify: `docs/superpowers/specs/2026-11-09-parallel-dispatch-design.md`：状态行改为「已批准，v0.8.0 实施」。

- [ ] **Step 1: 改文档，跑三套测试**

Run: `python3 bin/test_kit.py && python3 template/skills/team-ledger/test_team_ledger.py && bash template/.githooks/tests/hooks.test.sh`
Expected: 三套全过。把实际计数写进交接说明 §六。

- [ ] **Step 2: 提交、打标签、推送 team-kit**

```bash
git commit -m "Docs for v0.8.0 parallel lanes" -- README.md docs/交接说明.md docs/superpowers/specs/2026-11-09-parallel-dispatch-design.md docs/superpowers/plans/2026-11-09-parallel-lanes.md
git tag -a v0.8.0 -m "Parallel lanes: worktree per code lane, SA merges, queued cumulative acceptance"
git push origin main --tags
```

Expected: `git status --short` 为空，`git ls-remote --tags origin v0.8.0` 有输出。

- [ ] **Step 3: 同步 vista、prism**

对每个工程：
1. 运行 `bin/kit sync ../<工程>`；
2. 照它打印的 `git -C … commit -m "…" -- <路径>` 带路径提交，新文件 `并行线.md` 先 `git add --` 再提交；
3. 运行 `bin/kit check ../<工程>`。

Expected:
- check 退出 0；
- 警告里有 `缺节「并行线」`；
- `git -C ../<工程> show --stat HEAD` 里只有 kit 管理的路径；
- 两个工程都不推送。

- [ ] **Step 4: 核内核逐字一致**

Run: 对 MANIFEST 列出的每个文件（目录展开），比较 kit `template/`、vista、prism 三份的 sha256。
Expected: 38 个文件三方一致（原 37 个，加 `并行线.md`）。

- [ ] **Step 5: 在两个工程的账本里各挂一个待办**

```bash
python3 ../<工程>/skills/team-ledger/team-ledger.py append --role sa --item parallel-lanes-adopt --status 阻塞 --blocker-role sa --blocker "工程配置分支策略禁止分支与工作树，需改策略并填「并行线」节后才能启用 v0.8.0 并行线" --note "team-kit v0.8.0 已同步；未填前按原规则执行"
```

Expected: `stale --hours 0` 里能看到该项，接续方为 SA。

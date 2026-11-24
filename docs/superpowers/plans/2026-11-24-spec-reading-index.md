# 规范按需阅读索引 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** UI 设计规范开头加「按需阅读」一节；工程配置模板「项目规范」表加「何时读」列，`kit check` 对缺列只警告；SE、PM、QA、契约、AGENTS、diff-impact 的读法改成按索引读。发 v0.12.0，同步 vista、prism。

**Architecture:**
- 索引是 `template/docs/rules/UI设计规范.md` 里一个不编号的 `## 按需阅读` 节，放在引言之后、`## 0.` 之前，正文与节号一字不动。
- 「何时读」只改工程配置模板（`profile/`，只在工程缺文件时生成），工程里已有的配置由各工程自己改；`bin/kit check` 发现「项目规范」表头没有「何时读」时给警告，不报错。
- 全部判据写进 `bin/test_kit.py`：索引的结构与覆盖、模板与警告、各处措辞。

**Tech Stack:** 中文 Markdown；Python 3 标准库（`bin/kit`、`bin/test_kit.py`）；git。

**Spec:** `docs/superpowers/specs/2026-11-24-spec-reading-index-design.md`

## Global Constraints

- **内核逐字相同。** 只改 `template/`、`profile/`、`bin/kit`、`bin/test_kit.py` 和 kit 自己的文档；工程侧只有 `bin/kit sync` 带来的改动。
- **不改 UI 设计规范的规则内容和节号**，不给 §22 补节号；`ui.md` 不改（UI 出原型通读全文，依据恰两份）。
- **索引口径（照抄设计）**：索引给出最少要读的范围，拿不准就读全文；表里没有的任务读全文。
- **通读全文的场合**：UI 角色出原型；PM 审原型、审 SE 实现的界面；新增页面；拿不准该读哪些节时。
- **本工程实例每次整份读。**
- **每次都读**：§0、§1、§2.4、§4、§20、§21、§22（与设计「每次都读」表逐行一致，含「为什么」一列）。
- **按任务再读**：与设计「按任务再读」表 18 行逐行一致。
- **写法**：`§N` 表示整节（含全部子节），`§N.M` 只读该子节；每个一级节 §0–§24 在两张表里至少整节出现一次。
- **`kit check` 警告原文**：`工程配置「项目规范」表缺「何时读」列（未加时各角色按原必读段读）`。
- **措辞**：简体中文、短句；规则文件不写变更由来；保持各角色文件原有编号与格式。
- **提交与推送**：kit 内带路径提交（`git commit -m … -- <路径>`）；只推送 team-kit；工程只做本地带路径提交，不推送。
- **版本**：v0.12.0。

## Review Focus

1. **索引里的说明文字冒充覆盖**：「写法」一句若写成「§0–§24」，按全文抓节号会把 0 和 24 算成已覆盖。覆盖判据只从两张表的表格行（以 `|` 开头）里取节号，Task 1 测试照此写。
2. **索引里出现标题行，打断现有断点测试**：`t_demo_breakpoints_match_spec` 用 `spec.index("### 4.1")`、`spec.index("## 5.")` 取第一次出现处。索引节里不得有以 `#` 开头的行（节名本身除外），也不得出现 `## 5.` 字样。Task 1 测试核前者，现有断点测试核后者。
3. **节号按级别匹配会误判**：§16.1–§16.4、§11.2.1 是 `####`，§11.7.1 是 `###`。正文节号从 `##`–`####` 标题里统一按编号取，不看级别。Task 1 测试用这个集合。
4. **工程配置里根本没有表**，或「项目规范」节被删：没有表也要警告缺列；缺节本身仍按现有规则报错，不重复报。Task 2 测试核「有节无表」给警告。
5. **旧措辞残留在别处**：「列给 SE / QA / PM 的必读文件」「各角色必读范围」「涉及前端时必读」「按 `docs/rules/UI设计规范.md` 自查」改完后内核里不再出现。Task 3 测试对整个 `template/` 扫这几句。

---

### Task 1：UI 设计规范加「按需阅读」

**Files:**
- Modify: `template/docs/rules/UI设计规范.md`（第 10 行 `---` 之后、第 12 行 `## 0. 设计哲学` 之前插入 `## 按需阅读` 一节，节后加一条 `---`）
- Test: `bin/test_kit.py`

**Interfaces:**
- Produces: 常量 `UI_SPEC = "docs/rules/UI设计规范.md"`；`_ui_index(text) -> str`（取 `## 按需阅读` 到下一个 `\n## ` 之间的文字）；`_spec_numbers(text) -> set[str]`（正文 `^#{2,4} ` 标题里的节号，如 `"0"`、`"2.4"`、`"11.2.1"`）。

- [ ] **Step 1：写失败的测试 `t_ui_spec_reading_index`**

```python
def t_ui_spec_reading_index():
    import re
    spec = open(os.path.join(kit.TEMPLATE, UI_SPEC), encoding="utf-8").read()
    ok("\n## 按需阅读\n" in spec, "UI 设计规范有「按需阅读」一节")
    ok("## 按需阅读" in spec and spec.index("## 按需阅读") < spec.index("\n## 0. "), "「按需阅读」在 §0 之前")
    idx = _ui_index(spec)
    ok(not any(l.startswith("#") for l in idx.splitlines()), "索引节里没有标题行")
    for s in ["拿不准", "读全文", "本工程实例", "整份", "出原型", "审原型", "新增页面"]:
        ok(s in idx, f"索引写了「{s}」")
    nums = _spec_numbers(spec)
    ok({str(i) for i in range(25)} <= nums, f"正文节号解析到 §0–§24（{sorted(nums)[:5]}…）")
    refs = re.findall(r"§(\d+(?:\.\d+)*)", idx)
    ok(refs and all(r in nums for r in refs), f"索引引用的节号都存在（多出 {sorted(set(refs) - nums)}）")
    rows = "\n".join(l for l in idx.splitlines() if l.startswith("|"))
    whole = set(re.findall(r"§(\d+)(?![\d.])", rows))
    ok(whole == {str(i) for i in range(25)}, f"§0–§24 在表格里都整节出现（缺 {sorted({str(i) for i in range(25)} - whole, key=int)}）")
    always = _section(idx, "**每次都读**", "**按任务再读**")
    ok(set(re.findall(r"§(\d+(?:\.\d+)*)", always)) == {"0", "1", "2.4", "4", "20", "21", "22"}, "「每次都读」恰为 §0、§1、§2.4、§4、§20、§21、§22")
```

`_spec_numbers` 用 `re.findall(r"^#{2,4} (\d+(?:\.\d+)*)\.?\s", text, re.M)`。

- [ ] **Step 2：跑测试，确认失败**

Run: `python3 bin/test_kit.py 2>&1 | tail -15`
Expected: `t_ui_spec_reading_index` 下有 ✗（缺「按需阅读」一节），其余照旧通过。

- [ ] **Step 3：写「按需阅读」一节**

内容按设计「1. UI 设计规范「按需阅读」一节」：通读全文的场合；其余场合的读法（先「每次都读」，再按任务、取并集，表里没有的读全文）；本工程实例每次整份读；写法一句（`§N` 整节、`§N.M` 只读该子节，不写「§0–§24」这类区间）；「每次都读」表（节 | 为什么每次都读）；「按任务再读」表（本次任务涉及 | 再读）。两张表的小标题分别写成 `**每次都读**`、`**按任务再读**`（粗体段落，不用标题行）；正文提到它们时写「每次都读」，不加粗，免得测试截错段。设计里标「维护方判断」的括注不搬进规范。

- [ ] **Step 4：跑测试，确认通过**

Run: `python3 bin/test_kit.py 2>&1 | tail -3`
Expected: `✓ 全部通过`，`t_demo_breakpoints_match_spec` 仍通过。

- [ ] **Step 5：变异核对**。把规范备份到工作区，分别 ① 删掉「按任务再读」里 §24 那一行，② 把「每次都读」的 §4 改成 §4.1，③ 在索引里加一行 `### x`，各跑一次测试，每次都应有 ✗；最后从备份恢复并确认全绿。

- [ ] **Step 6：提交**

```bash
git commit -m "UI spec: reading index before §0" -- template/docs/rules/UI设计规范.md bin/test_kit.py
```

---

### Task 2：工程配置模板加「何时读」，`kit check` 缺列警告

**Files:**
- Modify: `profile/docs/rules/工程配置.md:61-72`
- Modify: `bin/kit`（`check()` 里工程配置那一段之后）
- Test: `bin/test_kit.py`

**Interfaces:**
- Produces: `bin/kit` 中 `profile_spec_table_has_when(text: str) -> bool`：取 `## 项目规范` 到下一个 `\n## ` 之间第一条以 `|` 开头的行，含「何时读」返回 True；没有该节返回 True（缺节已另报错）；有节无表返回 False。常量 `WHEN_COL_WARN` 为 Global Constraints 里的警告原文。

- [ ] **Step 1：写失败的测试**

```python
def t_profile_template_has_when_column():
    t = open(os.path.join(kit.PROFILE, kit.PROFILE_DOC), encoding="utf-8").read()
    sec = _section(t, "## 项目规范")
    head = next((l for l in sec.splitlines() if l.startswith("|")), "")
    ok("何时读" in head, f"模板「项目规范」表头有「何时读」（{head}）")
    ok("动手前必读的项目规范" not in t, "模板删掉了「动手前必读的项目规范」一段")
    ok("页面与组件命名约定" in sec, "「页面与组件命名约定」一段保留")

def t_check_warns_missing_when_column():
    d = new_repo()
    run("install", d)
    errors, warns = kit.check(d, quiet=True)
    ok(not any("何时读" in w for w in warns), "新装的工程配置有「何时读」：不警告")
    p = os.path.join(d, kit.PROFILE_DOC)
    s = open(p, encoding="utf-8").read()
    old = s.replace("| 规范 | 位置 | 何时读 |\n|---|---|---|", "| 规范 | 位置 |\n|---|---|")
    open(p, "w", encoding="utf-8").write(old)
    errors, warns = kit.check(d, quiet=True)
    ok(kit.WHEN_COL_WARN in warns, f"表头缺「何时读」给出警告（{warns}）")
    ok(not any("何时读" in e for e in errors), "缺列不算错")
    rc, _ = run("check", d)
    ok(rc == 0, "只缺「何时读」时 check 退出 0")
    sec = _section(old, "## 项目规范")
    open(p, "w", encoding="utf-8").write(old.replace(sec, "\n无表\n"))
    _, warns = kit.check(d, quiet=True)
    ok(kit.WHEN_COL_WARN in warns, "「项目规范」有节无表也警告")
    shutil.rmtree(d)
```

`t_check_warns_missing_when_column` 里 `replace` 的原文要与 Step 3 写出的模板表头逐字一致；不一致时以模板为准改测试，并在账本记 Ruling。

- [ ] **Step 2：跑测试，确认失败**

Run: `python3 bin/test_kit.py 2>&1 | tail -20`
Expected: 两个新测试有 ✗（模板无「何时读」、`kit.WHEN_COL_WARN` 不存在会抛 AttributeError——先在 `bin/kit` 只加常量再跑，确认是断言失败而不是异常）。

- [ ] **Step 3：改模板**。表改为三列，行与「何时读」取值按设计「2. 工程配置「项目规范」加「何时读」」（前端技术栈、产品前端主题、原型主题三行各写「涉及前端时」；「其他项目规范」的「何时读」写占位 `<例：涉及权限、鉴权、数据隔离时；开工前都读的写「必读」，可限定角色，如「SE、QA 必读」>`）。删掉 `**SE / QA / UI 动手前必读的项目规范**` 一段；表下加一句：PM、SE、QA 按「何时读」对照本次任务读；UI 只依据需求文档与 UI 设计规范，项目规范里要 UI 遵守的由 PM 写进需求。「页面与组件命名约定」不动。

- [ ] **Step 4：实现 `profile_spec_table_has_when`**，在 `check()` 读到工程配置正文的那一段里调用，返回 False 时 `warns.append(WHEN_COL_WARN)`。

- [ ] **Step 5：跑测试，确认通过**

Run: `python3 bin/test_kit.py 2>&1 | tail -3`
Expected: `✓ 全部通过`。

- [ ] **Step 6：变异核对**。把 `check()` 里那句 `warns.append` 注释掉、把模板表头的「何时读」删掉，各跑一次，应有 ✗；恢复后全绿。

- [ ] **Step 7：提交**

```bash
git commit -m "Profile: 何时读 column in 项目规范; kit check warns when missing" -- profile/docs/rules/工程配置.md bin/kit bin/test_kit.py
```

---

### Task 3：角色文件与规则文字改成按索引读

**Files:**
- Modify: `template/docs/rules/roles/se.md:6,8,19`、`template/docs/rules/roles/pm.md:8,10`、`template/docs/rules/roles/qa.md:6`
- Modify: `template/docs/rules/团队协作契约.md:50`
- Modify: `template/AGENTS.md:93`（§3.3）
- Modify: `template/skills/diff-impact/SKILL.md:49`
- Test: `bin/test_kit.py`

**Interfaces:**
- Consumes: Task 1 的 `UI_SPEC`；Task 2 模板里的列名「何时读」；现有 `_section`、`_lines_with`。

- [ ] **Step 1：写失败的测试 `t_reading_rules_use_index`**

```python
def t_reading_rules_use_index():
    rd = lambda rel: open(os.path.join(kit.TEMPLATE, rel), encoding="utf-8").read()
    item = lambda text, n: next((l for l in text.splitlines() if l.startswith(f"{n}. ")), "")
    se, pm, qa = rd("docs/rules/roles/se.md"), rd("docs/rules/roles/pm.md"), rd("docs/rules/roles/qa.md")
    for name, t in (("se", se), ("pm", pm), ("qa", qa)):
        ok("何时读" in item(t, 2), f"{name}.md 第 2 条按「何时读」读项目规范")
    s4 = item(se, 4)
    ok(all(x in s4 for x in ["按需阅读", "新增页面", "通读", "本工程实例", "整份"]), "se.md 第 4 条：按需阅读、新增页面通读、实例整份读")
    p4 = item(pm, 4)
    ok(all(x in p4 for x in ["按需阅读", "审原型", "通读"]) and "界面" in p4, "pm.md 第 4 条：审原型和审界面通读，写需求按需阅读")
    ls = _lines_with(se, "自查")
    ok(bool(ls) and all("按需阅读" in l for l in ls), "se.md 快速链路自查一句引用按需阅读")
    c50 = next((l for l in rd("docs/rules/团队协作契约.md").splitlines() if l.startswith("| 2 开发 |")), "")
    ok("按需阅读" in c50, "契约快速链路第 2 棒自查引用按需阅读")
    a33 = _section(rd("AGENTS.md"), "### 3.3", "\n### ")
    ok("按需阅读" in a33 and "何时读" in a33, "AGENTS §3.3 写了按需阅读与何时读")
    di = next((l for l in rd(DIFF_IMPACT).splitlines() if l.startswith("1. **读上下文。**")), "")
    ok("何时读" in di and "按需阅读" in di, "diff-impact 第 1 步按何时读与按需阅读")
    ok("按需阅读" not in rd("docs/rules/roles/ui.md"), "ui.md 不改（出原型通读全文）")
    stale = ["列给 SE 的必读", "列给 QA 的必读", "列给 PM 的必读", "各角色必读范围",
             "涉及前端时必读", "涉及界面时必读", "UI设计规范.md` 自查"]
    hits = [(rel, s) for rel in kit.kernel_files()[0] if rel.endswith(".md")
            for s in stale if s in rd(rel)]
    ok(hits == [], f"内核里不再有旧措辞（{hits}）")
```

- [ ] **Step 2：跑测试，确认失败**

Run: `python3 bin/test_kit.py 2>&1 | tail -20`
Expected: `t_reading_rules_use_index` 有多条 ✗，其余照旧通过。

- [ ] **Step 3：改文字**，按设计「3. 读法写进哪里」逐行改：
  - se.md 第 2 条、qa.md 第 2 条、pm.md 第 2 条：按「项目规范」表的「何时读」对照本次任务读；表里还没有这一列时，按原来的必读段读。se、qa 原有的括注（接口、鉴权…；权限、隔离…）保留。
  - se.md 第 4 条：前半句改为「涉及前端时按它开头「按需阅读」读，新增页面通读全文；本工程实例整份读」，后面原型一段原样保留。
  - se.md 第 19 行、契约第 50 行：「改到界面按 `docs/rules/UI设计规范.md` 自查」改为按其开头「按需阅读」读后自查。
  - pm.md 第 4 条：审原型、审 SE 实现的界面时通读全文；写涉及界面的需求时按「按需阅读」读；`skills/ui-design/SKILL.md` 照旧一起读。
  - AGENTS.md §3.3：加一句「按需阅读见规范开头；出原型、审界面、新增页面通读全文」；第 93 行「及各角色必读范围」改为「及何时读」。
  - diff-impact 第 1 步：「与这次改动相关的规范」后补「（按「何时读」一列判断；UI 设计规范按其开头「按需阅读」）」。

- [ ] **Step 4：跑测试，确认通过**

Run: `python3 bin/test_kit.py 2>&1 | tail -3`
Expected: `✓ 全部通过`（含 `t_diff_impact_in_kernel`、`t_diff_impact_referenced` 照旧通过）。

- [ ] **Step 5：变异核对**。把 se.md 第 19 行改回旧句、删掉 pm.md 第 4 条的「审原型」、把 AGENTS 的「何时读」改回「各角色必读范围」，各跑一次应有 ✗；恢复后全绿。

- [ ] **Step 6：提交**

```bash
git commit -m "Roles and rules read specs via index and 何时读" -- template/docs/rules/roles/se.md template/docs/rules/roles/pm.md template/docs/rules/roles/qa.md template/docs/rules/团队协作契约.md template/AGENTS.md template/skills/diff-impact/SKILL.md bin/test_kit.py
```

---

### Task 4：文档、整体审阅、发版、同步

**Files:**
- Modify: `docs/交接说明.md`（§5.2 两个工程要补「何时读」的事项；§六 kit 测试项数；§八 加 v0.12.0）

- [ ] **Step 1：写文档**。§5.2 按设计「5. 对工程」写 vista、prism 两条（prism 含两个 skill 不在表里、UI 那条与「恰两份」冲突应改由 PM 写进需求）；§六 测试项数照实际输出填；§八 写 v0.12.0 改了什么、`kit check` 新警告。带路径提交。
- [ ] **Step 2：整体审阅**。`review-package` 生成审阅包，派 opus 子代理审，带上 spec、plan、本节 Review Focus、账本 Ruling 行。Critical / Important 一轮修完，每条先写失败的测试；Minor 记进交接说明 §5.1。
- [ ] **Step 3：发版**

Run（依次）：
- `python3 bin/test_kit.py`、`python3 template/skills/team-ledger/test_team_ledger.py`、`python3 template/skills/team-check/test_team_check.py`、`bash template/.githooks/tests/hooks.test.sh`
  Expected: 全部通过。
- `git tag -a v0.12.0 -m "v0.12.0: spec reading index"`，`git push origin main v0.12.0`
- 对 `../vista`、`../prism` 各执行：`bin/kit sync <工程>`；带路径提交 sync 改动的文件（vista：`chore(infra): sync team-kit v0.12.0 — spec reading index (_infra)`；prism：`Sync team-kit v0.12.0: spec reading index`）；`bin/kit check <工程>`。
  Expected: check 退出 0，并给出 `WHEN_COL_WARN` 警告（两个工程都还没加列）；三个仓库全部内核文件 sha256 一致；工程不推送，工程配置不动。
- [ ] **Step 4：记账**。交接说明 §八 补发版验证结果，带路径提交并推送 team-kit；更新记忆 `helix-absorption.md`。

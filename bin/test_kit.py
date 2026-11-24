#!/usr/bin/env python3
"""bin/kit 的判据。运行：python3 bin/test_kit.py（全部在临时目录里建 git 仓库，不碰任何真实工程）。"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.realpath(__file__))
kit = SourceFileLoader("kit", os.path.join(HERE, "kit")).load_module()

passed, failed = 0, 0


def ok(cond, msg):
    global passed, failed
    if cond:
        passed += 1
        print("  ✓ " + msg)
    else:
        failed += 1
        print("  ✗ " + msg)


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = kit.main(list(argv))
    return rc, out.getvalue() + err.getvalue()


def new_repo():
    d = tempfile.mkdtemp(prefix="kit-test-")
    subprocess.run(["git", "init", "-q", d], check=True)
    subprocess.run(["git", "-C", d, "config", "user.email", "t@example.invalid"], check=True)
    subprocess.run(["git", "-C", d, "config", "user.name", "t"], check=True)
    return d


def commit_all(d):
    subprocess.run(["git", "-C", d, "add", "-A"], check=True)
    subprocess.run(["git", "-C", d, "commit", "-q", "-m", "x", "--no-verify"], check=True)


def fill_profile(d):
    p = os.path.join(d, kit.PROFILE_DOC)
    s = open(p, encoding="utf-8").read().replace("<例", "<").replace("<…>", "x")
    open(p, "w", encoding="utf-8").write(s)


def t_install_then_check_clean():
    d = new_repo()
    rc, out = run("install", d)
    ok(rc == 0, "install 成功")
    files, _ = kit.kernel_files()
    ok(all(os.path.exists(os.path.join(d, f)) for f in files), "内核文件全部就位")
    ok(os.path.islink(os.path.join(d, ".claude/skills")) and os.readlink(os.path.join(d, ".claude/skills")) == "../skills", ".claude/skills 软链")
    ok(os.path.exists(os.path.join(d, kit.PROFILE_DOC)), "生成工程配置模板")
    ok(".team-ledger/" in open(os.path.join(d, ".gitignore")).read(), ".gitignore 补上账本目录")
    hp = subprocess.run(["git", "-C", d, "config", "--get", "core.hooksPath"], capture_output=True, text=True).stdout.strip()
    ok(hp == ".githooks", "钩子已装（core.hooksPath=.githooks）")
    errors, warns = kit.check(d, quiet=True)
    ok(errors == [], f"安装后 check 无错（{errors}）")
    ok(any("占位" in w for w in warns), "工程配置未填时给出提醒")
    shutil.rmtree(d)


def t_check_detects_drift():
    d = new_repo()
    run("install", d)
    with open(os.path.join(d, "AGENTS.md"), "a", encoding="utf-8") as f:
        f.write("\n本工程私改一行\n")
    os.remove(os.path.join(d, "docs/rules/roles/qa.md"))
    open(os.path.join(d, "skills/team-ledger/extra.md"), "w").write("x")
    errors, _ = kit.check(d, quiet=True)
    ok(any("不一致" in e and "AGENTS.md" in e for e in errors), "改过的内核文件判为不一致")
    ok(any("缺失" in e and "qa.md" in e for e in errors), "删掉的内核文件判为缺失")
    ok(any("多出" in e and "extra.md" in e for e in errors), "内核目录里多出的文件被报出")
    rc, _ = run("check", d)
    ok(rc == 1, "check 有差异时退出 1")
    shutil.rmtree(d)


def t_check_profile_sections():
    d = new_repo()
    run("install", d)
    p = os.path.join(d, kit.PROFILE_DOC)
    s = open(p, encoding="utf-8").read().replace("## 部署\n", "## 发布部署\n")
    open(p, "w", encoding="utf-8").write(s)
    errors, _ = kit.check(d, quiet=True)
    ok(any("缺节「部署」" in e for e in errors), "工程配置改了节名被报出")
    shutil.rmtree(d)


def t_check_soft_section_missing_only_warns():
    d = new_repo()
    run("install", d)
    p = os.path.join(d, kit.PROFILE_DOC)
    s = open(p, encoding="utf-8").read()
    i = s.index("## 并行线\n")
    j = s.index("\n## ", i + 1)
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
            text = open(os.path.join(kit.TEMPLATE, rel), encoding="utf-8").read()
            for name in re.findall(r"工程配置「([^」]+)」", text):
                if name not in have:
                    missing.add(f"{rel}: {name}")
    ok(not missing, f"内核引用的工程配置节都在 profile 里（缺：{sorted(missing)}）")


DISPATCH_RULE = "docs/rules/派活与交付.md"


def t_dispatch_rule_in_kernel():
    files, _ = kit.kernel_files()
    ok(DISPATCH_RULE in files, "派活与交付.md 在内核清单里")
    p = os.path.join(kit.TEMPLATE, DISPATCH_RULE)
    text = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    for sec in ["一、派活单", "二、回报", "三、spec+plan 必须写明", "四、证据", "五、旧失败"]:
        ok(f"## {sec}" in text, f"派活与交付.md 有「{sec}」一节")


def t_hooks_wired():
    import json
    s = json.load(open(os.path.join(kit.TEMPLATE, ".claude/settings.json"), encoding="utf-8"))
    cp = os.path.join(kit.TEMPLATE, ".codex/hooks.json")
    c = json.load(open(cp, encoding="utf-8")) if os.path.exists(cp) else {"hooks": {}}
    for name, cfg in (("claude", s), ("codex", c)):
        hooks = cfg.get("hooks", {})
        for ev in ("SessionStart", "PostToolUse", "SubagentStart", "SubagentStop"):
            hs = [h for g in hooks.get(ev, []) for h in g.get("hooks", [])]
            ok(any("skills/team-check/hook.py" in h.get("command", "") and ev in h.get("command", "") for h in hs),
               f"{name} 挂了 {ev}")
            ok(bool(hs) and all(h.get("timeout") == 10 for h in hs), f"{name} {ev} 超时 10 秒")
    pt = [g.get("matcher", "") for g in s.get("hooks", {}).get("PostToolUse", [])]
    ok(pt == ["Write|Edit|NotebookEdit"], f"claude PostToolUse matcher 为 Write|Edit|NotebookEdit（{pt}）")
    cpt = [g.get("matcher", "") for g in c.get("hooks", {}).get("PostToolUse", [])]
    ok(cpt == ["apply_patch"], f"codex PostToolUse matcher 只挂 apply_patch（{cpt}）")
    ok(".codex/hooks.json" in kit.kernel_files()[0], ".codex/hooks.json 在内核清单里")


def t_dispatch_rule_referenced():
    need = ["docs/rules/团队协作契约.md", "docs/rules/双端协作与交接.md",
            "docs/rules/roles/pm.md", "docs/rules/roles/ui.md",
            "docs/rules/roles/se.md", "docs/rules/roles/qa.md"]
    for rel in need:
        text = open(os.path.join(kit.TEMPLATE, rel), encoding="utf-8").read()
        ok("派活与交付.md" in text, f"{rel} 引用了派活与交付.md")


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
    scope = text.split("## 一、输入与范围", 1)[-1].split("\n## ", 1)[0] if "## 一、输入与范围" in text else ""
    for s in ["git merge-base", "git ls-files --others --exclude-standard",
              "git show <sha>:<path>", "rev-parse --verify"]:
        ok(s in scope, f"「输入与范围」写了 {s}")
    for s in ["静态分析，未运行测试", "证据确定性", "team-check.py migrations --refs",
              "§4.1", "docs/tests/<版本>/影响分析-<工作项>.md", "commit:path"]:
        ok(s in text, f"diff-impact 写了「{s}」")
    lane = text.split("**线的模式**", 1)[-1].split("\n\n", 1)[0] if "**线的模式**" in text else ""
    for s in ["不能直接对比", "实际用的基准 sha", "merge-tree --write-tree", "交集"]:
        ok(s in lane, f"「线的模式」写了「{s}」")
    seven = text.split("## 七、不是什么", 1)[-1] if "## 七、不是什么" in text else ""
    for s in ["不是评审结论", "不是测试证据", "派活与交付.md"]:
        ok(s in seven, f"「七、不是什么」写了「{s}」")


def t_hook_wording_matches_subagent_stop():
    """子代理结束提醒会让子代理再走一轮（decision: block），说明文字不能还写「只提醒、绝不拦截」。"""
    agents = open(os.path.join(kit.TEMPLATE, "AGENTS.md"), encoding="utf-8").read()
    line = next((l for l in agents.splitlines() if "运行时钩子" in l), "")
    ok("再走一轮" in line and "只提醒、不拦截" not in line, "AGENTS.md 钩子一条写明子代理会再走一轮")
    hook = open(os.path.join(kit.TEMPLATE, "skills/team-check/hook.py"), encoding="utf-8").read()
    doc = hook.split('"""', 2)[1] if hook.count('"""') >= 2 else ""
    ok("绝不拦截" not in doc and "decision" in doc, "hook.py 头注写明子代理结束的 decision 输出")


def _section(text, start, stop="\n## "):
    return text.split(start, 1)[-1].split(stop, 1)[0] if start in text else ""


def _lines_with(text, token):
    return [l for l in text.splitlines() if token in l]


def t_diff_impact_referenced():
    rd = lambda rel: open(os.path.join(kit.TEMPLATE, rel), encoding="utf-8").read()
    c = _section(rd("docs/rules/团队协作契约.md"), "### 2.1", "\n### ")
    ok("skills/diff-impact" in c, "契约 §2.1 引用 diff-impact")
    cl = _lines_with(c, "skills/diff-impact")
    ok(bool(cl) and all("已有改动可分析的" in l and "不论" not in l and "无论" not in l for l in cl),
       "契约那句限定在已有改动可分析时")
    lanes = rd("docs/rules/并行线.md")
    five = _section(lanes, "## 五、合入集成分支")
    ok("skills/diff-impact" in five, "并行线「五」引用 diff-impact")
    six = _section(lanes, "## 六、测试服与验收")
    ok("skills/diff-impact" in six and "影响分析" in six, "并行线「六」引用 diff-impact 并说存报告")
    for name, sec in (("契约 §2.1", c), ("并行线「五」", five), ("并行线「六」", six)):
        ls = _lines_with(sec, "skills/diff-impact")
        ok(bool(ls) and all("可以" in l and "必须" not in l and "须用" not in l for l in ls),
           f"{name} 引用 diff-impact 的句子写「可以」、不强制")
    md = rd("skills/manage-docs/SKILL.md")
    ok("影响分析" in md and "skills/diff-impact" in md, "manage-docs 写了影响分析的落位")


def t_sync_refuses_local_edit_and_force_overrides():
    d = new_repo()
    run("install", d)
    fill_profile(d)
    commit_all(d)
    with open(os.path.join(d, "CLAUDE.md"), "a", encoding="utf-8") as f:
        f.write("\n私改\n")
    commit_all(d)
    rc, out = run("sync", d)
    ok(rc == 1 and "CLAUDE.md" in out, "工程里改过内核文件时 sync 拒绝并点名")
    rc, out = run("sync", d, "--force")
    ok(rc == 0, "--force 覆盖成功")
    errors, _ = kit.check(d, quiet=True)
    ok(errors == [], "覆盖后与内核一致")
    shutil.rmtree(d)


def t_refuses_dirty_kernel_paths():
    d = new_repo()
    run("install", d)
    commit_all(d)
    with open(os.path.join(d, "AGENTS.md"), "a", encoding="utf-8") as f:
        f.write("\n未提交\n")
    rc, out = run("sync", d, "--force")
    ok(rc == 1 and "未提交改动" in out, "内核文件有未提交改动时拒绝（即使 --force）")
    rc, _ = run("sync", d, "--force", "--allow-dirty")
    ok(rc == 0, "--allow-dirty 明确放行")
    shutil.rmtree(d)


def t_profile_not_overwritten():
    d = new_repo()
    run("install", d)
    p = os.path.join(d, kit.PROFILE_DOC)
    open(p, "a", encoding="utf-8").write("\n本工程自填内容\n")
    commit_all(d)
    run("sync", d)
    ok("本工程自填内容" in open(p, encoding="utf-8").read(), "sync 不覆盖工程配置")
    open(os.path.join(d, "AGENTS.md"), "a", encoding="utf-8").write("\n私改\n")
    commit_all(d)
    rc, out = run("sync", d, "--force")
    ok(rc == 0 and 'commit -m "<提交信息>" -- .team-kit.json AGENTS.md' in out, "sync 打印带路径的提交命令（只含本次同步动到的路径）")
    shutil.rmtree(d)


def t_diff_shows_change():
    d = new_repo()
    run("install", d)
    with open(os.path.join(d, "AGENTS.md"), "a", encoding="utf-8") as f:
        f.write("改进一行\n")
    rc, out = run("diff", d, "AGENTS.md")
    ok(rc == 1 and "+改进一行" in out, "diff 打印工程侧的改动")
    shutil.rmtree(d)



class temp_kit:
    """adopt 会写 template/：测试一律在 kit 的临时副本上跑，不碰真实 kit。"""
    def __enter__(self):
        self.saved = (kit.KIT, kit.TEMPLATE, kit.PROFILE)
        self.dir = tempfile.mkdtemp(prefix="kit-copy-")
        for name in ("template", "profile"):
            shutil.copytree(os.path.join(self.saved[0], name), os.path.join(self.dir, name), symlinks=True)
        shutil.copy2(os.path.join(self.saved[0], "MANIFEST"), self.dir)
        subprocess.run(["git", "init", "-q", self.dir], check=True)
        subprocess.run(["git", "-C", self.dir, "config", "user.email", "t@example.invalid"], check=True)
        subprocess.run(["git", "-C", self.dir, "config", "user.name", "t"], check=True)
        commit_all(self.dir)
        kit.KIT, kit.TEMPLATE, kit.PROFILE = self.dir, os.path.join(self.dir, "template"), os.path.join(self.dir, "profile")
        return self.dir

    def __exit__(self, *exc):
        kit.KIT, kit.TEMPLATE, kit.PROFILE = self.saved
        shutil.rmtree(self.dir)


def t_adopt_pulls_project_edit_back():
    with temp_kit() as k:
        d = new_repo()
        run("install", d)
        commit_all(d)
        with open(os.path.join(d, "AGENTS.md"), "a", encoding="utf-8") as f:
            f.write("\n工程里的改进\n")
        open(os.path.join(d, "skills/team-ledger/NOTE.md"), "w").write("新增")
        rc, out = run("adopt", d)
        ok(rc == 0, "adopt 成功")
        ok("工程里的改进" in open(os.path.join(k, "template/AGENTS.md"), encoding="utf-8").read(), "改动收回 kit 的 template/")
        ok(os.path.exists(os.path.join(k, "template/skills/team-ledger/NOTE.md")), "内核目录里新增的文件一并收回")
        commit_all(d)
        rc, _ = run("sync", d)
        ok(rc == 0, "收回后对原工程 sync 不再被拒")
        errors, _ = kit.check(d, quiet=True)
        ok(errors == [], "收回并同步后与内核一致")
        shutil.rmtree(d)


def t_adopt_refuses_when_kit_changed_too():
    with temp_kit() as k:
        d = new_repo()
        run("install", d)
        commit_all(d)
        with open(os.path.join(k, "template/CLAUDE.md"), "a", encoding="utf-8") as f:
            f.write("\nkit 的新改动\n")
        commit_all(k)
        with open(os.path.join(d, "CLAUDE.md"), "a", encoding="utf-8") as f:
            f.write("\n工程的改动\n")
        rc, out = run("adopt", d)
        ok(rc == 1 and "CLAUDE.md" in out, "kit 同时改过同一文件时拒绝并点名")
        ok("kit 的新改动" in open(os.path.join(k, "template/CLAUDE.md"), encoding="utf-8").read(), "拒绝时不冲掉 kit 的新改动")
        rc, _ = run("adopt", d, "--force")
        ok(rc == 0 and "工程的改动" in open(os.path.join(k, "template/CLAUDE.md"), encoding="utf-8").read(), "--force 明确覆盖")
        shutil.rmtree(d)


def t_adopt_scope_and_guards():
    with temp_kit() as k:
        d = new_repo()
        run("install", d)
        commit_all(d)
        for f in ("AGENTS.md", "CLAUDE.md"):
            with open(os.path.join(d, f), "a", encoding="utf-8") as h:
                h.write("\n改\n")
        rc, out = run("adopt", d, "AGENTS.md")
        ok(rc == 0 and "AGENTS.md" in out and "CLAUDE.md" not in out, "给了路径只收回这些路径")
        rc, out = run("adopt", d, "src/app.py")
        ok(rc == 2 and "不是内核文件" in out, "非内核路径报用法错误")
        with open(os.path.join(k, "template/CLAUDE.md"), "a", encoding="utf-8") as h:
            h.write("\nkit 里没提交的改动\n")
        rc, out = run("adopt", d, "CLAUDE.md")
        ok(rc == 1 and "未提交改动" in out, "要收回的文件在 kit 的 template/ 里有未提交改动时拒绝")
        commit_all(k)
        os.remove(os.path.join(d, "docs/rules/roles/qa.md"))
        rc, out = run("adopt", d, "docs/rules/roles/qa.md")
        ok(os.path.exists(os.path.join(k, "template/docs/rules/roles/qa.md")) and "被删了" in out, "工程里删掉的内核文件不在 kit 里删，只提示")
        shutil.rmtree(d)

def t_check_all_profile_files_required():
    d = new_repo()
    run("install", d)
    profile_files = kit._walk(kit.PROFILE, ".")
    ok(all(os.path.exists(os.path.join(d, f)) for f in profile_files), "install 生成全部工程专属文件模板")
    os.remove(os.path.join(d, kit.UI_INSTANCE_DOC))
    errors, _ = kit.check(d, quiet=True)
    ok(any(kit.UI_INSTANCE_DOC in e and "不存在" in e for e in errors), "缺 UI 设计规范本工程实例时 check 报错")
    shutil.rmtree(d)


def t_sync_refuses_overwriting_unmanaged_file():
    d = new_repo()
    run("install", d)
    commit_all(d)
    p = os.path.join(d, "AGENTS.md")
    open(p, "a", encoding="utf-8").write("\n工程原有的同名文件内容\n")
    stamp_path = os.path.join(d, kit.STAMP)
    import json
    data = json.load(open(stamp_path, encoding="utf-8"))
    del data["files"]["AGENTS.md"]          # 模拟：该文件是内核新增的，kit 从没接管过
    json.dump(data, open(stamp_path, "w", encoding="utf-8"))
    commit_all(d)
    rc, out = run("sync", d)
    ok(rc == 1 and "AGENTS.md" in out and "未接管" in out, "工程里已有同名文件且 kit 未接管过时 sync 拒绝并点名")
    ok("工程原有的同名文件内容" in open(p, encoding="utf-8").read(), "拒绝时不覆盖工程原有文件")
    rc, _ = run("sync", d, "--force")
    ok(rc == 0 and kit.check(d, quiet=True)[0] == [], "--force 明确覆盖后与内核一致")
    shutil.rmtree(d)


def t_install_refuses_existing_kernel_named_file():
    d = new_repo()
    open(os.path.join(d, "CLAUDE.md"), "w", encoding="utf-8").write("工程自己的 CLAUDE.md\n")
    commit_all(d)
    rc, out = run("install", d)
    ok(rc == 1 and "CLAUDE.md" in out, "install 遇到工程已有的同名文件时拒绝")
    rc, _ = run("install", d, "--force")
    ok(rc == 0, "install --force 明确覆盖")
    shutil.rmtree(d)


def t_version_recorded_and_shown():
    with temp_kit() as k:
        subprocess.run(["git", "-C", k, "tag", "-a", "v9.8.7", "-m", "t"], check=True)
        d = new_repo()
        rc, out = run("install", d)
        import json
        stamp = json.load(open(os.path.join(d, kit.STAMP), encoding="utf-8"))
        ok(stamp.get("kit_version") == "v9.8.7", f"stamp 记录 kit 版本号（{stamp.get('kit_version')}）")
        ok("v9.8.7" in out, "install 输出版本号")
        rc, out = run("check", d)
        ok("v9.8.7" in out, "check 输出版本号")
        open(os.path.join(k, "template/AGENTS.md"), "a", encoding="utf-8").write("\n新\n")
        commit_all(k)
        ok(kit.kit_version().startswith("v9.8.7-1-g"), f"标签之后的提交显示为「标签-距离-提交」（{kit.kit_version()}）")
        shutil.rmtree(d)


def t_check_warns_unfilled_ui_instance():
    d = new_repo()
    run("install", d)
    _, warns = kit.check(d, quiet=True)
    ok(any(kit.UI_INSTANCE_DOC in w and "占位" in w for w in warns), "UI 设计规范本工程实例未填时给出提醒")
    p = os.path.join(d, kit.UI_INSTANCE_DOC)
    s = "\n".join(l for l in open(p, encoding="utf-8").read().splitlines() if not l.strip().startswith("<"))
    open(p, "w", encoding="utf-8").write(s + "\n")
    _, warns = kit.check(d, quiet=True)
    ok(not any(kit.UI_INSTANCE_DOC in w for w in warns), "占位全部替换后不再提醒")
    shutil.rmtree(d)


def t_demo_breakpoints_match_spec():
    import re
    spec = open(os.path.join(kit.TEMPLATE, "docs/rules/UI设计规范.md"), encoding="utf-8").read()
    sec = spec[spec.index("### 4.1"):spec.index("## 5.")]
    allowed = {int(x) for x in re.findall(r"@media \(width\s*[<>]=?\s*(\d+)px\)", sec)}
    ok(allowed == {768, 1180, 1440, 2560}, f"规范 §4.1 的断点阶为 768/1180/1440/2560（{sorted(allowed)}）")
    widths = lambda text: {int(x) for q in re.findall(r"@media\s*\(([^)]*)\)", text) for x in re.findall(r"(\d+)px", q)}
    demo = open(os.path.join(kit.TEMPLATE, "docs/rules/ui-demo.html"), encoding="utf-8").read()
    ok(widths(demo) <= allowed, f"演示页的 @media 断点都在 §4.1 断点阶内（多出 {sorted(widths(demo) - allowed)}）")
    ok(widths(spec) <= allowed, f"规范正文示例里的 @media 断点都在 §4.1 断点阶内（多出 {sorted(widths(spec) - allowed)}）")


UI_SPEC = "docs/rules/UI设计规范.md"


def _ui_index(text):
    return _section(text, "\n## 按需阅读\n")


def _spec_numbers(text):
    import re
    return set(re.findall(r"^#{2,4} (\d+(?:\.\d+)*)\.?\s", text, re.M))


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
    ok({str(i) for i in range(25)} <= nums, f"正文节号解析到 §0–§24（共 {len(nums)} 个）")
    refs = re.findall(r"§(\d+(?:\.\d+)*)", idx)
    ok(bool(refs) and all(r in nums for r in refs), f"索引引用的节号都存在（多出 {sorted(set(refs) - nums)}）")
    rows = "\n".join(l for l in idx.splitlines() if l.startswith("|"))
    whole = set(re.findall(r"§(\d+)(?![\d.])", rows))
    want = {str(i) for i in range(25)}
    ok(whole == want, f"§0–§24 在表格里都整节出现（缺 {sorted(want - whole, key=int)}）")
    always = _section(idx, "**每次都读**", "**按任务再读**")
    ok(set(re.findall(r"§(\d+(?:\.\d+)*)", always)) == {"0", "1", "2.4", "4", "20", "21", "22"},
       "「每次都读」恰为 §0、§1、§2.4、§4、§20、§21、§22")


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
    ok(not any("何时读" in w for w in warns), f"新装的工程配置有「何时读」：不警告（{warns}）")
    p = os.path.join(d, kit.PROFILE_DOC)
    s = open(p, encoding="utf-8").read()
    old = s.replace("| 规范 | 位置 | 何时读 |\n|---|---|---|", "| 规范 | 位置 |\n|---|---|")
    ok(old != s, "测试把表头改回两列")
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


def t_reading_rules_use_index():
    rd = lambda rel: open(os.path.join(kit.TEMPLATE, rel), encoding="utf-8").read()
    item = lambda text, n: next((l for l in text.splitlines() if l.startswith(f"{n}. ")), "")
    se, pm, qa = rd("docs/rules/roles/se.md"), rd("docs/rules/roles/pm.md"), rd("docs/rules/roles/qa.md")
    for name, t in (("se", se), ("pm", pm), ("qa", qa)):
        ok("何时读" in item(t, 2), f"{name}.md 第 2 条按「何时读」读项目规范")
    s4 = item(se, 4)
    ok(all(x in s4 for x in ["按需阅读", "新增页面", "通读", "本工程实例", "整份"]),
       "se.md 第 4 条：按需阅读、新增页面通读、实例整份读")
    p4 = item(pm, 4)
    ok(all(x in p4 for x in ["按需阅读", "审原型", "通读"]) and "界面" in p4,
       "pm.md 第 4 条：审原型和审界面通读，写需求按需阅读")
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

def t_adopt_three_way_merges_disjoint_edits():
    with temp_kit() as k:
        d = new_repo()
        run("install", d)
        commit_all(d)
        t = os.path.join(k, "template/CLAUDE.md")
        orig = open(t, encoding="utf-8").read()
        open(t, "w", encoding="utf-8").write("kit 在开头加的一行\n" + orig)
        commit_all(k)
        with open(os.path.join(d, "CLAUDE.md"), "a", encoding="utf-8") as f:
            f.write("\n工程在结尾加的一行\n")
        rc, out = run("adopt", d)
        merged = open(t, encoding="utf-8").read()
        ok(rc == 0 and "合并" in out, f"kit 与工程改了同一文件的不同处：三方合并收回（rc={rc}）")
        ok("kit 在开头加的一行" in merged and "工程在结尾加的一行" in merged, "合并结果同时保留两边的改动")
        shutil.rmtree(d)


def t_check_quiet_when_only_kit_docs_changed():
    with temp_kit() as k:
        d = new_repo()
        run("install", d)
        commit_all(d)
        os.makedirs(os.path.join(k, "docs"), exist_ok=True)
        open(os.path.join(k, "docs/说明.md"), "w", encoding="utf-8").write("只改 kit 自己的文档\n")
        commit_all(k)
        _, warns = kit.check(d, quiet=True)
        ok(not any(kit.STAMP in w for w in warns), f"kit 只改了内核以外的文件：不提醒版本落后（{warns}）")
        open(os.path.join(k, "template/AGENTS.md"), "a", encoding="utf-8").write("\n内核改动\n")
        commit_all(k)
        _, warns = kit.check(d, quiet=True)
        ok(any(kit.STAMP in w and "内核有更新" in w for w in warns), "内核有改动：提醒工程该 sync 了")
        shutil.rmtree(d)


if __name__ == "__main__":
    for name, fn in sorted((k, v) for k, v in globals().items() if k.startswith("t_")):
        print(name)
        fn()
    print(f"{'✓ 全部通过' if not failed else '✗ 有失败'}  通过 {passed} · 失败 {failed}")
    sys.exit(1 if failed else 0)

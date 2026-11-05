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
    shutil.rmtree(d)


def t_diff_shows_change():
    d = new_repo()
    run("install", d)
    with open(os.path.join(d, "AGENTS.md"), "a", encoding="utf-8") as f:
        f.write("改进一行\n")
    rc, out = run("diff", d, "AGENTS.md")
    ok(rc == 1 and "+改进一行" in out, "diff 打印工程侧的改动")
    shutil.rmtree(d)


if __name__ == "__main__":
    for name, fn in sorted((k, v) for k, v in globals().items() if k.startswith("t_")):
        print(name)
        fn()
    print(f"{'✓ 全部通过' if not failed else '✗ 有失败'}  通过 {passed} · 失败 {failed}")
    sys.exit(1 if failed else 0)

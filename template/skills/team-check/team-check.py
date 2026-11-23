#!/usr/bin/env python3
"""SA 手动运行的检查命令（只读）。用法见同目录 SKILL.md。

退出码：0 通过 / 1 有问题 / 2 判不了（判不了 ≠ 通过）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checks  # noqa: E402


def _repo(args):
    root = checks.repo_root(args.repo or os.getcwd())
    if not root:
        print("[team-check] 判不了：当前目录不在 git 仓库里")
        sys.exit(2)
    return root


def cmd_scope(args):
    repo = _repo(args)
    for c in [args.base, *args.commits]:
        if not checks.commit_exists(repo, c):
            print(f"[team-check] 判不了：提交不存在 {c}")
            sys.exit(2)
    paths = checks.changed_paths(repo, args.commits)
    bad = checks.out_of_scope(paths, args.allow, args.deny)
    if bad:
        print(f"[team-check] {len(bad)} 个路径越界（共改动 {len(paths)} 个）：")
        for p, why in bad:
            print(f"  {p}  {why}")
        sys.exit(1)
    print(f"[team-check] 无越界（共改动 {len(paths)} 个路径）")


def cmd_migrations(args):
    repo = _repo(args)
    rel = args.dir or checks.migration_dir(repo)
    if not rel:
        print(f"[team-check] 判不了：没给 --dir，{checks.CONFIG_DOC} 里也没有「数据库迁移」一行")
        sys.exit(2)
    if args.refs:
        try:
            dupes = checks.flyway_dupes_across(repo, rel, args.refs)
        except ValueError as e:
            print(f"[team-check] 判不了：{e}")
            sys.exit(2)
        if dupes:
            print(f"[team-check] {' + '.join(args.refs)} 合在一起，{rel} 有重复的迁移版本号：")
            for v, names in sorted(dupes.items()):
                print(f"  V{v}: {', '.join(names)}")
            sys.exit(1)
        print(f"[team-check] {' + '.join(args.refs)} 合在一起，{rel} 迁移版本号无重复")
        return
    path = os.path.join(repo, rel)
    if not os.path.isdir(path):
        print(f"[team-check] 判不了：迁移目录不存在 {rel}")
        sys.exit(2)
    dupes = checks.flyway_dupes(path)
    if dupes:
        print(f"[team-check] {rel} 有重复的迁移版本号：")
        for v, names in sorted(dupes.items()):
            print(f"  V{v}: {', '.join(names)}")
        sys.exit(1)
    print(f"[team-check] {rel} 迁移版本号无重复")


def cmd_plan(args):
    repo = _repo(args)
    p = args.file if os.path.isabs(args.file) else os.path.join(os.getcwd(), args.file)
    if not os.path.exists(p):
        p = os.path.join(repo, args.file)
    if not os.path.exists(p):
        print(f"[team-check] 判不了：文件不存在 {args.file}")
        sys.exit(2)
    with open(p, encoding="utf-8") as f:
        missing = checks.plan_missing(f.read())
    if missing:
        print(f"[team-check] {args.file} 缺：{'、'.join(missing)}（docs/rules/并行线.md「二」）")
        sys.exit(1)
    print(f"[team-check] {args.file} 并行编排齐全")


def cmd_lanes(args):
    repo = _repo(args)
    led = checks.ledger_dir(repo)
    try:
        extra, missing = checks.lanes(repo, checks.read_events(led))
    except ValueError as e:
        print(f"[team-check] 判不了：{e}")
        sys.exit(2)
    if extra:
        print("[team-check] 多出（有分支或工作树，未收口工作项里没登记）：")
        for x in extra:
            print(f"  {x}")
    if missing:
        print("[team-check] 缺失（未收口工作项登记了，分支和工作树都不在）：")
        for x in missing:
            print(f"  {x}")
    if extra or missing:
        sys.exit(1)
    print("[team-check] 工作树与账本登记的线一致")


def main():
    ap = argparse.ArgumentParser(prog="team-check.py")
    ap.add_argument("--repo", default=None, help="仓库路径（默认当前目录所在仓库）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scope", help="核对提交改动是否越出可写范围")
    s.add_argument("--base", required=True)
    s.add_argument("--commits", nargs="+", required=True)
    s.add_argument("--allow", nargs="+", required=True)
    s.add_argument("--deny", nargs="*", default=[])
    m = sub.add_parser("migrations", help="Flyway 迁移版本号是否重复")
    m.add_argument("--dir", default=None)
    m.add_argument("--refs", nargs="+", default=None,
                   help="合入前用：把这些分支（如 <集成分支> lane/<短名>）的迁移文件合在一起判重")
    p = sub.add_parser("plan", help="迭代规划是否有并行编排")
    p.add_argument("file")
    sub.add_parser("lanes", help="工作树与账本登记的线是否一致")
    args = ap.parse_args()
    {"scope": cmd_scope, "migrations": cmd_migrations, "plan": cmd_plan, "lanes": cmd_lanes}[args.cmd](args)


if __name__ == "__main__":
    main()

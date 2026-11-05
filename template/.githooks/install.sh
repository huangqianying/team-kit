#!/usr/bin/env bash
# 安装本仓库的 git 钩子：设置 core.hooksPath=.githooks 并自检。
#
# 用法：在仓库内执行 `bash .githooks/install.sh`。可重复执行，结果相同。
# 为什么需要：core.hooksPath 只存在本地 .git/config，不随克隆传递；
# 不装，新克隆的仓库里钩子不会被 git 调用，且没有任何提示。
set -euo pipefail

root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "❌ 不在 git 仓库内：请在仓库根执行 bash .githooks/install.sh" >&2
  exit 1
}
cd "$root"

if [ ! -f .githooks/pre-commit ]; then
  echo "❌ 找不到 .githooks/pre-commit：本脚本须随内核 .githooks/ 一起放在仓库根。" >&2
  exit 1
fi

previous="$(git config --local --get core.hooksPath || true)"
if [ -n "$previous" ] && [ "$previous" != ".githooks" ]; then
  echo "⚠️  core.hooksPath 原为「${previous}」，改为 .githooks（原目录里的钩子不再被调用）。" >&2
fi
git config --local core.hooksPath .githooks

# 克隆、解压或在 core.fileMode=false 的环境里，可执行位可能丢失；git 会跳过不可执行的钩子。
for hook in .githooks/*; do
  [ -f "$hook" ] || continue
  case "$hook" in *.sh|*.conf|*.md) continue ;; esac
  chmod +x "$hook"
done

# ─── 自检：任何一项不过都以非零退出 ─────────────────────────────────
fail=0
check() {  # check <描述> <命令…>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  ✓ ${desc}"
  else echo "  ✗ ${desc}" >&2; fail=1; fi
}
echo "钩子自检（${root}）："
check "core.hooksPath = .githooks" test "$(git config --get core.hooksPath)" = ".githooks"
check "pre-commit 可执行" test -x .githooks/pre-commit
check "pre-commit 语法可解析" bash -n .githooks/pre-commit
check "python3 可用（口令扫描依赖）" command -v python3
if [ -f .githooks/project.conf ]; then
  check "project.conf 可被 bash 解析" bash -n .githooks/project.conf
else
  echo "  ℹ️  未找到 .githooks/project.conf：钩子按内核默认判据运行（无工程追加路径、无白名单）。"
fi

if [ "$fail" -ne 0 ]; then
  echo "❌ 自检未通过，钩子可能不生效。" >&2
  exit 1
fi
echo "✅ 钩子已安装。"

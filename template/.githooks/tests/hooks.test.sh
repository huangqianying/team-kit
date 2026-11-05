#!/usr/bin/env bash
# git 钩子单测：在一次性临时仓库里真跑 git commit，不碰本仓库。
#
# 只测「钩子挂上后真能拦住」——静态读代码看不出钩子有没有被 git 实际调用。
set -uo pipefail

HOOKS_DIR="$(cd "${BASH_SOURCE[0]%/*}/.." && pwd)"
FAILS=0
n=0

ok() {  # ok <描述> <实际> <期望>
  n=$((n + 1))
  if [[ "$2" == "$3" ]]; then echo "  ✓ $1"
  else echo "  ✗ $1：期望 [$3] 实得 [$2]" >&2; FAILS=$((FAILS + 1)); fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

setup_repo() {   # 建一个干净仓库并挂上被测钩子
  rm -rf "${TMP}/repo"; mkdir -p "${TMP}/repo"
  git -C "${TMP}/repo" init -q
  git -C "${TMP}/repo" config user.email t@t; git -C "${TMP}/repo" config user.name t
  git -C "${TMP}/repo" config core.hooksPath "${HOOKS_DIR}"
  # 先落一个基线提交，避免首个提交的特殊性干扰
  echo x > "${TMP}/repo/readme.md"
  git -C "${TMP}/repo" add readme.md
  git -C "${TMP}/repo" commit -qm "base" 2>/dev/null
}

commit_rc() {  # commit_rc <消息> → 打印退出码
  git -C "${TMP}/repo" commit -m "$1" >/dev/null 2>&1; echo $?
}

fixture_commit_rc() {  # fixture_commit_rc <路径> <内容> <消息> → 打印退出码
  local path="$1" content="$2" message="$3"
  setup_repo
  mkdir -p "$(dirname "${TMP}/repo/${path}")"
  printf '%s\n' "$content" > "${TMP}/repo/${path}"
  git -C "${TMP}/repo" add "$path"
  commit_rc "$message"
}

echo "[A1 凭据文件本身不得提交]"
setup_repo
mkdir -p "${TMP}/repo/.deploy"
printf '[test]\nhost = 1.2.3.4\nuser = root\npassword = RealSecret123\n' > "${TMP}/repo/.deploy/credentials.ini"
git -C "${TMP}/repo" add -f .deploy/credentials.ini      # -f 模拟绕过 .gitignore
out=$(git -C "${TMP}/repo" commit -m "chore: 凭据" 2>&1); rc=$?
ok "credentials.ini 被 staged → 拒绝" "$([[ $rc -ne 0 ]] && echo yes || echo no)" "yes"
ok "拒绝时说明该改模板" "$(printf '%s' "$out" | grep -c 'example')" "1"

setup_repo
printf 'DEPLOY_PASSWORD=RealSecret123\n' > "${TMP}/repo/.env"
git -C "${TMP}/repo" add -f .env
ok ".env 被 staged → 拒绝" "$([[ "$(commit_rc 'chore: env')" -ne 0 ]] && echo yes || echo no)" "yes"

setup_repo
mkdir -p "${TMP}/repo/.deploy"
printf '[test]\nhost = 1.2.3.4\nuser = root\npassword =\n' > "${TMP}/repo/.deploy/credentials.ini.example"
git -C "${TMP}/repo" add .deploy/credentials.ini.example
ok "模板 .example 可正常提交" "$([[ "$(commit_rc 'chore: 模板')" -eq 0 ]] && echo yes || echo no)" "yes"

echo "[A2 提交内容里的明文口令]"
setup_repo
printf "DEPLOY_PASSWORD='RealSecret123'\n" > "${TMP}/repo/deploy.sh"
git -C "${TMP}/repo" add deploy.sh
ok "脚本含明文口令 → 拒绝" "$([[ "$(commit_rc 'chore: 部署脚本')" -ne 0 ]] && echo yes || echo no)" "yes"

setup_repo
mkdir -p "${TMP}/repo/tests"
printf 'DEPLOY_PASSWORD=fixture-pw\n' > "${TMP}/repo/tests/x.test.sh"
git -C "${TMP}/repo" add tests/x.test.sh
ok "测试文件里的夹具口令不误报" "$([[ "$(commit_rc 'test: 夹具')" -eq 0 ]] && echo yes || echo no)" "yes"

echo "[A2 真凭据形态必须全部拦截]"
ok "代码 password 字面量 → 拒绝" \
   "$([[ "$(fixture_commit_rc src/password.ts "const password = 'hunter2xyz';" 'test: password literal')" -ne 0 ]] && echo yes || echo no)" "yes"
ok "代码 api_key 字面量 → 拒绝" \
   "$([[ "$(fixture_commit_rc src/api.ts "const auth = { api_key: 'sk-live-9f3ab77c2211' };" 'test: api key literal')" -ne 0 ]] && echo yes || echo no)" "yes"
ok ".env 裸密码 → 拒绝" \
   "$([[ "$(fixture_commit_rc .env 'DEPLOY_PASSWORD=Str0ngP4ss!x' 'test: env password')" -ne 0 ]] && echo yes || echo no)" "yes"
ok "YAML 裸 secret_key → 拒绝" \
   "$([[ "$(fixture_commit_rc deploy/config.yml 'secret_key: aB3xY9zQ7wE1' 'test: yaml secret')" -ne 0 ]] && echo yes || echo no)" "yes"
ok "带前缀 password 的代码字面量 → 拒绝" \
   "$([[ "$(fixture_commit_rc src/postgres.ts "const config = { PGPASSWORD: 'Str0ngRealPass99' };" 'test: prefixed code password')" -ne 0 ]] && echo yes || echo no)" "yes"
ok "带前缀 password 的配置裸值 → 拒绝" \
   "$([[ "$(fixture_commit_rc deploy/postgres.conf 'PGPASSWORD=Str0ngP4ss9x' 'test: prefixed config password')" -ne 0 ]] && echo yes || echo no)" "yes"

echo "[A2 标识符、表达式与 spec 夹具不得误报]"
ok "phaseToken 复合标识符 → 放行" \
   "$([[ "$(fixture_commit_rc src/phase.ts 'const phaseToken: AdvisoryLockPhaseToken = value;' 'test: phase token identifier')" -eq 0 ]] && echo yes || echo no)" "yes"
ok "token 类型标识符 → 放行" \
   "$([[ "$(fixture_commit_rc src/token.ts 'token: AdvisoryLockPhaseToken,' 'test: token type')" -eq 0 ]] && echo yes || echo no)" "yes"
ok "password 解码表达式 → 放行" \
   "$([[ "$(fixture_commit_rc src/url.ts 'const password = decodeURIComponent(parsed.password);' 'test: password expression')" -eq 0 ]] && echo yes || echo no)" "yes"
ok "temporaryPassword 属性表达式 → 放行" \
   "$([[ "$(fixture_commit_rc src/form.ts 'password: temporaryPassword.value,' 'test: password property')" -eq 0 ]] && echo yes || echo no)" "yes"
ok "csrfToken 复合标识符 → 放行" \
   "$([[ "$(fixture_commit_rc src/csrf.ts 'csrfToken: material.csrfToken,' 'test: csrf token')" -eq 0 ]] && echo yes || echo no)" "yes"
ok ".spec.ts 中的夹具字面量 → 放行" \
   "$([[ "$(fixture_commit_rc src/auth.spec.ts "const password = 'fixture-password-123';" 'test: spec fixture')" -eq 0 ]] && echo yes || echo no)" "yes"

echo "[A2 不得误报：占位符与中文说明]"
ok "表单连续空字符串 → 放行" \
   "$([[ "$(fixture_commit_rc src/form.ts "const form = { currentPassword: '', newPassword: '', confirmation: '' };" 'test: empty form fields')" -eq 0 ]] && echo yes || echo no)" "yes"
ok "双引号连续空字符串 → 放行" \
   "$([[ "$(fixture_commit_rc src/form.ts 'const form = { password: "", token: "" };' 'test: empty double quotes')" -eq 0 ]] && echo yes || echo no)" "yes"
ok "仅空白字符串 → 放行" \
   "$([[ "$(fixture_commit_rc src/form.ts "const form = { password: '    ', token: '' };" 'test: blank form field')" -eq 0 ]] && echo yes || echo no)" "yes"
ok "模板字面量空字符串 → 放行" \
   "$([[ "$(fixture_commit_rc src/form.ts 'const form = { password: ``, token: `` };' 'test: empty template literal')" -eq 0 ]] && echo yes || echo no)" "yes"
ok "空字段后同一行的真实口令 → 拒绝" \
   "$([[ "$(fixture_commit_rc src/form.ts "const form = { currentPassword: '', newPassword: 'RealSecret123' };" 'test: secret after empty field')" -ne 0 ]] && echo yes || echo no)" "yes"
ok "占位字段后同一行的真实口令 → 拒绝" \
   "$([[ "$(fixture_commit_rc src/form.ts "const form = { password: 'dummy', token: 'RealSecret123' };" 'test: secret after dummy field')" -ne 0 ]] && echo yes || echo no)" "yes"
setup_repo
printf 'password = ${DEPLOY_PASSWORD}\npasswd: <你的口令>\napi_key = xxx\n' > "${TMP}/repo/conf.sh"
git -C "${TMP}/repo" add conf.sh
ok "占位符不误报" "$([[ "$(commit_rc 'chore: 占位符')" -eq 0 ]] && echo yes || echo no)" "yes"

setup_repo
printf '# 口令说明\npassword = 见配置文件\ntoken：由管理员发放\n' > "${TMP}/repo/说明.md"
git -C "${TMP}/repo" add 说明.md
ok "中文说明不误报" "$([[ "$(commit_rc 'docs: 说明')" -eq 0 ]] && echo yes || echo no)" "yes"

echo "[钩子确实被 git 调用（而非静态看着像挂上了）]"
setup_repo
printf "DEPLOY_PASSWORD='RealSecret123'\n" > "${TMP}/repo/x.sh"
git -C "${TMP}/repo" add x.sh
out=$(git -C "${TMP}/repo" commit -m "chore: x" 2>&1)
ok "拒绝信息来自本钩子" "$(printf '%s' "$out" | grep -c '疑似含明文凭据')" "1"
ok "--no-verify 能绕过（如实说，不假装拦得住）" \
   "$([[ "$(git -C "${TMP}/repo" commit --no-verify -m 'chore: x' >/dev/null 2>&1; echo $?)" -eq 0 ]] && echo yes || echo no)" "yes"

echo "[B. 被引文档编辑触发 spec 引用核]"
# 判据：改被引文档必须当场核，而不是等下游偶然撞上红门。
# 实发七次、七次全靠偶然发现——其中两次由团队二改契约引起，
# develop 的 spec 门红了数小时，SE 正在这道红门上做发布证据。

setup_repo
mkdir -p "${TMP}/repo/docs/superpowers/specs"
# 桩 checker：按参数决定红绿，本测试只验「有没有被触发」，不验 checker 自身
# 桩必须是合法 JS：hook 用 node 跑它，shell 桩会被当成语法错误、
# 混淆成「引用失配」（本测试首轮即因此误报）
cat > "${TMP}/repo/docs/superpowers/specs/check-spec-refs.mjs" <<'STUB'
import { existsSync } from 'node:fs';
if (existsSync(new URL('../../../RED', import.meta.url))) {
  console.error('SPEC_EXTERNAL_REF_HASH_MISMATCH: 桩造的失配');
  process.exit(1);
}
process.exit(0);
STUB
mkdir -p "${TMP}/repo/docs/rules"
printf 'contract v1\n' > "${TMP}/repo/docs/rules/团队协作契约.md"
git -C "${TMP}/repo" add -A -f >/dev/null 2>&1
git -C "${TMP}/repo" commit -q --no-verify -m "base" 2>/dev/null

# 绿：改被引文档且核通过 → 放行
printf 'contract v2\n' > "${TMP}/repo/docs/rules/团队协作契约.md"
git -C "${TMP}/repo" add -f docs/rules/团队协作契约.md
ok "改被引文档且引用核通过 → 放行" \
   "$([[ "$(commit_rc 'docs: 改契约')" -eq 0 ]] && echo yes || echo no)" "yes"

# 红：改被引文档且核失败 → 拦下
# 只跑一次 commit 并同时取退出码与输出——跑两次的话第二次已无 staged 内容，
# 会因「nothing to commit」失败而假装成「被拦住」（本测试首轮即踩此坑）。
touch "${TMP}/repo/RED"
printf 'contract v3\n' > "${TMP}/repo/docs/rules/团队协作契约.md"
git -C "${TMP}/repo" add -f docs/rules/团队协作契约.md
out=$(git -C "${TMP}/repo" commit -m "docs: 改契约" 2>&1); rc=$?
ok "改被引文档且引用失配 → 拦下" "$([[ "${rc}" -ne 0 ]] && echo yes || echo no)" "yes"
ok "拦下原因是引用核而非无内容可提交" \
   "$(printf '%s' "$out" | grep -c 'nothing to commit')" "0"
ok "拒绝信息指向重锚命令" "$(printf '%s' "$out" | grep -c 'spec:reanchor')" "1"

# 未触及被引文档 → 不跑，红也不该拦
# 先清 staged：上一步 commit 被拦，被引文档仍在暂存区，不清会继续触发该门
git -C "${TMP}/repo" reset -q
printf 'hello\n' > "${TMP}/repo/unrelated.txt"
git -C "${TMP}/repo" add unrelated.txt
ok "未触及被引文档 → 不触发该核" \
   "$([[ "$(commit_rc 'chore: 无关改动')" -eq 0 ]] && echo yes || echo no)" "yes"
rm -f "${TMP}/repo/RED"

echo
if [[ "${FAILS}" -gt 0 ]]; then echo "❌ ${FAILS}/${n} 项失败"; exit 1; fi
echo "✅ 全部通过（${n} 项）"

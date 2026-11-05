#!/usr/bin/env bash
# git 钩子单测：在一次性临时仓库里真跑 git commit / install.sh，不碰本仓库。
#
# 只测「钩子挂上后真能拦住」——静态读代码看不出钩子有没有被 git 实际调用。
# 工程专属的路径与白名单由测试内临时写入的 .githooks/project.conf 提供，
# 内核脚本本身不带任何工程专属值。
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
R="${TMP}/repo"

# 测试用工程配置：两个姊妹工程专属项的并集（凭据文件位置、业务取值白名单）。
TEST_CONF='HOOK_CRED_FILE_RE='\''(^|/)\.deploy/credentials\.ini$'\''
HOOK_SECRET_ALLOW_VALUE_RE='\''total_(input_|output_)?tokens'\''
HOOK_CRED_HINT='\''本地凭据只放不入库的凭据文件。'\'''

write_conf() { printf '%s\n' "$1" > "${R}/.githooks/project.conf"; }

setup_repo() {   # 建一个干净仓库，把被测钩子放进它自己的 .githooks/ 并挂上
  rm -rf "${R}"; mkdir -p "${R}/.githooks"
  git -C "${R}" init -q
  git -C "${R}" config user.email t@t; git -C "${R}" config user.name t
  cp "${HOOKS_DIR}/pre-commit" "${HOOKS_DIR}/install.sh" "${R}/.githooks/"
  git -C "${R}" config core.hooksPath .githooks
  write_conf "${TEST_CONF}"
  # 先落一个基线提交，避免首个提交的特殊性干扰
  echo x > "${R}/readme.md"
  git -C "${R}" add readme.md
  git -C "${R}" commit -qm "base" 2>/dev/null
}

verdict_of_last() {  # 按上一次 commit 的退出码与输出判：allow | reject | other:<rc>
  local rc="$1"
  if [[ "$rc" -eq 0 ]]; then echo allow
  elif grep -qE '疑似含明文凭据|凭据文件不得提交' "${TMP}/last.out"; then echo reject
  else echo "other:${rc}"; fi
}

commit_verdict() {  # commit_verdict <消息> → allow | reject | other:<rc>（reject 必须是本钩子的拦截信息）
  git -C "${R}" commit -m "$1" >"${TMP}/last.out" 2>&1; verdict_of_last $?
}

fixture_verdict() {  # fixture_verdict <路径> <内容> <消息>
  local path="$1" content="$2" message="$3"
  setup_repo
  mkdir -p "$(dirname "${R}/${path}")"
  printf '%s\n' "$content" > "${R}/${path}"
  git -C "${R}" add -f "$path"
  commit_verdict "$message"
}

rejects() { [[ "$(fixture_verdict "$@")" == reject ]] && echo yes || echo no; }
allows()  { [[ "$(fixture_verdict "$@")" == allow ]] && echo yes || echo no; }

echo "[A1 凭据文件本身不得提交]"
setup_repo
mkdir -p "${R}/.deploy"
printf '[test]\nhost = 1.2.3.4\nuser = root\npassword = RealSecret123\n' > "${R}/.deploy/credentials.ini"
git -C "${R}" add -f .deploy/credentials.ini      # -f 模拟绕过 .gitignore
out=$(git -C "${R}" commit -m "chore: 凭据" 2>&1); rc=$?
ok "credentials.ini 被 staged → 拒绝（路径来自 project.conf）" "$([[ $rc -ne 0 ]] && printf '%s' "$out" | grep -q '凭据文件不得提交' && echo yes || echo no)" "yes"
ok "拒绝时说明该改模板" "$(printf '%s' "$out" | grep -q '\.example' && echo yes || echo no)" "yes"

setup_repo
printf 'DEPLOY_PASSWORD=RealSecret123\n' > "${R}/.env"
git -C "${R}" add -f .env
ok ".env 被 staged → 拒绝" "$([[ "$(commit_verdict 'chore: env')" == reject ]] && echo yes || echo no)" "yes"

setup_repo
mkdir -p "${R}/.deploy"
printf '[test]\nhost = 1.2.3.4\nuser = root\npassword =\n' > "${R}/.deploy/credentials.ini.example"
git -C "${R}" add .deploy/credentials.ini.example
ok "模板 .example 可正常提交" "$([[ "$(commit_verdict 'chore: 模板')" == allow ]] && echo yes || echo no)" "yes"

echo "[A2 提交内容里的明文口令]"
setup_repo
printf "DEPLOY_PASSWORD='RealSecret123'\n" > "${R}/deploy.sh"
git -C "${R}" add deploy.sh
ok "脚本含带引号明文口令 → 拒绝" "$([[ "$(commit_verdict 'chore: 部署脚本')" == reject ]] && echo yes || echo no)" "yes"
ok "脚本含裸值 DEPLOY_PASSWORD=RealSecret123 → 拒绝（.sh 按配置类扫裸值）" \
   "$(rejects deploy.sh 'DEPLOY_PASSWORD=RealSecret123' 'chore: 部署脚本')" "yes"

setup_repo
mkdir -p "${R}/tests"
printf 'DEPLOY_PASSWORD=fixture-pw\n' > "${R}/tests/x.test.sh"
git -C "${R}" add tests/x.test.sh
ok "测试文件里的夹具口令不误报" "$([[ "$(commit_verdict 'test: 夹具')" == allow ]] && echo yes || echo no)" "yes"
ok "普通代码改动放行" "$(allows backend.py 'print(1)' 'chore: 后端改动')" "yes"

echo "[A2 真凭据形态必须全部拦截]"
ok "代码 password 字面量 → 拒绝" "$(rejects src/password.ts "const password = 'hunter2xyz';" 'test: password literal')" "yes"
ok "代码 api_key 字面量 → 拒绝" "$(rejects src/api.ts "const auth = { api_key: 'sk-live-9f3ab77c2211' };" 'test: api key literal')" "yes"
ok ".env 裸密码 → 拒绝" "$(rejects .env 'DEPLOY_PASSWORD=Str0ngP4ss!x' 'test: env password')" "yes"
ok "YAML 裸 secret_key → 拒绝" "$(rejects deploy/config.yml 'secret_key: aB3xY9zQ7wE1' 'test: yaml secret')" "yes"
ok "带前缀 password 的代码字面量 → 拒绝" "$(rejects src/postgres.ts "const config = { PGPASSWORD: 'Str0ngRealPass99' };" 'test: prefixed code password')" "yes"
ok "带前缀 password 的配置裸值 → 拒绝" "$(rejects deploy/postgres.conf 'PGPASSWORD=Str0ngP4ss9x' 'test: prefixed config password')" "yes"
ok "带类型标注的口令字面量（Python）→ 拒绝" "$(rejects app/settings.py 'password: str = "RealSecret123"' 'test: typed py')" "yes"
ok "带类型标注的口令字面量（TS）→ 拒绝" "$(rejects src/cfg.ts "const password: string = 'RealSecret123';" 'test: typed ts')" "yes"

echo "[A2 标识符、表达式与 spec 夹具不得误报]"
ok "phaseToken 复合标识符 → 放行" "$(allows src/phase.ts 'const phaseToken: AdvisoryLockPhaseToken = value;' 'test: phase token identifier')" "yes"
ok "token 类型标识符 → 放行" "$(allows src/token.ts 'token: AdvisoryLockPhaseToken,' 'test: token type')" "yes"
ok "password 解码表达式 → 放行" "$(allows src/url.ts 'const password = decodeURIComponent(parsed.password);' 'test: password expression')" "yes"
ok "temporaryPassword 属性表达式 → 放行" "$(allows src/form.ts 'password: temporaryPassword.value,' 'test: password property')" "yes"
ok "csrfToken 复合标识符 → 放行" "$(allows src/csrf.ts 'csrfToken: material.csrfToken,' 'test: csrf token')" "yes"
ok ".spec.ts 中的夹具字面量 → 放行" "$(allows src/auth.spec.ts "const password = 'fixture-password-123';" 'test: spec fixture')" "yes"

echo "[A2 不得误报：占位符与中文说明]"
ok "表单连续空字符串 → 放行" "$(allows src/form.ts "const form = { currentPassword: '', newPassword: '', confirmation: '' };" 'test: empty form fields')" "yes"
ok "双引号连续空字符串 → 放行" "$(allows src/form.ts 'const form = { password: "", token: "" };' 'test: empty double quotes')" "yes"
ok "仅空白字符串 → 放行" "$(allows src/form.ts "const form = { password: '    ', token: '' };" 'test: blank form field')" "yes"
ok "模板字面量空字符串 → 放行" "$(allows src/form.ts 'const form = { password: ``, token: `` };' 'test: empty template literal')" "yes"
ok "空字段后同一行的真实口令 → 拒绝" "$(rejects src/form.ts "const form = { currentPassword: '', newPassword: 'RealSecret123' };" 'test: secret after empty field')" "yes"
ok "占位字段后同一行的真实口令 → 拒绝" "$(rejects src/form.ts "const form = { password: 'dummy', token: 'RealSecret123' };" 'test: secret after dummy field')" "yes"
setup_repo
printf 'password = ${DEPLOY_PASSWORD}\npasswd: <你的口令>\napi_key = xxx\n' > "${R}/conf.sh"
git -C "${R}" add conf.sh
ok "占位符不误报" "$([[ "$(commit_verdict 'chore: 占位符')" == allow ]] && echo yes || echo no)" "yes"
ok "脚本里的命令展开与格式占位不误报" \
   "$(allows gen.sh "$(printf '%s\n' 'db_password=$(openssl rand -hex 32)' "printf 'DB_PASSWORD=%s\\n' \"\$db_password\" > qa.env" 'PGPASSWORD="$1" psql')" 'chore: 生成口令')" "yes"

ok "值中段含命令展开（运行时生成）不误报" "$(allows verify.sh 'DB_PASSWORD=verify-$(od -An -N8 -tx1 /dev/urandom)' 'chore: 随机口令')" "yes"
ok "Markdown 行内代码不是字符串字面量 → 放行" \
   "$(allows docs/评审.md '未携 token=`401 AUTH_REQUIRED`；admin password: `DEFAULT_ADMIN_PASSWORD`' 'docs: 评审')" "yes"
ok "Markdown 里带引号的真实口令 → 拒绝" "$(rejects docs/部署.md 'export DEPLOY_PASSWORD="RealSecret123"' 'docs: 部署')" "yes"

setup_repo
printf '# 口令说明\npassword = 见配置文件\ntoken：由管理员发放\n' > "${R}/说明.md"
git -C "${R}" add 说明.md
ok "中文说明不误报" "$([[ "$(commit_verdict 'docs: 说明')" == allow ]] && echo yes || echo no)" "yes"

echo "[持有者令牌代码不是明文凭据]"
holder_case() {
  ok "$1" "$(fixture_verdict backend.py "$2" 'test: holder field')" "$3"
}
holder_case "ORM无默认值声明放行" 'holder_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)' allow
holder_case "UUID生成表达式放行" 'holder_token=str(uuid4()),' allow
holder_case "字段引用转发放行" 'holder_token=row.holder_token,' allow
holder_case "硬编码持有者令牌仍拒绝" 'holder_token="FixtureNonceValue123"' reject
holder_case "带硬编码默认值的声明仍拒绝" 'holder_token: Mapped[str] = mapped_column(Text, default="FixtureNonceValue123")' reject
holder_case "引用样式字符串仍拒绝" 'holder_token="row.holder_token"' reject
holder_case "生成样式字符串仍拒绝" 'holder_token="str(uuid4())"' reject
holder_case "同一行另有口令仍拒绝" 'holder_token=str(uuid4()), password="FixtureCredentialValue123"' reject
holder_case "前缀口令字段仍拒绝" 'sub2api_password="FixtureCredentialValue123"' reject

echo "[Vue 动态绑定与事件不是明文凭据]"
vue_case() {
  local c; c="$(printf '<template>%s</template>' "$2")"
  ok "$1" "$(fixture_verdict src/views/A.vue "$c" 'test: Vue binding')" "$3"
}
vue_case "动态指标属性引用放行" '<Chart :token="state.tokens.main" />' allow
vue_case "动态指标索引及事件转发放行" '<Chart :token="state.tokens[kind]" @update:token="state.tokens[kind] = $event" />' allow
vue_case "动态模板索引引用放行" '<Chart :token="state.tokens[`follow-${id}`]" />' allow
vue_case "Token指标类型声明放行" '<script lang="ts">defineProps<{ token: TokenMetric; }>()</script>' allow
vue_case "Token指标默认枚举放行（白名单来自 project.conf）" "<script>const detail = { token: 'total_tokens', data: null }</script>" allow
vue_case "Token事件emit转发放行" "<Chart @update:token=\"emit('update:token', \$event)\" />" allow
vue_case "伪装类型名的静态凭据仍拒绝" '<Chart token="TokenMetric" />' reject
vue_case "Vue密码操作事件回调放行" "<Toolbar @password=\"appAction('password')\" />" allow
vue_case "密码操作事件内字面口令仍拒绝" "<Toolbar @password=\"'FixtureCredentialValue123'\" />" reject
vue_case "空密码后紧跟其他语句放行" "<script>form={old_password:'',new_password:''};loading=false</script>" allow
vue_case "空密码同一行另有真值仍拒绝" "<script>old_password='';new_password='FixtureCredentialValue123';loading=false</script>" reject
vue_case "密码含转义引号仍拒绝" '<script>password="ab\"FixtureCredentialValue123"</script>' reject
vue_case "静态Token属性值仍拒绝" '<Chart token="FixtureCredentialValue123" />' reject
vue_case "绑定字符串字面值仍拒绝" "<Chart :token=\"'FixtureCredentialValue123'\" />" reject
vue_case "合法动态绑定同一行口令仍拒绝" '<Chart :token="state.tokens.main" password="FixtureCredentialValue123" />' reject
vue_case "模型Token事件元组类型放行" '<script lang="ts">defineEmits<{token:[string,TokenMetric];open:[string,RankingItem]}>()</script>' allow
vue_case "模型Token双参数事件转发放行" '<Chart @token="(model,token)=>state.modelUsers.cards[model].token=token" />' allow
vue_case "模型Token事件仍扫描同行凭据" '<Chart @token="(model,token)=>state.modelUsers.cards[model].token=token" password="FixtureCredentialValue123" />' reject
vue_case "元组类型伪装静态字符串仍拒绝" '<script>token="[string,TokenMetric]"</script>' reject

echo "[project.conf：工程专属项只从这里来；缺失时不静默放行]"
setup_repo; rm -f "${R}/.githooks/project.conf"
printf "DEPLOY_PASSWORD='RealSecret123'\n" > "${R}/x.sh"; git -C "${R}" add x.sh
out=$(git -C "${R}" commit -m "chore: x" 2>&1); rc=$?
ok "project.conf 缺失 → 提交时打印提示" "$(printf '%s' "$out" | grep -c '未找到 .githooks/project.conf')" "1"
ok "project.conf 缺失 → 仍拦明文口令" "$([[ $rc -ne 0 ]] && printf '%s' "$out" | grep -q '疑似含明文凭据' && echo yes || echo no)" "yes"
setup_repo; write_conf ''
mkdir -p "${R}/src"; printf "%s\n" "const detail = { token: 'total_tokens' }" > "${R}/src/a.ts"; git -C "${R}" add src/a.ts
ok "未配业务白名单 → 同一取值被拦（白名单不在内核里）" "$([[ "$(commit_verdict 'test: no allow')" == reject ]] && echo yes || echo no)" "yes"
setup_repo; write_conf "HOOK_TEST_PATH_RE='^qa/fixtures/'"
mkdir -p "${R}/qa/fixtures"; printf "%s\n" "const password = 'fixture-password-123';" > "${R}/qa/fixtures/login.mjs"; git -C "${R}" add qa
ok "HOOK_TEST_PATH_RE 追加的测试路径 → 豁免" "$([[ "$(commit_verdict 'test: qa fixture')" == allow ]] && echo yes || echo no)" "yes"
setup_repo; write_conf "HOOK_CONFIG_PATH_RE='\\.inventory\$'"
printf 'ansible_password=RealSecret123\n' > "${R}/hosts.inventory"; git -C "${R}" add hosts.inventory
ok "HOOK_CONFIG_PATH_RE 追加的配置类路径 → 扫裸值" "$([[ "$(commit_verdict 'chore: inventory')" == reject ]] && echo yes || echo no)" "yes"
setup_repo; write_conf "HOOK_TEST_PATH_RE='(unclosed'"
echo y > "${R}/y.md"; git -C "${R}" add y.md
out=$(git -C "${R}" commit -m "chore: y" 2>&1); rc=$?
ok "project.conf 正则写错 → 拦下而非放行" "$([[ $rc -ne 0 ]] && echo yes || echo no)" "yes"
ok "拦下时指明是哪个变量" "$(printf '%s' "$out" | grep -c 'HOOK_TEST_PATH_RE 不是合法正则')" "1"

echo "[钩子确实被 git 调用（而非静态看着像挂上了）]"
setup_repo
printf "DEPLOY_PASSWORD='RealSecret123'\n" > "${R}/x.sh"
git -C "${R}" add x.sh
out=$(git -C "${R}" commit -m "chore: x" 2>&1)
ok "拒绝信息来自本钩子" "$(printf '%s' "$out" | grep -c '疑似含明文凭据')" "1"
ok "--no-verify 能绕过（如实说，不假装拦得住）" \
   "$([[ "$(git -C "${R}" commit --no-verify -m 'chore: x' >/dev/null 2>&1; echo $?)" -eq 0 ]] && echo yes || echo no)" "yes"

echo "[install.sh：新克隆的仓库装上钩子才生效]"
rm -rf "${R}"; mkdir -p "${R}/.githooks"
git -C "${R}" init -q; git -C "${R}" config user.email t@t; git -C "${R}" config user.name t
cp "${HOOKS_DIR}/pre-commit" "${HOOKS_DIR}/install.sh" "${R}/.githooks/"
write_conf "${TEST_CONF}"
chmod 644 "${R}/.githooks/pre-commit"            # 模拟克隆 / 解压后可执行位丢失
printf "DEPLOY_PASSWORD='RealSecret123'\n" > "${R}/x.sh"; git -C "${R}" add x.sh
ok "未安装时钩子不生效（这正是要治的问题）" "$([[ "$(commit_verdict 'chore: before install')" == allow ]] && echo yes || echo no)" "yes"
out1=$(cd "${R}" && bash .githooks/install.sh 2>&1); rc1=$?
ok "install.sh 在仓库根执行成功" "$rc1" "0"
ok "设置 core.hooksPath=.githooks" "$(git -C "${R}" config --get core.hooksPath)" ".githooks"
ok "恢复 pre-commit 可执行位" "$([[ -x "${R}/.githooks/pre-commit" ]] && echo yes || echo no)" "yes"
ok "输出自检结论" "$(printf '%s' "$out1" | grep -c '钩子已安装')" "1"
mkdir -p "${R}/sub"; out2=$(cd "${R}/sub" && bash ../.githooks/install.sh 2>&1); rc2=$?
ok "重复执行（含从子目录执行）仍成功且结果不变" "${rc2}:$(git -C "${R}" config --get-all core.hooksPath)" "0:.githooks"
printf "DEPLOY_PASSWORD='RealSecret123'\n" > "${R}/y.sh"; git -C "${R}" add y.sh
ok "安装后同样的明文口令被拦" "$([[ "$(commit_verdict 'chore: after install')" == reject ]] && echo yes || echo no)" "yes"
mkdir -p "${TMP}/not-a-repo"
ok "不在 git 仓库内执行 → 非零退出" \
   "$( (cd "${TMP}/not-a-repo" && GIT_CEILING_DIRECTORIES="${TMP}" bash "${HOOKS_DIR}/install.sh" >/dev/null 2>&1); [[ $? -ne 0 ]] && echo yes || echo no)" "yes"


echo "▸ 内核文件改动提醒（只提醒，不拦）"
kit_stamp() {  # kit_stamp <路径>…：按当前工作区内容写 .team-kit.json，模拟 kit 同步后的状态
  python3 - "$R" "$@" <<'PY'
import hashlib, json, os, sys
root, paths = sys.argv[1], sys.argv[2:]
files = {p: hashlib.sha256(open(os.path.join(root, p), "rb").read()).hexdigest() for p in paths}
json.dump({"kit_commit": "test", "files": files}, open(os.path.join(root, ".team-kit.json"), "w"))
PY
}
setup_repo; mkdir -p "${R}/docs/rules"; echo "契约 v1" > "${R}/docs/rules/契约.md"
kit_stamp docs/rules/契约.md; git -C "${R}" add -A; git -C "${R}" commit -qm "sync" 2>/dev/null
echo "本工程私改" >> "${R}/docs/rules/契约.md"; git -C "${R}" add docs/rules/契约.md
v=$(commit_verdict "docs: 私改内核")
ok "私改内核文件：照常放行" "$v" "allow"
ok "私改内核文件：打印提醒并点名文件" "$(grep -c 'docs/rules/契约.md' "${TMP}/last.out")" "1"
ok "提醒里给出收回命令" "$(grep -c 'bin/kit adopt' "${TMP}/last.out")" "1"
echo "契约 v2" > "${R}/docs/rules/契约.md"; kit_stamp docs/rules/契约.md; git -C "${R}" add -A
commit_verdict "chore: kit sync" >/dev/null
ok "kit 同步带来的改动（与 .team-kit.json 摘要一致）：不提醒" "$(grep -c '团队基建内核文件' "${TMP}/last.out")" "0"
git -C "${R}" rm -q docs/rules/契约.md
commit_verdict "docs: 删内核" >/dev/null
ok "删除内核文件：提醒" "$(grep -c '契约.md（删除）' "${TMP}/last.out")" "1"
echo "普通" > "${R}/note.txt"; git -C "${R}" add note.txt
commit_verdict "docs: 非内核" >/dev/null
ok "非内核文件改动：不提醒" "$(grep -c '团队基建内核文件' "${TMP}/last.out")" "0"
setup_repo; mkdir -p "${R}/docs"; echo x > "${R}/docs/a.md"; git -C "${R}" add docs/a.md
commit_verdict "docs: 无 kit 记录" >/dev/null
ok "没有 .team-kit.json：不提醒、不报错" "$(grep -c '团队基建内核文件' "${TMP}/last.out"):$(verdict_of_last 0)" "0:allow"

echo
if [[ "${FAILS}" -gt 0 ]]; then echo "❌ ${FAILS}/${n} 项失败"; exit 1; fi
echo "✅ 全部通过（${n} 项）"

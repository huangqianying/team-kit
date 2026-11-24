# UI 设计规范

> 本规范定义前端的完整视觉与交互标准，与具体业务项目无关，是新增或修改任何页面的**首要依据**。
> 所有实现以本规范为准；变更规范前须先更新本文档。
>
> **两层结构**：本文件是**通用规则**，在所有工程逐字相同（team-kit 内核，工程里不单独改；通用规则要改，报 team-kit 维护方）；**本产品的取值**（产品名、启用了哪些可选能力、各身份的件数、具体路由与数据口径等）写在工程里的 **`docs/rules/UI设计规范-本工程实例.md`**，按本文件的节号逐节对应。二者合称「UI 设计规范」；**本文件不写任何产品事实**，凡写「见本工程实例」处，以实例文件对应一节为准。演示页 `docs/rules/ui-demo.html`（同属内核，浏览器直接打开）按本文件的令牌与规则实现，示例数据仅作演示；**演示页与本文件不一致时以本文件为准**，并报 team-kit 维护方修演示页。
>
> 设计目标：**灵动 · 清晰**——堪比 Apple（iOS / macOS）的观感与手感。用**材质、光影、动效**建立层次，用**留白、排版、克制用色**建立秩序。

---

## 按需阅读

本节只说**最少要读哪些节**，不改任何规则。**拿不准就读全文。**

**通读全文的场合**（要与本规范逐条对，或者涉及面太广）：
- UI 角色出原型；
- PM 审原型、审 SE 实现的界面；
- 新增页面；
- 拿不准该读哪些节时。

**其余场合**（如 SE 改已有页面、快速链路改界面、SA 评审涉及界面的产物、PM 写涉及界面的需求）：先读下面「每次都读」的节，再读本次任务涉及的行，取并集；表里找不到本次任务的，读全文。

**本工程实例**（`docs/rules/UI设计规范-本工程实例.md`）每次整份读：它记的例外不一定挂在你要读的节号下。

写法：`§N` 指整节，含它的全部子节；`§N.M` 只指该子节。

**每次都读**

| 节 | 为什么每次都读 |
|---|---|
| §0 设计哲学 | 规则冲突时的裁决顺序 |
| §1 令牌体系总览 | 不得硬编码、暗色为一等公民 |
| §2.4 语义化令牌 | 组件只引用这一层 |
| §4 间距、栅格与断点 | 间距令牌几乎每个界面任务都用；断点全站统一、强制 |
| §20 数据展示格式化 | 两条红线管所有展示数据和文案的地方 |
| §21 无障碍与降级 | 聚焦、对比度、命中区，任何可交互元素都适用 |
| §22 新增页面检查清单 | 改完逐条自查用 |

**按任务再读**

| 本次任务涉及 | 再读 |
|---|---|
| 表格、列表页 | §11.2、§12、§13、§17、§18 |
| 筛选栏、查询条件 | §12、§15.1、§15.2 |
| 表单、输入 | §14、§15、§18.3 |
| 弹窗、抽屉 | §16、§15、§18.3 |
| 按钮、操作列 | §14、§13.3 |
| 卡片、汇总信息卡、仪表盘、指标卡、图表 | §11、§5、§2.5、§6.5 |
| 页面骨架、顶栏、侧栏、导航、页签 | §7、§8、§9、§10、§23.2 |
| 登录页 | §7 |
| 组织树、双栏、看板、大屏、投屏 | §10 |
| 颜色、主题、对比度、新的文字与底色组合 | §2 |
| 字体、字号、数字排版 | §3 |
| 圆角、阴影、材质、玻璃 | §5 |
| 动效、过渡 | §6 |
| 空状态、加载、加载失败 | §18 |
| 消息提示、通知中心 | §19、§23 |
| 移动端、窄屏 | §23、§16 |
| 一次性凭据 | §15、§16 |
| 富文本编辑器 | §24 |

---

## 0. 设计哲学

四条总纲，贯穿全文，冲突时按此优先级裁决：

1. **清晰优先（Clarity）**：信息层次一眼可辨；内容是主角，装饰退居其次。层次靠**字号 + 字重 + 留白**建立，而非靠颜色和边框堆砌。
2. **材质与深度（Depth）**：用**半透明材质 + 柔和光影**表达层级，而不是到处画 1px 边框。顶栏与侧边栏是"浮在内容之上的磨砂玻璃"，卡片是"从背景抬起的一层"。
3. **灵动（Fluidity）**：一切状态变化都有动效衔接。动效**快、有弹性、有目的**（hover / press / 进场 / 转场），绝不为炫技而动，并尊重 `prefers-reduced-motion`。
4. **克制（Restraint）**：单一强调色（accent）只用于主操作、激活态与**指定的活力焦点（见第 5 条）**；中性灰承载约 90% 的界面；颜色一旦泛滥，清晰即崩塌。
5. **活力焦点（Vitality）**：在克制的骨架上，允许**少数高辨识度的"活力时刻"**——仪表盘 Hero 焦点卡、指标渐变图标、趋势 delta、环形进度、持续微动。它们只出现在**焦点**（数据概览 / 关键指标），主体表格、表单、导航仍保持克制清晰。核心口诀：**克制的骨架 + 克制的活力时刻**，宁少而精，忌处处装饰——"素"与"花"都是失败。

## 1. 令牌体系总览（Design Tokens）

所有设计决策沉淀为 CSS 变量，分为五组：**色彩、排版、间距、圆角与材质、动效**。
**本规范的令牌取值表即唯一事实源**，各前端工程在自己的令牌 / 工具文件里**实现**本规范的取值；本规范不绑定任何单个工程的路径。

> **当前落点**：产品前端主题与原型主题的位置见工程配置「项目规范」。

- 组件**不得硬编码**主题色值（背景 / 边框 / 文字 / 主色 / 阴影 / 动效曲线），一律引用变量。
- 组件内部的结构性装饰色（如指标分类色）允许在 `<style scoped>` 中用 hex，但须**克制（≤3 种）**，且优先取自下文"数据可视化色板"。
- 新增语义颜色须先在 `:root` 定义变量再使用。
- **暗色模式为一等公民**：每个颜色变量都必须提供亮 / 暗两套值，见 §2.4。

---

## 2. 色彩系统

### 2.1 强调色 · System Blue（accent）

单一强调色。数据报表场景中蓝色最沉稳、辨识度高，且不与多色系图表打架。

**填充与文字分属两个令牌**：同一个蓝作填充底（配 `--accent-contrast`）与作文字（压在界面底上）需要的明度相反，用一个令牌兼任必有一侧不达 §21 阈值。

| 变量 | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| `--accent` | `#0F62CC` | `#0A84FF` | 主按钮填充、激活背景、聚焦环 |
| `--accent-hover` | `#0B57B8` | `#409CFF` | 悬停 |
| `--accent-pressed` | `#08479A` | `#2E90FF` | 按下瞬时 |
| `--accent-soft` | `#EAF3FF` | `rgba(10,132,255,.16)` | 激活背景、微染、pill 底 |
| `--accent-contrast` | `#FFFFFF` | `#0B0F14` | accent 填充之上的文字 |
| `--accent-ink` | `#0F62CC` | `#409CFF` | **accent 作文字**：链接、激活态导航项、tag 文字 |

亮色三档必须整体同向：`--accent-hover` 比 `--accent` 深、`--accent-pressed` 最深，否则悬停反馈方向反了。暗色主按钮为「亮蓝底 + 深墨字」——暗色下白字压任一档蓝底都不达阈值，翻转 `--accent-contrast` 是唯一同时保住色相与阈值的解。

### 2.2 语义色（Semantic）

每个语义分四层：`--x` 作填充与图标，`--x-soft` 作微染底，`--x-ink` 作压在微染底上的文字，`--x-contrast` 作压在 `--x` 填充之上的文字（与 §2.1 的 `--accent-contrast` 同理：填充底与文字分属两个令牌）。

| 变量 | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| `--success` / `--success-soft` / `--success-ink` / `--success-contrast` | `#187A36` / `#E8F8ED` / `#17692F` / `#FFFFFF` | `#30D158` / `rgba(48,209,88,.16)` / `#30D158` / `#0B0F14` | 成功、正向指标 |
| `--warning` / `--warning-soft` / `--warning-ink` / `--warning-contrast` | `#AD5700` / `#FFF3D6` / `#7A4A00` / `#FFFFFF` | `#FFD60A` / `rgba(255,214,10,.16)` / `#FFD60A` / `#0B0F14` | 提醒、待处理 |
| `--danger` / `--danger-soft` / `--danger-ink` / `--danger-contrast` | `#B42318` / `#FDECEB` / `#B01F17` / `#FFFFFF` | `#FF453A` / `rgba(255,69,58,.18)` / `#FF7A70` / `#0B0F14` | 危险操作、错误、异常 |
| `--info` / `--info-soft` / `--info-ink` / `--info-contrast` | `#5AC8FA` / `#E8F7FF` / `#0C5E7B` / `#0B0F14` | `#64D2FF` / `rgba(100,210,255,.18)` / `#64D2FF` / `#0B0F14` | 中性提示 |

`--x-contrast` 的明暗由 `--x` 填充的明度定，不按主题一刀切：暗色四档填充都是高明度彩色，故四个 `--x-contrast` 一律取深墨 `#0B0F14`；亮色里 `--info` 本身是浅青，白字压它远不达 §21 阈值，故亮色 `--info-contrast` 同样取深墨，其余三色亮色填充够深，取白。

新增语义色须同时给出四层（**漏 `--x-contrast` 则该语义不得用于填充按钮 / 徽标**），并通过 §2.7 的机械核算后才能进入本表。

### 2.3 中性灰阶（Cool Gray）

微冷色调的中性阶，承载绝大多数界面。

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--gray-50` | `#F7F8FA` | `#1E232B` |
| `--gray-100` | `#F2F4F7` | `#242A33` |
| `--gray-200` | `#E7EAF0` | `#2C333D` |
| `--gray-300` | `#D7DCE5` | `#3A424E` |
| `--gray-400` | `#AEB6C2` | `#525C6A` |
| `--gray-500` | `#8A93A3` | `#77828F` |
| `--gray-600` | `#647085` | `#98A2AF` |
| `--gray-700` | `#45505F` | `#C0C7D1` |
| `--gray-900` | `#161B22` | `#F2F4F7` |

### 2.4 语义化令牌（组件只引用这一层）

组件**只引用**下表语义变量，绝不直接引用 §2.3 的原子灰阶或写死 hex。语义变量在亮 / 暗主题下自动切换。

| 变量 | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| `--bg` | `#F2F4F7` | `#0B0F14` | 全局分组背景（内容区） |
| `--bg-soft` | `#F7F8FA` | `#141920` | 次级背景 |
| `--surface` | `#FFFFFF` | `#16191F` | 卡片、弹窗抬起面 |
| `--surface-2` | `#F7F8FA` | `#1E232B` | 卡片内嵌块（指标块、分页条） |
| `--separator` | `rgba(60,60,67,.11)` | `rgba(255,255,255,.10)` | 发丝分隔线（0.5px） |
| `--border` | `#E7EAF0` | `#2C333D` | 必要的实体边框 |
| `--border-strong` | `#D7DCE5` | `#3A424E` | 强调边框 |
| `--text` | `#161B22` | `#F2F4F7` | 主文字 |
| `--text-secondary` | `#4A5568` | `rgba(235,235,245,.66)` | 次级文字 |
| `--text-tertiary` | `#616D82` | `rgba(235,235,245,.64)` | 辅助 / 占位 / 空状态 |

暗色这两档是半透明白，alpha 受 §2.7 承载矩阵里**最严格的一格**约束——`--info-soft` 叠在 `--surface-2`（四种中性底里最浅的一档）之上，文字再叠于其上。**alpha 低于 `.63` 这一格即不达 §21 阈值**（§21 不设宽容带，贴线即判不过）；本表取 `.64` / `.66` 留出余量，并保住「主 → 次级 → 辅助」三档的层级差。**调低这两个 alpha 必须重跑 §2.7 核算**，不得凭目视判「看起来够淡 / 够清楚」。

### 2.5 数据可视化色板

图表、指标分类等**多色**场景专用；不用于界面结构。以 accent 蓝为锚，含一档 teal。

| 变量 | 亮色 | 暗色 | 语义倾向 |
|---|---|---|---|
| `--viz-1` | `#007AFF` | `#0A84FF` | 主序列 |
| `--viz-2` | `#14B8A6` | `#2DD4BF` | 第二序列 |
| `--viz-3` | `#FF9500` | `#FF9F0A` | 第三序列 |
| `--viz-4` | `#34C759` | `#30D158` | 正向 / 达标 |
| `--viz-5` | `#AF52DE` | `#BF5AF2` | 补充序列 |
| `--viz-6` | `#FF375F` | `#FF6482` | 告警 / 未达标 |

> 多序列取色顺序固定为 1→6，保证同一指标跨页颜色一致。图表配色的可访问性与搭配另见 `dataviz` skill。

### 2.6 主题切换机制

```css
:root { /* 默认亮色令牌 */ }

/* 跟随系统 */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* 暗色令牌覆盖 */ }
}

/* 用户手动指定（顶栏切换，优先级最高） */
:root[data-theme="dark"]  { /* 暗色令牌 */ }
:root[data-theme="light"] { /* 亮色令牌 */ }
```

- 默认**跟随系统**；顶栏提供"跟随系统 / 亮 / 暗"三态切换，选择持久化到 `localStorage`。
- 切换时对 `color` / `background` / `border` 施加 `transition: … var(--dur-2) var(--ease-standard)`，实现柔和过渡（不闪烁）。

### 2.7 承载矩阵与机械核算

**哪个文字令牌允许压在哪种底上，由下表穷举**——不在表内的组合不得出现在实现里。表内每一格都必须满足 §21 的对比度阈值，由本工程的**对比度核算命令**（见工程配置「命令」）逐格核算，亮暗各自跑。

| 文字令牌 | 允许的承载底 |
|---|---|
| `--text` / `--text-secondary` / `--text-tertiary` | `--bg`、`--bg-soft`、`--surface`、`--surface-2`，以及全部五种 `--x-soft`（`accent` / `success` / `warning` / `danger` / `info`） |
| `--accent-ink` | `--accent-soft`，以及四种中性底 |
| `--success-ink` / `--warning-ink` / `--danger-ink` / `--info-ink` | 各自的 `--x-soft`，以及四种中性底 |
| `--accent-contrast` | `--accent`、`--accent-hover`、`--accent-pressed` 三档填充 |
| `--success-contrast` | `--success` 填充 |
| `--warning-contrast` | `--warning` 填充 |
| `--danger-contrast` | `--danger` 填充 |
| `--info-contrast` | `--info` 填充 |

半透明底（暗色的 `--x-soft`、`rgba(...)` 文字）按「压在每一种不透明底之上」分别展开核算，不允许只算其中一种。

命令逐格打印比值与判定。**任一格未达标、任一令牌无法机械解析（渐变、`color-mix` 等）、或暗色两块（`@media prefers-color-scheme` 与 `[data-theme="dark"]`）同名令牌取值不同，都以非 0 退出。** 核算器顶部的常量是本节矩阵的可执行副本，改矩阵必须同改那里。

**尚未接入该命令的前端工程**（独立包、原型）须以**同一算法、同一阈值、同一矩阵、亮暗各跑**的单测承担同一判据，未达标同样以非 0 退出。**「本工程没有那条命令」不是跳过核算的理由，目视一律不作数。**

---

## 3. 排版系统

### 3.1 字体栈

以 Apple 系统字体（SF Pro）领衔，中文用苹方，Web 端回退 Inter。

```css
--font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
             "PingFang SC", "Helvetica Neue", "Segoe UI", Roboto, Inter, Arial,
             "Microsoft YaHei", sans-serif;
--font-mono: ui-monospace, "SF Mono", "JetBrains Mono", "Menlo", monospace;

font-family: var(--font-sans);
font-size: 15px;                    /* 正文基准 */
-webkit-font-smoothing: antialiased;
-moz-osx-font-smoothing: grayscale;
text-rendering: optimizeLegibility;
```

### 3.2 字号阶（Type Scale）

层次由**字号 + 字重 + 字距**建立，禁止用颜色深浅充当层级。大标题使用负字距（更紧致、更 Apple）。

| 层级 | 字号 / 行高 | 字重 | 字距 | 用途 |
|---|---|---|---|---|
| Large Title | 28 / 34 | 700 | -0.02em | 页面主标题 `.page-header h2` |
| Title 2 | 20 / 26 | 650 | -0.01em | 汇总卡标题、弹窗标题 |
| Headline | 17 / 22 | 600 | 0 | 卡片 / 分节标题 `.section-title` |
| Body | 15 / 22 | 400 | 0 | 正文、表单标签、菜单项 |
| Callout | 14 / 20 | 400 | 0 | 表格数据、密集正文 |
| Subhead | 13 / 18 | 600 | 0 | 表头、字段标签 |
| Footnote | 13 / 18 | 400 | 0 | 副标题、辅助说明 |
| Caption | 11 / 14 | 600 | +0.06em | 分节标签（大写）`.nav-section-label` |

### 3.3 数字排版

- **所有数值数据**（计数、金额、耗时、日期）使用等宽数字，避免跳动：
  ```css
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1;
  ```
- 大额指标数字可用 `--font-mono` 或 SF Pro 的 tabular 变体，增强"仪表盘"读感。

---

## 4. 间距、栅格与断点

严格 **4pt 基准网格**（8pt 为主节奏），令牌化后杜绝随意像素。

| 变量 | 值 | 典型用途 |
|---|---|---|
| `--sp-1` | 4px | 图标与文字间隙 |
| `--sp-2` | 8px | 紧凑内边距、chip 间距 |
| `--sp-3` | 12px | 控件间距 |
| `--sp-4` | 16px | 卡片间距、表单行距 |
| `--sp-5` | 20px | 卡片内边距 |
| `--sp-6` | 24px | 内容区留白、区块间距 |
| `--sp-8` | 32px | 大区块分隔 |
| `--sp-10` | 40px | 页面级留白 |

- 页面组件竖向间距（`.page` 的 `gap`）：`var(--sp-5)`（20px）。
- 内容区 padding：`var(--sp-6) var(--sp-8)`（24px / 32px）。

### 4.1 响应式断点阶（全站统一 · 强制）

**全站只用这三个断点**，另加一个投屏限宽档。同一页内各区**必须共用同一组断点**——各区自取断点会导致同一屏内各部分在不同宽度分别换行，节奏错乱。

| 档 | 视口 | 典型布局 | 语义 |
|---|---|---|---|
| **投屏 / 宽桌面** | ≥ 1440 | 多列铺满；画布限宽 `min(2200px, 100%)`，**≥2560 放宽至 `min(2800px, 100%)`** | 投屏与宽屏工作站 |
| **桌面** | 1180 – 1440 | 完整多列，宿主壳（侧边栏 + 顶栏）常驻 | 主力使用场景 |
| **平板 / 分屏** | 768 – 1180 | 多列降为 2 列；并排双卡降为 1 列；卡头标题独占一行 | 平板、分屏、小笔记本 |
| **窄屏** | < 768 | 全部降为 1 列；内容区 padding 收至 14px；宿主壳导航收纳 | 手机自查 |

**写法（强制）**

```css
/* 用区间语法，不用 max-width 逐个试值 */
@media (width < 768px)  { … }   /* 窄屏 */
@media (width < 1180px) { … }   /* 平板及以下 */
@media (width >= 1440px) { … }  /* 宽桌面 / 投屏限宽 */
@media (width >= 2560px) { … }  /* 投屏放宽档 */
```

- **禁止新增本阶之外的断点值**。确有特殊布局需要，须在本次的 spec 中说明理由并经评审，不得就地取值。
- 断点判据是**布局需要**，不是设备型号——同一档内不同设备共用同一套布局。
- **限宽两档的理由**：单一 2200px 上限在逻辑宽 3840 的真 4K 上只占 57%、留白 43%，违背投屏「远距离可读」初衷；多数 4K 电视按 1080p/1440p 缩放呈现（逻辑宽 1920–2560），故 2200 覆盖常见场景、2800 兜住真 4K。**投屏相关改动须用实际投屏设备验证，不得只按逻辑宽推算**——设备缩放策略决定实际落在哪一档。
- **断点值落主题令牌文件**（位置见工程配置「项目规范」）供 JS / CSS 共用；§23 移动端形态按本阶的窄屏 / 平板档落地，不另立断点。
- 存量页面尚未对齐本阶的，逐处映射与销账计划写在本工程实例。

---

## 5. 圆角与材质层次

### 5.1 连续圆角（Continuous Corners）

采用偏"超椭圆（squircle）"的较大圆角，视觉更柔和。CSS 无法原生画超椭圆，用**较大 `border-radius` 逼近**，并遵守**同心圆角**规则：内层半径 = 外层 − 内边距。

| 变量 | 值 | 用途 |
|---|---|---|
| `--r-xs` | 8px | chip、tag、小控件 |
| `--r-sm` | 10px | 按钮、输入框 |
| `--r-md` | 12px | 卡片内嵌块、指标图标 |
| `--r-lg` | 16px | 卡片、表格容器、popover |
| `--r-xl` | 20px | 弹窗 |
| `--r-full` | 999px | pill、开关、头像 |

### 5.2 层次阶梯（Elevation）

用光影而非边框表达"抬起"。四级阶梯，每级是一对阴影。

| 变量 | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| `--elev-0` | `none` | `none` | 与背景齐平 |
| `--elev-1` | `0 1px 2px rgba(16,24,40,.06), 0 4px 12px rgba(16,24,40,.05)` | `0 1px 2px rgba(0,0,0,.5)` | 卡片、表格、输入框 |
| `--elev-2` | `0 6px 20px rgba(16,24,40,.10)` | `0 8px 24px rgba(0,0,0,.6)` | 悬停抬起、popover |
| `--elev-3` | `0 24px 64px rgba(16,24,40,.22)` | `0 32px 80px rgba(0,0,0,.72)` | 弹窗 |

> 暗色下阴影辨识度低，改以**表面提亮 + `1px solid var(--separator)` 描边**辅助分层。

### 5.3 磨砂材质（Materials）

顶栏、侧边栏、sticky 表头、popover 使用半透明磨砂玻璃，透出底层内容，产生"浮层"深度。

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--material-chrome` | `rgba(255,255,255,.72)` | `rgba(22,25,31,.72)` |
| `--material-blur` | `saturate(180%) blur(20px)` | `saturate(180%) blur(20px)` |

```css
.chrome {
  background: var(--material-chrome);
  -webkit-backdrop-filter: var(--material-blur);
  backdrop-filter: var(--material-blur);
}
/* 不支持 backdrop-filter 时回退为不透明 --surface */
@supports not (backdrop-filter: blur(1px)) {
  .chrome { background: var(--surface); }
}
```

### 5.4 发丝分隔线（Hairline）

分隔优先用 `--separator`，并在高分屏渲染真正的 0.5px：

```css
.hairline { border-bottom: 1px solid var(--separator); }
@media (min-resolution: 2dppx) {
  .hairline { border-bottom-width: 0.5px; }
}
```

### 5.5 玻璃表面（Glass / 透明灵动）

在磨砂 chrome（§5.3）之外，主体卡片与浮层也施加**克制的玻璃质感**：半透明表面 + `backdrop-filter` 模糊，让底层背景微渐变淡淡透出，营造通透灵动感。

```css
:root { --surface-glass: color-mix(in srgb, var(--surface) 74%, transparent); }

/* 主体卡片 */
.card-glass {
  background: var(--surface-glass);
  -webkit-backdrop-filter: saturate(185%) blur(18px);
  backdrop-filter: saturate(185%) blur(18px);
  border-top-color: rgba(255,255,255,.55);   /* 玻璃顶部亮边 rim light */
}
/* 浮层（弹窗 / 抽屉 / popover / toast）更强 */
.overlay-glass { backdrop-filter: saturate(190%) blur(24px); }

/* 不支持时回退不透明 */
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  :root { --surface-glass: var(--surface); }
}
```

规则：
- **适用范围**：数据卡、指标卡、汇总卡、筛选栏、组织树面板、看板卡等主体卡片，以及弹窗 / 抽屉 / popover / 更多菜单 / toast / 通知等浮层。
- **玻璃亮边**：顶部 `1px` 亮白高光（`rgba(255,255,255,.55)`，亮 / 暗通用），是玻璃"受光边缘"的关键特征。
- **焦点实底例外**：仪表盘 **Hero 焦点卡保持不透明实底**（§11.6），不玻璃化，以维持焦点重量。密集数据表可视需要略提不透明度，保证可读性。
- **主题自适应**：用 `color-mix` 由 `--surface` 派生，亮 / 暗自动切换。
- **降级**：不支持 `backdrop-filter` 时回退不透明 `--surface`；玻璃是"锦上添花"，不得成为可读性前提。

---

## 6. 动效系统（Motion）—— 灵动的核心

### 6.1 曲线与时长令牌

| 变量 | 值 | 语义 |
|---|---|---|
| `--ease-standard` | `cubic-bezier(.4, 0, .2, 1)` | 通用出入 |
| `--ease-out` | `cubic-bezier(.16, 1, .3, 1)` | 减速进场（内容浮现） |
| `--ease-spring` | `cubic-bezier(.34, 1.56, .64, 1)` | 弹性（弹窗、开关、pill） |
| `--dur-1` | 120ms | 微反馈（hover / press） |
| `--dur-2` | 200ms | 常规过渡 |
| `--dur-3` | 320ms | 进场 / 转场 |
| `--dur-4` | 480ms | 大幅位移 / 骨架 shimmer |

### 6.2 微交互（必做）

| 元素 | 状态 | 动效 |
|---|---|---|
| 按钮 / 卡片 / 行 | hover | `transform: translateY(-1px)` + 升至 `--elev-2`，`var(--dur-1) var(--ease-standard)` |
| 按钮 / 可点元素 | press | `transform: scale(.97)`，`var(--dur-1)` |
| 输入框 / 可聚焦元素 | focus | 柔光"绽放"：`box-shadow: 0 0 0 4px var(--accent-soft)` 从 0 扩散；键盘焦点另须 §21 的实线轮廓，柔光不能替代 |
| 开关 / 复选 | 切换 | 滑块 `--ease-spring` 位移 |
| filter pill | 增 / 删 | `--ease-spring` scale-in / scale-out |

### 6.3 进场与转场

- **列表 / 表格行**：载入时逐行 `opacity 0→1 + translateY(8px→0)`，`stagger` 每行延迟 20–30ms，上限约 12 行后不再延迟。
- **弹窗**：`scale(.96)→1 + opacity`，`--ease-spring var(--dur-3)`；背景遮罩同步 `blur` 渐入。
- **页面 / Tab 切换**：交叉淡入 `--dur-2 --ease-out`，避免生硬跳变。
- **数字**：指标卡数值载入时 count-up（约 `--dur-4`，`--ease-out`）。

### 6.4 无障碍降级（必做）

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .001ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 6.5 活力动效（焦点专用）

服务于「活力焦点」（§0 原则 5），**仅用于仪表盘 / 概览等焦点区**，主体列表 / 表单不施加：

- **Bento 卡进场**：弹性 `scale(.96)→1 + translateY` 逐格铺开，卡间 stagger 40–60ms。
- **图标微弹**：指标渐变图标 hover 时 `scale(1.16) + rotate(-6deg)` 回弹（`--ease-spring`）。
- **呼吸脉冲**：实时 / 活跃指示点用扩散淡出的 pulse 环（约 2.2s 循环）。
- **Hero 流光**：焦点卡渐变上一道极轻斜向高光缓慢扫过（≈7s、透明度 ≤ .20），若隐若现，非扫光炫技。
- **环形绘制**：占比环载入时 `--p` 由 0 缓动到目标（约 `--dur-4`、`--ease-out`），数值同步 count-up。
- 循环类动效（脉冲 / 流光）必须在 `prefers-reduced-motion` 下停止（§6.4 已全局覆盖）。

---

## 7. 布局骨架 —— 三层材质工作台

```
┌───────────────────────────────────────────────────────────┐
│  顶栏 Chrome（磨砂玻璃，52px，浮于内容之上）              │
├──────────────┬────────────────────────────────────────────┤
│  侧边栏      │  内容区 content                            │
│  磨砂材质    │  padding: 24px 32px                         │
│  240px 固定  │  背景：var(--bg)（分组灰）                  │
│  内嵌分组    │  内容为大留白的分组卡片                     │
└──────────────┴────────────────────────────────────────────┘
```

- 顶栏与侧边栏是"浮层材质"，内容区在其下滚动、透出磨砂。
- 内容区内容**占满可用宽度**（`.page` 宽度 100%），仅保留内容区自身的 `24px / 32px` 内边距，不做居中限宽。

### 7.1 全屏登录页（无外壳）

登录 / 找回密码等页面**不套三层工作台外壳**，采用「整页背景 + 居中扁平分栏卡」。

```
┌─ 整页背景（中性渐变 + 极光光斑，避免与卡片撞色）──────────────┐
│  ◇ LOGO（左上）                              [跟随/亮/暗]（右上）│
│            ┌───────────────┬────────────────┐                │
│            │  视觉 / 图片区  │   登录表单区     │  ← 扁平分栏卡  │
│            │  品牌渐变+插画  │  标题/账号/密码  │   (横向、居中) │
│            └───────────────┴────────────────┘                │
│                        © 版权（底部居中）                      │
└──────────────────────────────────────────────────────────────┘
```

**登录页专用令牌**（落主题令牌文件，亮/暗双值，仅鉴权页用）：

| 令牌 | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| `--page-bg` | `linear-gradient(150deg,#EAECF1,#DCE0E8,#D2D6E0)` | `linear-gradient(150deg,#1C1F26,#14171F,#0D0F15)` | 登录页素雅底 |
| `--visual-grad` | `linear-gradient(155deg,#0B5ED9,#3538A6,#4B2E9C)` | `linear-gradient(155deg,#0A2E6E,#241E5E,#3A2170)` | 左视觉区（蓝→靛→紫和谐过渡） |

**背景**
- 用**中性色**（如石墨灰渐变 `--page-bg`），**与登录卡的主色明确区分色系**，防止撞色。
- 可叠**极轻的氛围层**破单调：极光光斑（两团柔光缓慢漂移，避开卡片主色）/ 发丝网格 / 点阵 / 噪点，四选一，克制为要；循环动效遵循 `prefers-reduced-motion`（§6.4）。
- 左上品牌标、右上主题切换、底部居中版权，颜色**跟随主题**（勿硬编码白，浅背景会看不见）。
- 品牌标优先用**纯文字 wordmark** 或**磨砂玻璃**融入背景，避免实心色块在氛围背景（极光/渐变）上显得突兀。

**登录卡（扁平分栏）**
- 横向宽扁比例（约 `960–1040 × 410`），扁平：轻投影 + 顶部微亮边，圆角 `--r-xl`，`overflow:hidden`。
- **左 · 视觉/图片区**（约 45%）：品牌渐变 + 契合插画 / 图片 + 一句话标题（**单行不换行**）。
- **右 · 表单区**：竖向居中排布。

**表单**
- 登录方式**以产品实际启用为准**：表单顶部用**标题**（如「账号密码登录」）标识当前主方式，不强制用 Tab。
- 输入框：前置语义图标 + 聚焦绽放（§15）；密码显隐；记住我 + 找回密码 / 注册入口（按产品启用）。
- 主按钮**全宽** + 提交 loading。
- 校验与反馈遵循 §15.3 / §19。
- **可选扩展**（产品需要多登录方式时才加）：Tab 切换（下划线滑动，§10.1 同款）/ 手机验证码（「获取验证码」60s 倒计时）/ 底部 `—— 或 ——` + SSO 圆形图标按钮。
- 本产品启用哪些登录方式、「记住我 / 找回密码 / 注册」各取什么形态，写在本工程实例 §7.1。**未启用的方式与可选项，入口一律不渲染**：DOM 中没有对应节点，也不以置灰或点了弹 toast 的占位冒充（同 §8.1「不可用项」与 §23.3 末条铁律）；页面级形态见 **`prototypes/<版本>/` 下的 Web UI 原型**（登录页），界面上的承重口径见 **PRD**。

**响应式**：窄屏档（§4.1，`width < 768px`）隐藏左视觉区，仅保留居中表单。

---

## 8. 顶栏 Chrome

- 高度 `52px`；背景 `--material-chrome` + `--material-blur`；**默认无边框**，内容滚动后浮现底部 `--separator`（0.5px）。
- 左：**纯文字 wordmark**（产品名，取工程配置「产品」，写法见本工程实例 §8；18px/800）+ 版本号 pill（`--accent-soft` 底 + `--accent` 字）；**不用实心色块徽标**（与登录页品牌语言统一——氛围/渐变背景上实心色块显突兀）。
- 右：**件数逐身份写死，每一种身份都是一个常数，不多不少** —— 候选件依次为 **主题切换（跟随系统 / 亮 / 暗）** + **区域切换入口**（如「管理中心」，可见性见下文，区域导航见 §9.2） + **消息铃铛**（可见性按下条判，通知中心见 §23.4） + **用户名下拉**（内容见 §8.1）。
  **「恰 N 件」不得退化成「视情况」** —— 本条的作用是**可按 DOM 核的写死数量**（同下条「数量写死」与 §22 走查清单）。逐身份写死 ≠ 「可能两件也可能三件」：**每一种身份下，件数是一个确定的常数，可按节点数断言**。
  **加一件（如全局搜索框）须先推翻本条**，不得就地追加；页面内的检索一律落 §12 筛选栏的 `.search-field`。

- **区域切换入口的可见性 —— 按「能不能进入该区域」判**：能进入 ⇒ 渲染（文字按钮，紧挨在铃铛之前）；不能进入 ⇒ **不渲染**（A 档，DOM 中无节点，**不置灰** —— 置灰暗示「设法可用」，而角色不是界面内能改的东西）。渲染条件取服务端返回的当前角色，与 §9 入口集同源。
  **进、出共用这一件**：入口在主区与另一区里**同一件、同一位置**，文案与去向随所在区变 —— 在主区显示进入另一区的文案，进入后显示返回主区的文案，点它回主区的落地页；不另起一件，也不在另一区的侧栏放返回项（§9.2）。所在区按当前路由判，与进入方式无关（顶栏点进、直接访问路由、区内刷新同形）。
  **入口不带当前态**：它是出入口，不是「你在哪个区」的标记 —— 任何区内都无 `aria-current`，静止态样式两区相同（只文案不同）；所在的面由侧栏激活态（§9）标示。

- **消息铃铛的可见性 —— 按「有可能收到通知的身份」判，不按身份写死**：
  产品的**通知收件人集合**里**有可能出现**某身份 ⇒ 铃铛对他渲染；**一类通知都不可能收到** ⇒ 铃铛对他 **不渲染（§23.3 的 A 档口径：DOM 中无节点，不是置灰、不是空态）**。
  **通知不得被做成只有管理员才有的功能**（同 §23.4 首句）：没有通知可收的身份才没有铃铛，**「只给管理员铃铛」在任何产品里都会被本条判红**（管理员若一类都收不到，他恰是那个没有铃铛的身份）。
  **渲染条件写在需求侧、不写在页面里**：实现**不得按身份分支**（`v-if="user.isAdmin"` 之类，同 §8.1「内容须逐项声明」与 §24.1 的能力集口径）；件集与 §9 侧边栏的入口集同源。
  **须给出逐身份的 DOM 判据**（可自动化断言）：每一种身份下 `.topbar-right` 的**直接子元素数**（选择器 `.topbar-right > *`，**不含后代**）与铃铛节点数**各是一个写死的常数**。
  **被计数的对象必须是「直接子元素」，不能是「按钮数」** —— 人眼概念上的「一件」与 DOM 上的一个 `button` **不是同一个对象**：顶栏的一件可以是一个**容器**、内含多个 `button`（如三态主题切换，§2.6）⇒ 数 `button` 会把一件数成三件，**判据按字面必然判红一个正确实现**；而为满足它去把容器拆成单按钮，又会推翻 §2.6。
  **通则**（契约 §五）：**凡计数判据，被计数对象必须是 DOM / 文本上可唯一圈定的集合，且写明圈定方式**（选择器 ＋ 层级）；**不得用「件 / 项 / 条」这类人眼量词充当被计数对象**。**每一「件」恰是 `.topbar-right` 的一个直接子节点** —— 这条映射是本条成立的前提，实现不得把一件拆成多个直接子节点。
  **须写明失效条件**：某身份今天没有铃铛，是因为他今天不在任何一类通知的收件人集合内 —— **一旦产品给他任一类通知，本条自动使铃铛回来**。**不得在任何产品文档里留一条无条件的「某身份没有铃铛」。**

本产品各身份的顶栏件数、区域切换入口的文案与去向、铃铛对哪些身份渲染及其 DOM 判据，写在本工程实例 §8。
- 图标按钮：`36×36`，圆角 `--r-full`，hover 显示 `--gray-100` 圆形底 + `--dur-1` 过渡。

### 8.1 用户名下拉的内容（强制基准）

| 项 | 规则 |
|---|---|
| 触发区 | 用户名（Body 15/500，`--text-primary`）+ 右侧 chevron；hover 同 §8 图标按钮；**不渲染头像占位方块**（无真实头像时不用首字母色块冒充） |
| 浮层 | `--surface` + `--elev-2` + `--r-lg`，右对齐顶栏右边缘；宽度 `180–220px`；进场遵 §6.3 |
| **内容须逐项声明** | 下拉项**由需求逐项声明，数量写死**；**未声明的项一律不得出现**（同 §24.1 对工具栏的口径）。**不得**在此放任何业务入口（**任何业务对象的列表 / 详情 / 创建入口**），业务入口一律归 §9 侧边栏。<br>**通则正文不写任何产品事实** —— 产品对象名、业务面枚举一律落本工程实例 §8.1（两层结构同 §12「『全部』是清空态」那条通则） |
| 分区 | 第一区 ＝ 账号自助动作；末区 ＝ 退出登录，与上方以 `--separator` 分隔；**退出登录恒为最后一项** |
| 受限态 | 「必须改密」等不套工作台外壳的受限态下，**顶栏整条不渲染** ⇒ 本下拉随之不存在（A 档，DOM 中无节点），不得渲染一个点了无效的下拉 |
| 不可用项 | 本版不提供的项**不渲染**（A 档），不以置灰或点了弹 toast 的假项冒充（同 §23.3 末铁律） |

本产品下拉的逐项清单写在本工程实例 §8.1；页面级形态见 **`prototypes/<版本>/` 下的 Web UI 原型**。

---

## 9. 侧边栏 —— 内嵌磨砂分组导航

macOS「系统设置」式材质面板，**常驻展开**（不折叠、不手风琴）。

```html
<nav class="side-menu">
  <a class="nav-item"><i class="nav-icon">…</i> 顶级菜单项</a>
  <div class="nav-section-label">分节标签</div>
  <a class="nav-item nav-child"><i class="nav-icon">…</i> 子菜单项</a>
</nav>
```

| 元素 | 规则 |
|---|---|
| `.side-menu` | 240px，`--material-chrome` + `--material-blur`，右侧 `--separator`，内边距 `var(--sp-3)` |
| `.nav-section-label` | Caption（11px 大写 +0.06em），`--text-tertiary`，`margin: var(--sp-4) var(--sp-3) var(--sp-1)` |
| `.nav-item` | Body（15px/500），圆角 `--r-sm`，padding `9px 12px`，含 `--nav-icon`（18px 单色描边图标，`--text-secondary`），`gap: var(--sp-2)` |
| `.nav-child` | 继承 `.nav-item`，`padding-left: 34px`，字号 14px |
| hover 态 | 背景 `--gray-100`（暗色 `--surface-2`），`--dur-1` 过渡 |
| **激活态** | 背景 `--accent-soft`，文字与图标 `--accent-ink`，字重 600；圆角 pill；可选左侧 3px accent 竖条或内发光 |

### 9.1 多级菜单层级

| 层级 | 承载位置 | 说明 |
|---|---|---|
| L1 一级 | 侧边栏 `.nav-item` | 顶级入口 |
| L2 二级 | 侧边栏 `.nav-child`（分组标签下） | 子入口；**侧边栏到此为止** |
| L3 三级 | **内容区顶部下划线页签**（§10.1） | 进入某个 L2 页面后的子视图切换 |

- **侧边栏最多 2 级**：常驻展开、清晰优先，不做第三级缩进树，也不折叠 / 手风琴。
- **第三级用页内页签**，不塞进侧边栏——避免深层缩进与"藏起来 + 多一次点击"的认知成本。
- 页签是**导航**（切换不同子视图），须与"筛选分段控件（§12，同一视图内过滤）"在语义与形态上区分清楚，不可混用。

### 9.2 区域导航（工作区 / 管理区）

- 产品有不同读者的两组面（如业务面与系统管理面）时，分成**两个区**，**各用一套侧栏，互斥渲染**：不在同一侧栏里用分组标签并列。
- **进入**另一区与**返回**主区共用顶栏同一个区域切换入口（§8）：文案随所在区变，返回落回主区的落地页。**侧栏只放本区的面，不放返回项。**
- 两个区共用同一个顶栏，件数不因所在区而变（§8）。
- 落地页只按主区侧栏的入口集算出；区域切换入口不参与。

本产品两个区各自的侧栏入口、落地页，写在本工程实例 §9.2；页面级形态 ＝ **`prototypes/<版本>/` 下的 Web UI 原型**。

---

## 10. 页面结构模板

所有列表页统一结构，组件竖向间距 `var(--sp-5)`（20px，由 `.page` 的 `gap` 控制）：

```html
<section class="page">
  <!-- 页标题（直接路由页面必须有） -->
  <div class="page-header">
    <h2>页面标题</h2>              <!-- Large Title 28 -->
    <p class="page-subtitle">副标题 / 说明</p>   <!-- 可选，Footnote -->
    <!-- 可选：右侧主操作按钮 -->
  </div>

  <!-- 筛选栏（见 §12） -->
  <div class="filter-bar"> … </div>

  <!-- 汇总信息卡（可选，见 §11.4） -->
  <section class="summary-card"> … </section>

  <!-- 数据卡片 -->
  <div class="data-card">
    <el-table :data="rows" v-loading="loading">…</el-table>
    <p v-if="!loading && rows.length === 0" class="empty-state">暂无数据</p>
    <div v-if="total > 0" class="pagination"><el-pagination … /></div>
  </div>
</section>
```

**页标题规则**：
- 直接路由访问的页面**必须**有 `.page-header`。
- 嵌入 `el-tabs` 面板的组件**不加**页标题，由 tab 标签提供上下文。
- 双模式组件用 prop 控制：`v-if="!isAdminMode"`（prop `admin: Boolean`，默认 `false`）。

### 10.1 三级菜单 · 页内下划线页签（`.l3-tabs`）

L3（第三级菜单）不进侧边栏，改为**页标题下方的下划线页签**，进入某个 L2 页面后在此切换子视图。

```html
<div class="page-header"><h2>用户列表</h2></div>

<nav class="l3-tabs" role="tablist">
  <a class="l3-tab active">全部</a>
  <a class="l3-tab">内部用户</a>
  <a class="l3-tab">外部用户</a>
</nav>

<!-- 当前页签对应的内容（筛选栏 + 数据卡片…） -->
```

```css
.l3-tabs { display:flex; gap:var(--sp-5); border-bottom:1px solid var(--separator); }
.l3-tab {
  position:relative; padding:10px 2px; font-size:15px; font-weight:500;
  color:var(--text-secondary); cursor:pointer;
  transition:color var(--dur-1) var(--ease-standard);
}
.l3-tab:hover  { color:var(--text); }
.l3-tab.active { color:var(--text); font-weight:600; }
.l3-tab.active::after {                 /* accent 下划线，切换时滑动 */
  content:""; position:absolute; left:0; right:0; bottom:-1px; height:2px;
  background:var(--accent); border-radius:2px;
}
```

规则：

- **数量 2–5 个，理想 ≤4**；超过 5 个应触发反思（多半不是真正平级，应拆分为不同 L2 入口），超出时用"更多 ▾"收纳或横向滚动 + 边缘磨砂渐隐，禁止无限排列。
- **每个页签带独立路由**（如 `/users-list/internal`），可分享、可刷新、可前进后退；不要用纯前端 `v-show` 顶替路由。
- 切换时下划线在页签间**滑动过渡**（`--dur-2 --ease-standard`），非瞬间跳变。
- 与筛选分段控件区分：页签用于"换子视图"（下划线形态、在页标题下方）；分段控件用于"同视图内过滤"（分段胶囊形态、在 `.filter-bar` 内）。

### 10.2 组织树 · 双栏 Master–Detail（复杂交互专项）

组织架构等**层级数据**统一采用**双栏 Master–Detail**：左侧组织树常驻，右侧为选中节点的详情。

```
┌ .org-layout（grid: 320px 1fr）────────────────────────────┐
│ ┌ .tree-panel ─────┐  ┌ 详情区 ────────────────────────┐ │
│ │ ⌕ 搜索组织        │  │ 面包屑（可回跳）                │ │
│ │ ▾ 集团总部 (1240) │  │ 当前组织概览（.summary-card）    │ │
│ │   ▾ 研发中心 (320)│  │ 直接下级组织（.data-card + 表）  │ │
│ │      前端组 (48)  │  │                                 │ │
│ └──────────────────┘  └────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

**布局与总原则**
- 左栏 `.tree-panel` 固定约 `280–320px`，`--surface` + `--elev-1`，内置搜索框（顶部）+ 可滚动树体。
- 右栏详情自上而下：**面包屑 → 汇总卡（§11.4，"当前组织：{名称}" + 指标块）→ 直接下级组织表（§11.2）**。
- 详情随选中节点更新，切换时**交叉淡入**（`--dur-2 --ease-out`），不整屏刷新。
- 左树栏可在**内容区内临时收起**（`.org-layout.collapsed` → `grid-template-columns: 0 1fr`，`--dur-3` 过渡），详情平滑铺满。**注意：这是内容区内的收起，与"侧边栏不折叠（§9）"是两回事，不冲突。**

**树节点样式（`.tree-node`）**

| 元素 | 规则 |
|---|---|
| 行 | 高 `40px`，圆角 `--r-sm`，`gap: 6px`；每级缩进 `padding-left: 8 + depth×18` px |
| 层级表达 | **靠缩进 + chevron**，Apple 惯例**不画粗连接线**；如需引导线仅用 `--separator` 发丝级 |
| chevron | 18–20px，展开时 `transform: rotate(90deg)`，`--dur-2 --ease-standard`；叶子节点占位留白对齐 |
| 名称 | Callout（14px），`show-overflow` 省略号截断 |
| 计数徽标 | 节点右侧 pill，`tabular-nums`，`--surface-2` 底；显示该节点用户数等 |
| hover | 背景 `--surface-2`，`--dur-1` |
| **选中态** | 背景 `--accent-soft` + 左侧 3px accent 竖条；名称与徽标转 `--accent` / 加粗 |

**展开 / 收起动效**
- 子级容器用高度动画平滑展开（推荐 `grid-template-rows: 0fr → 1fr` + 内层 `overflow:hidden`，或等效 max-height 方案），配合子项 `opacity/translateY` **逐级 stagger** 淡入。
- **懒加载**：首次展开未加载的节点，先在其下渲染 **2–3 行骨架**（§13.2 shimmer），数据到达后替换。

**搜索**
- 树顶搜索框实时过滤：**仅保留命中节点及其祖先**，**自动展开命中分支**，命中文字用 `<mark>`（`--warning-soft` 底）高亮。
- 聚焦态复用搜索框绽放规则（§12）。

**面包屑**
- 展示从根到当前节点的路径；除末级外每级可点击回跳。**属导航**，与筛选分段控件语义区分（同 §10.1）。

**下钻联动**
- 右侧"直接下级组织"表每行提供"进入"，点击后**联动左树展开并选中**该子节点，实现"表格 → 树"的下钻，与直接点树保持同一选中状态。

**数量与深度建议**
- 组织层级建议 ≤6 级；超深层级依赖搜索与面包屑定位，不强行全展开。
- 大数据量必须懒加载子节点；一次性加载全树仅限已知小规模场景。

**落地提示**
- 可用 Element Plus `el-tree`（`lazy` + `load` 懒加载 + `filter-node-method` 搜索）承载，或自定义递归组件；无论哪种，视觉与动效均须符合本节。
- 详情区组件复用 §11.4 汇总卡与 §11.2 数据卡片，不另起样式。

### 10.3 工作台账看板（Kanban · 复杂交互专项）

**有状态流转**的记录（如任务 / 工单类台账；产品若无此类场景可略）用 **Trello 式看板**：按状态分列，每条记录 = 一张卡片，可在列间拖动改状态。与数据表是同一数据的两种视图，可切换。

> ⚠ **本节正文中的对象名、字段名都是举例**：引用本节时先核该词在本产品中有无对象（本产品的说明见本工程实例 §10.3）。
> **本节的字段枚举是举例、不是强制清单**：各产品版本的看板卡片字段**由其 PRD 逐项声明、由 Web UI 原型呈现**。

**看板整体**
- 顶部工具条：筛选（如层级维度 = §12.1 树形下拉）+ 搜索 + 主操作（新建）。
- **状态泳道**：每个状态一列（如 待启动 / 进行中 / 已完成 / 已搁置）；列头 = 状态色条 + 列名 + **计数徽标**；列体可纵向滚动。
- 列建议 3–5 个；过多则考虑分组或换表格视图。

**卡片 anatomy（一条记录 = 一张卡）**
```
┌───────────────────────────┐
│ ●优先级        [逾期]      │  优先级色点 + 逾期红标(条件)
│ 记录标题（最多两行截断）    │
│ 👤 负责人 · 归属           │  头像 + 负责人 + 归属
│ 🗓 启动 → 结束 · 剩 N 天    │  时间区间 + 剩余/逾期(逾期标红)
│ ▓▓▓▓▓░░░                  │  进度条（accent）
│ ✔ 5/8 子项         62%     │  子项完成度 + 百分比
└───────────────────────────┘
```
- 卡片 `--r-xs`~`--r-sm` 圆角、`--elev-1`、玻璃表面（§5.5）；hover 抬起。
- **逾期**：过结束时间且未完成时，卡片右上 danger 红标 + 结束日/剩余天数标红。
- 颜色只落在优先级点、逾期标、进度条几处焦点（§0 原则 5）。

**交互**
- **拖拽改状态**：卡片在列间拖动，落下即改状态；拖动时卡片浮起（`--elev-2` / 半透）、原位留虚线占位、**目标列高亮**（`--accent-soft` + accent 内描边）；落定弹 toast 反馈（§19）。
- **点击卡片**：右侧**详情抽屉**滑入（`--ease-out`、`--elev-3`、玻璃），展示子项及各自进度。
- **空列**：显示「暂无{记录}」空态（§18）。
- 卡片载入逐张 stagger（§6.3）。

**落地提示**
- 拖拽可用原生 HTML5 DnD 或 `vuedraggable`；落列即提交状态变更。
- 状态列的语义色：中性（待启动）/ accent（进行中）/ success（已完成）/ warning（搁置）；逾期用 danger，仅作标记不单列。

### 10.4 大屏 / 投屏（只读展示态）

**投屏展示态**（远距离、无人操作、可轮播）是与常规交互页不同的界面语言，用**独立「大屏模式」外壳**，不套侧边栏 / 标准顶栏。

> **本节是通用规则**：产品是否提供大屏、有哪几种屏、各屏的登录要求与内容，写在本工程实例 §10.4。**本工程实例声明不提供大屏的产品，不得据本节渲染任何入口**（A 档，相关路由不存在）。

**外壳（`.board-shell`）**
- 脱常规 app 外壳：**无侧边栏、无标准顶栏 chrome**；沉浸背景复用 §7.1 `--page-bg` + aurora（`prefers-reduced-motion` 停飘移）。
- **顶部条**：产品名 + 范围切换器（下拉 / 轮播）+ 当前统计口径（如本月、当前考核周期）+ **数据新鲜度标注**（外部单向推送的数据可能陈旧，须显式标「截至 …」，不得暗示实时）+ 全屏按钮。
- **主区**：§11.6 Bento，一个 Hero 焦点卡领衔（大屏模式 Hero 数字放大至 **≈72px**，常规仪表盘为 ≈52px）。
- **限宽**：画布限宽按 §4.1 的投屏两档（`min(2200px, 100%)`，≥2560 放宽至 `min(2800px, 100%)`）。

**内容（聚合 · 只读）**
- Hero + 辅助卡只消费**聚合数据**；指标集合由 PRD 逐项声明。
- **只读**：大屏不承载任何写操作；下钻仅在授权登录态生效，面包屑返回不丢已选范围与周期。

**隐私红线（结构性）**
- 大屏仅消费**允许公开展示**的聚合数据；受限数据在**服务端授权强制点隔离**（不靠前端隐藏兜底；隔离由授权关系与谓词保证，不由端点数量保证）。
- 免登录投屏（若启用）**零个人敏感字段**：不点名、不出未达标名单式榜单。

**进出与刷新**
- **进入**：常规仪表盘右上角「大屏展示」按钮，或 `F11`。
- **退出**：`ESC`，或屏幕右上角常驻的悬浮「退出」按钮（两者并存，不可只留其一——投屏现场未必有键盘）。
- **筛选状态延续**：进入时**继承常规仪表盘当前筛选**（不重置为全量）；退出后**恢复为进入前的筛选状态**。独立 route 与状态延续经会话态传递实现，二者不冲突。
- **数据刷新**：每 30 秒静默刷新，**顶部条右侧常驻「最后刷新 HH:mm:ss」时间戳**（`tabular-nums`）。刷新不闪屏、不出全屏遮罩。

**轮播**：多范围 / 多视图自动轮播（≈8–10s/屏），提供暂停 / 上 / 下一屏手动控件；`prefers-reduced-motion` 下**停止自动轮播**、保留手动切换（§6.4）。轮播为可选能力，**由各产品版本的 PRD 显式声明启用与否**，不默认开启。

**落地**：独立 route（如 `/board` 或 `/dashboard?screen=1`）+ fullscreen CSS；权限走统一权限工具函数，不前端硬编码。

---

## 11. 卡片规范

### 11.1 通用卡片

**用光影与背景对比分层，去掉 1px 实体边框。**

```css
.card {
  background: var(--surface);
  border-radius: var(--r-lg);           /* 16px */
  box-shadow: var(--elev-1);
  border: none;                          /* 暗色下改用 1px solid var(--separator) 辅助 */
}
```

### 11.2 数据卡片（`.data-card`）

将表格与分页封装在同一抬起面内：

```css
.data-card {
  background: var(--surface);
  border-radius: var(--r-lg);
  box-shadow: var(--elev-1);
  overflow: hidden;                      /* 裁切内部圆角 */
}
```

- 内部 `el-table` 去掉独立边框 / 圆角 / 阴影（由 `.data-card .el-table` 覆盖）。
- 内部分页 `.pagination` 置于卡片底部，用顶部 `--separator` 与表格分隔，背景 `--surface-2`。

#### 11.2.1 卡片头（`.data-card-header`）—— 全站数据卡片统一必带

**规则（强制）**：所有 `.data-card`（列表页主表、弹窗内数据表、汇总表等）**必须带卡片头**，明确该卡片"是什么数据"。卡片头置于表格之上、卡片顶部，用底部 `--separator` 与表格分隔。

卡片头承载三类内容：**数据名标题 + 计数**（左）、**数据操作按钮**（新增 / 批量 靠左组、导入 / 导出 靠右组）。数据操作**内嵌卡片头**，不独立成卡（排布规则见 §12.2）。

```html
<div class="data-card">
  <div class="data-card-header">
    <div class="dch-title">用户列表<span class="dch-count">共 128 条</span></div>
    <div class="action-primary">                <!-- 靠左：新增/批量编辑/批量删除 -->
      <el-button type="primary">＋ 新增</el-button>
      <el-button :disabled="!selected.length">批量删除</el-button>
      <span v-if="selected.length" class="action-selected">已选 {{ selected.length }} 项</span>
    </div>
    <div class="action-io">                      <!-- 靠右：导入/导出（margin-left:auto） -->
      <el-button>导出 CSV</el-button>
    </div>
  </div>
  <el-table … />
  <div class="pagination">…</div>
</div>
```
```css
.data-card-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
  min-height: 52px;
  padding: var(--sp-3) var(--sp-5);
  border-bottom: 1px solid var(--separator);
}
.data-card-header .dch-title {
  color: var(--text);
  font-size: 15px;
  font-weight: 650;
}
.data-card-header .dch-title .dch-count {
  margin-left: var(--sp-2);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
}
/* 右对齐组：导入/导出、卡片级轻操作 */
.data-card-header .dch-extra,
.data-card-header .action-io { margin-left: auto; }
```

**标题口径（强制）**：**所有数据卡片的卡片头必须带数据名标题 `.dch-title` + 计数 `.dch-count`**（有分页 total 时）。多数据卡片页各卡以标题相互区分。标题即使与页面 `<h2>` 同名也保留（统一优先，卡片头自成一体标识该卡数据）。

- **数据操作内嵌卡片头**（新增 / 批量 / 导入 / 导出）：`.action-primary`（左组，紧随标题）+ `.action-io`（右组，靠右），排布规则见 §12.2；`.dch-extra` 为可选的卡片级轻操作（视图切换、列设置）。
- 与 §11.3 `.section-title` 区分：`.section-title` 是页面 / 区块的分节标题（可独立于卡片）；`.data-card-header` 是**数据卡片自带的头**，二者不重复叠加——数据卡片一律用 `.data-card-header`。

### 11.3 分节标题（`.section-title`）

```css
.section-title {
  color: var(--text);
  font-size: 17px;                       /* Headline */
  font-weight: 600;
  padding: var(--sp-4) var(--sp-5) var(--sp-3);  /* 横向与分页对齐 */
}
```

### 11.4 汇总信息卡（`.summary-card`）

展示当前上下文对象的关键指标，位于筛选栏与数据卡片之间。

```css
.summary-card {
  background: var(--surface);
  border-radius: var(--r-lg);
  box-shadow: var(--elev-1);
  padding: var(--sp-5);
}
.summary-card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: var(--sp-4);
}
.summary-card-title {              /* Title 2；单行不换行 */
  flex: 1; margin: 0 var(--sp-4) 0 0;
  font-size: 20px; font-weight: 650; letter-spacing: -0.01em;
  color: var(--text);
}
.summary-metrics {
  display: grid; gap: var(--sp-3);
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}
.summary-metric {
  background: var(--surface-2);
  border-radius: var(--r-md);
  padding: var(--sp-4);
}
.summary-metric span {             /* Footnote */
  display: block; font-size: 13px; color: var(--text-secondary);
  margin-bottom: var(--sp-1);
}
.summary-metric strong {           /* 数值，等宽数字 */
  font-size: 22px; color: var(--text);
  font-variant-numeric: tabular-nums;
}
```

### 11.5 指标卡（Dashboard 专用）

作为「活力焦点」（§0 原则 5），指标卡图标用**渐变色 squircle + 白色线性图标 + 同色柔光**，数值旁附**趋势 delta**：

```html
<div class="metric-card">
  <div class="metric-icon g-blue"><svg>…线性图标…</svg></div>
  <div class="metric-body">
    <p>指标名称</p>
    <strong>指标数值</strong>              <!-- count-up + tabular-nums -->
    <span class="delta up">▲ 12.4%</span> <!-- 趋势徽标，可选 -->
  </div>
</div>
```

- `.metric-icon`：`44×44`，圆角 `--r-md`，**135° 语义色渐变**背景 + 白色 SVG 线性图标（`stroke:#fff`）+ 同色柔光投影 `0 8px 18px -6px {色}/.5`；hover 图标微弹（§6.5）。
- **必须用 SVG 线性图标**，禁用字符 / emoji（避免占位符廉价感）。
- **趋势 delta（可选）**：`.delta.up`（`▲`，`--success` / `--success-soft`）、`.delta.down`（`▼`，`--danger` / `--danger-soft`），胶囊小徽标，带来颜色与意义。**仅当该指标本身有趋势语义时才出现；无 delta 不是缺陷，且不得以 `0`、箭头或占位文案替位。**

渐变图标配色：

| 类名 | 渐变（135°） | 柔光色 | 典型用途 |
|---|---|---|---|
| `.g-blue` | `#3AA0FF → #0A6FE0` | 蓝 | 主指标 |
| `.g-amber` | `#FFC24B → #FF8A00` | 琥珀 | 数量类指标 |
| `.g-green` | `#5FE08A → #22A745` | 绿 | 正向 / 达标类指标 |
| `.g-teal` | `#4EE6D0 → #12B3A4` | teal | 活跃类指标 |
| `.g-violet` | `#9B8CFF → #6C5CE7` | 紫 | 补充指标 |

> 紧凑 / 密度优先场景用 `-soft` 平色图标；仪表盘等焦点区用渐变版。

### 11.6 仪表盘 Bento 布局 与 Hero 焦点卡

仪表盘 / 概览页用 **Bento 便当栅格**建立主次，而非等宽平铺：

- **栅格 `.bento`**：多列网格（如 `grid-template-columns: repeat(4,1fr)` + `grid-auto-rows` 定基高），卡片以 `grid-column / grid-row: span N` 错落排布。
- **Hero 焦点卡**：跨约 `2×2` 的大卡，**accent 渐变实底 + 白字超大数字（≈52px）**，是全页视觉焦点，可选极轻流光（§6.5）；**趋势 delta 可选**（同 §11.5：无 delta 不是缺陷，不得占位替位）。**每页至多一个 Hero。**
- **辅助卡**：环形占比（`conic-gradient` 绘制 `--p`）、最近活动列表等；小指标块用 §11.5 渐变图标卡。
- **进场**：Bento 卡弹性逐格铺开（§6.5）；hover 抬起至 `--elev-2`。
- **响应式**（断点见 §4.1）：平板档（`< 1180px`）降为 2 列、Hero 与宽卡跨满整行；窄屏档（`< 768px`）降为 1 列。
- **克制护栏**：整页高饱和只出现在 Hero + 指标图标 + delta + 环形几处焦点，其余靠留白与中性灰——避免从"素"矫枉到"花"。

### 11.7 图表表达（无图表库 · SVG/CSS 手绘）

现有系统无图表库，图表库选型属 **TA 技术依赖**。在定库前，趋势 / 占比 / 对比 / 榜单一律用**纯 SVG/CSS 手绘**表达：零依赖、SE 可直接实现，**TA 定库后按同一设计契约平滑替换**（契约 = 下列结构与取色不变）。

| 图表 | 表达 | 取色（§2.5） |
|---|---|---|
| **趋势折线** | inline SVG `polyline` + 数据点 + **X/Y 坐标轴** + 末点数值标注（`tabular-nums`）；完整契约见 §11.7.1 | 主序列 `--viz-1` |
| **阈值线** | SVG `line` 虚线（`stroke-dasharray`），叠加于趋势图；正常点 / 告警点分色 | 阈值 `--text-secondary`、正向点 `--viz-4`、告警点 `--viz-6` |
| **占比 / 完成率环形** | §11.6 `conic-gradient(var(--p))`：正向弧 + 中性余弧 + 中心大数字 % | 正向弧 `--viz-4`，余弧中性灰 |
| **横向对比条** | 水平 CSS 条（宽 = 百分比），右侧数值；多序列按 1→6 顺序 | `--viz-1 → --viz-6` |
| **排行榜** | 列表行：排名 + 名称 + 数值 + 迷你进度条 | 进度条 `--viz-1` |

**规则**
- 取色一律从 §2.5 色板取，语义固定：正向 / 完成 `--viz-4`、告警 / 逾期 `--viz-6`、趋势主线 `--viz-1`、阈值线 `--text-secondary`。
- **暗色一等公民**：SVG `stroke` / `fill`、conic 停色一律引用令牌，亮 / 暗两套自动跟随。
- **不只靠颜色**：正常 / 告警关键值**同时以文本 / 图标**呈现（§21 无障碍）。
- 进场动效（折线描边、环形填充、条形展开）引用 §6 令牌，必做 `prefers-reduced-motion` 降级。
- 配色可访问性与多序列搭配另见 `dataviz` skill。

### 11.7.1 趋势折线 · 坐标系与数值标注（完整契约）

**① 坐标系**

| 轴 | 规则 |
|---|---|
| **Y 轴** | 4 档水平刻度（`0` / ⅓ / ⅔ / 峰值），刻度线 `--separator`；刻度值置图左侧、右对齐、`tabular-nums`、12px `--text-tertiary`，按 ③ 格式化 |
| **X 轴** | 期间标签置图下方、居中于各点，12px `--text-tertiary`；日粒度 `MM-DD`、月粒度 `YYYY-MM`；**按点数抽稀**（见下） |
| 绘图区边距 | 左 ≈56px 容 Y 刻度值、下 ≈28px 容 X 标签 |

**X 轴标签抽稀**（唯一判据 = 点数，防重叠）：

| 点数 | 显示 |
|---|---|
| ≤ 8 | 全部显示 |
| 9–31 | **均匀显示 6 个**，首末必显 |
| 12（年度按月） | 全部显示 |

**② 数据点与数值标注**

- **数据点常显**：每点小圆点（≈7px），取所属序列色。
- **末点数值常显**：末点旁标注数值（`tabular-nums`），重叠时沿 y 方向避让（行距 ≥ 行高 + 6px）。
- **末点标注的非颜色识别通道（强制）**：**序列数 ≥2 时，末点标注须为「序列名 + 数值」**（序列名超 6 字截断，完整名在图例）；单序列时仅数值，不引入冗余。**判据**：避让一旦触发，标注与其末点的空间邻近被削弱，若只有数值则身份识别退化为**仅靠颜色**，违反本节「不只靠颜色」与 §21；而末点标注是**无人操作场景下唯一的识别通道**，不得有识别歧义。
- **悬停 / 键盘聚焦时就地显示**：该 x 位置画垂直指示线（`--separator`），**该位置全部序列的点同时放大**；浮层一次列出「期间 + 各序列名 + 数值」，便于同期对比；移出即消失。
- **不取「全部点常显」**：30 点 × 多序列必然重叠，反破坏基本可读性。**逐点精确值本质是 drill-down，依赖交互是正确的信息分层**；零交互可读性由「坐标轴 + 末点常显」兜底——量级←Y 轴、时间范围←X 轴、当期值←末点、趋势形状←折线，四项全落常显层。

**③ 数值单位契约**（Y 轴刻度 / 末点标注 / 悬停浮层**三处统一**）

三处一律按 §20 的数据展示格式化取单位（如大数计数用紧凑单位 K / M / B、金额用货币符号 + 紧凑单位），本产品的指标类型与格式见本工程实例 §20。

图表组件须接收「指标类型」入参才能选对格式化函数——只传数据序列不足以决定单位。

**④ 无障碍（§21）**

- **悬停不得是唯一途径**：图表可 `tabindex` 聚焦，`←/→` 在数据点间移动并读出当前点的期间与数值（`aria-live`）。
- 序列区分不只靠颜色：图例带序列名，悬停浮层逐行列名，末点标注见 ②。
- `prefers-reduced-motion` 下取消点放大过渡。

**⑤ 实现约束（SVG 非等比缩放陷阱）**

SVG 若用 `preserveAspectRatio="none"` 配合固定高度，x/y 缩放比不等，**其内一切形状与字形敏感元素都会被非等比拉伸**——`<text>` 字形变形、`<circle>` 拉成椭圆，且**拉伸比随容器变宽单调增大**，投屏档最严重。

- **对策**：坐标轴刻度、期间标签、末点标注、数据点**一律用 HTML 绝对定位图层**叠加于 SVG 之上；SVG 内**只保留线性几何**（`<line>`/`<polyline>`），并施加 `vector-effect: non-scaling-stroke` 使其免疫缩放。
- **禁止**对 SVG 内元素施加反向 `transform` 补偿——补偿系数依赖运行时容器宽度，限宽档切换时必失准。

---

## 12. 筛选栏（`.filter-bar`）

抛弃拥挤的单行表单卡，改为 Apple 式筛选栏：**搜索框 + segmented control + filter pill + 高级筛选 popover**。

> **职责边界（重要）**：筛选栏（查询卡）**只承载查询条件**——数据操作（新增/批量编辑/批量删除/导入/导出）一律移入**数据卡片头 §11.2.1 / §12.2**，不得混入查询卡。**唯一例外**：查询卡自身的「查询 / 重置」按钮留在查询卡内、恒**右对齐**（`margin-left:auto`）。这样查询卡在条件少时一行不空、条件多时也不因混装操作按钮而参差。
>
> **收纳与对齐规则**（治"条件多换行不对齐/单条件也两行"）：
> - 查询卡**默认平铺该页最高频的 ≤4 个查询条件**；第 5 个起收进「高级筛选」`el-popover`，选中项回填为 `filter-pill`。
> - 条件控件**统一宽度基准**（§15.2）：不让单个控件（如日期区间）超宽挤乱节奏；换行时须**成列对齐**、左右边缘齐整。
> - 落地取向：**推荐 A｜Flex + 统一宽度**（条件控件等宽 + `.filter-actions{margin-left:auto}` 右对齐查询/重置；主栏 ≤4 条件通常一行放下）；条件确实较多时可用 **B｜Grid**（`repeat(auto-fill, minmax(200px,1fr))`）严格成列。

```html
<div class="filter-bar">
  <!-- 主搜索框：前置放大镜，圆角饱满 -->
  <div class="search-field">
    <i class="icon-search"></i>
    <input v-model="keyword" placeholder="搜索…（⌘F）" @keyup.enter="handleSearch" />
  </div>

  <!-- 常用互斥切换：分段控件 -->
  <el-segmented v-model="status" :options="statusOptions" />

  <!-- 附加条件：可增删 pill -->
  <button class="filter-pill" v-for="f in activeFilters" :key="f.key">
    {{ f.label }} <i class="icon-close" @click="removeFilter(f)"></i>
  </button>

  <!-- 高级筛选收进 popover -->
  <el-popover><button class="btn-ghost">筛选…</button>…</el-popover>

  <el-button type="primary" @click="handleSearch">查询</el-button>
</div>
```

```css
.filter-bar {
  display: flex; align-items: center; gap: var(--sp-3);
  flex-wrap: wrap;                        /* 条件多时优雅换行，不横向滚动 */
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface);
  border-radius: var(--r-lg);
  box-shadow: var(--elev-1);
}
.search-field {
  display: flex; align-items: center; gap: var(--sp-2);
  min-width: 240px; height: 36px; padding: 0 var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--r-sm);
  box-shadow: 0 0 0 1px var(--border) inset;
  transition: box-shadow var(--dur-1) var(--ease-standard);
}
.search-field:focus-within { box-shadow: 0 0 0 4px var(--accent-soft), 0 0 0 1px var(--accent) inset; }
.filter-pill {
  display: inline-flex; align-items: center; gap: var(--sp-1);
  height: 30px; padding: 0 var(--sp-3);
  border-radius: var(--r-full);
  background: var(--accent-soft); color: var(--accent);
  font-size: 13px; font-weight: 500;
  animation: pill-in var(--dur-2) var(--ease-spring);   /* 增删弹性 */
}
/* 条件区 + 操作区：查询卡只放条件，查询/重置恒右对齐（治"换行参差 / 单条件也两行"） */
.filter-conditions { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; flex: 1; min-width: 0; }
.filter-actions    { display: flex; align-items: center; gap: var(--sp-2); margin-left: auto; }
.filter-field {          /* 非输入类条件控件（日期区间 / 下拉触发）统一宽高基准，换行成列 */
  display: flex; align-items: center; gap: var(--sp-2);
  height: 36px; min-width: 200px; padding: 0 var(--sp-3);
  background: var(--surface-2); border-radius: var(--r-sm);
  box-shadow: 0 0 0 1px var(--border) inset;
}
```

**结构骨架**：查询卡 = `.filter-bar > .filter-conditions（条件们）+ .filter-actions（查询/重置）`。条件控件（`.search-field` / `.org-filter` / `.filter-field` / `el-segmented`）统一 `36px` 高、宽度取 §15.2 基准；`.filter-actions` 靠 `margin-left:auto` 恒居右。条件 ≤4 通常一行放下，换行也因等宽而成列。

- 搜索为主操作时可**即时查询**（防抖 300ms）；保留显式"查询"按钮兜底。
- 弹窗内筛选行用 `.dialog-toolbar`，规则相同。
- 若某页条件极简，可退化为仅"搜索框 + 查询"，仍用 `.filter-bar` 容器。

> **"全部"是清空态，不是一个类选项（通则，承重 —— 它管的是计数判据能不能被满足）**
>
> 任一枚举型筛选条件（`el-select` / `el-segmented` / filter-pill 组）里的「全部」「全部 X」「不限」一类取值，**语义是"不按该条件过滤"，即该条件的清空态 / 全量态**，与"该条件留空"同义。本规范 §12.1 的「全部组织」已是这个用法（**未选 = 占位「全部组织」，清除即恢复**）。
>
> - **它不属于该条件的类枚举** ⇒ 当某条件的取值域由别处的定义处给出（如一份正面清单）时，**那份枚举不含「全部」**，也不因加了「全部」而变长。
> - **计数判据一律数"类选项"，不数"控件节点"。** 两个数不同，且**不得互相代入**：若「全部」渲染为下拉 / 分段控件里的一项，则 **节点数 = 类选项数 + 1**，**这个 `+1` 必须在该页的设计落字里写出来**，不留给实现去猜。
> - **判据写错的两种后果都是实的**：把「全部」数进"类选项数"⇒ 判据按字面**判红一个正确实现**；为满足判据而去掉「全部」⇒ **筛选选了就清不回全量**，而多数列表页同时要求"进页即全量"。**两头咬，没有一个实现同时满足。**
> - **同一产品内不得各做一种**：每个筛选面都按本条声明「全部」的身份与那个 `+1`，**不逐面另立口径**。

### 12.1 组织作查询条件 · 树形下拉选择器（`.org-filter`）

组织是层级数据，作查询条件时**不使用普通单选下拉，也不使用级联 `el-cascader`**（深度不固定、深层难定位），统一使用**树形下拉 `el-tree-select`**。

**形态**：置于 `.filter-bar`，宽度 `200–240px`，圆角 `--r-sm`，焦点绽放遵循 §12。

**收起态**
- 显示当前选中组织名；未选 = 占位「全部组织」（`--text-tertiary`），语义为不按组织过滤。
- 右侧 chevron；`clearable`，hover 显 ✕，清除即恢复「全部组织」。

**展开态**（popover：`--surface` + `--elev-2` + `--r-lg`）
- 顶部搜索框：实时过滤 + 自动展开命中分支 + `<mark>` 高亮（同 §10.2）。
- 下方可滚动树：节点样式（缩进 18px/级、chevron 旋转、hover 微染、选中 `--accent-soft` + 左竖条）**复用 §10.2**。
- 点节点即回填并收起。

**选择模式：单选**
- 一次筛选一个组织。多组织对比属另一场景，本规范默认不启用多选；确需时再单独定义（checkbox 树 + 多 pill）。

**含下级组织开关（关键）**
- popover 内提供「含下级」开关，语义 = 统计**是否包含子组织数据**（决定查询是 `= org` 还是 `in 子树`）。
- **默认开启（含本级 + 全部下级）**，契合统计"看一个层级整体"的直觉；用户可关闭为仅本级。

**回填呈现**
- 选中后在 `.filter-bar` 以 filter-pill 呈现（§12）：`组织：研发中心 · 含下级 ✕`；关闭含下级时省略"· 含下级"。
- ✕ 移除该条件 = 恢复「全部组织」。

**落地提示**
- 用 Element Plus `el-tree-select`（`filterable` / `filter-node-method` 搜索、`lazy` 懒加载）承载；"含下级"以其外的独立开关状态提交给后端，不混入选中值。

### 12.2 数据操作区（内嵌数据卡片头 `.data-card-header`）

数据操作（新增/批量编辑/批量删除/导入/导出）**内嵌于数据卡片头 §11.2.1**，不独立成卡。卡片头一行内：数据名标题（左）→ `.action-primary`（左组，紧随标题）→ `.action-io`（右组，`margin-left:auto` 靠右）。**按需出现**：无 CRUD/导入导出能力的纯只读页不渲染操作组。

```html
<div class="data-card">
  <div class="data-card-header">
    <div class="dch-title">用户列表<span class="dch-count">共 128 条</span></div>
    <div class="action-primary">                   <!-- 左：数据操作组 -->
      <el-button type="primary" @click="openCreate">＋ 新增</el-button>
      <el-button :disabled="!selected.length" @click="openBatchEdit">批量编辑</el-button>
      <el-button type="danger" :disabled="!selected.length" @click="batchDelete">批量删除</el-button>
      <span v-if="selected.length" class="action-selected">已选 {{ selected.length }} 项</span>
    </div>
    <div class="action-io">                         <!-- 右：导入导出组（靠右） -->
      <el-button v-if="canImport" @click="openImport">导入</el-button>
      <el-button v-if="canExport" @click="exportData">导出</el-button>
    </div>
  </div>
  <el-table … />
</div>
```
```css
.action-primary, .action-io { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.action-io { margin-left: auto; }        /* 导入/导出靠右 */
.action-selected {                          /* 已选计数：accent-soft 胶囊 */
  display: inline-flex; align-items: center; height: 30px; padding: 0 var(--sp-3); margin-left: var(--sp-1);
  border-radius: var(--r-full); background: var(--accent-soft); color: var(--accent);
  font-size: 13px; font-weight: 600; animation: pill-in var(--dur-2) var(--ease-spring);
}
.action-selected b { margin: 0 3px; font-variant-numeric: tabular-nums; }
/* 批量按钮未选时禁用态 */
.btn:disabled { opacity: .45; cursor: not-allowed; box-shadow: none; }
.btn:disabled:hover { transform: none; }
```
```css
/* 行多选复选框（表格 selection 列，与操作卡联动；可用于 EP selection 皮肤化或自定义） */
.row-check { position: relative; display: inline-grid; place-items: center; width: 18px; height: 18px; cursor: pointer; }
.row-check input { position: absolute; inset: 0; opacity: 0; margin: 0; cursor: pointer; }
.row-check span {
  width: 18px; height: 18px; border-radius: 6px; background: var(--surface);
  box-shadow: 0 0 0 1px var(--border-strong) inset; display: grid; place-items: center;
  transition: background var(--dur-1), box-shadow var(--dur-1);
}
.row-check span::after {                    /* 勾（全选/行选） */
  content: ""; width: 11px; height: 11px; opacity: 0; transform: scale(.5);
  transition: all var(--dur-1) var(--ease-spring);
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='3.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12l5 5L20 6'/%3E%3C/svg%3E") center/contain no-repeat;
}
.row-check input:checked + span, .row-check input:indeterminate + span {
  background: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset;
}
.row-check input:checked + span::after { opacity: 1; transform: scale(1); }
.row-check input:indeterminate + span::after {   /* 半选：横杠 */
  opacity: 1; transform: none; width: 10px; height: 2px; border-radius: 1px; background: #fff;
}
tbody tr.is-selected { background: var(--accent-soft); }   /* 选中行高亮，hover 保持 */
tbody tr.is-selected:hover { background: var(--accent-soft); }
```

规则：
- **左组 `.action-primary`（数据操作）**：`新增`(primary) / `批量编辑` / `批量删除`(danger)。批量二者默认 `disabled`，**行多选选中后启用**，旁附「已选 N 项」。
- **右组 `.action-io`（导入导出）**：`导入`/`导出`，**按各页实际能力条件渲染**（无该能力则不出现）；不设死入口。
- **批量操作**：数据表首列加 `el-table-column type="selection"`（行多选，样式 `.row-check`）；**表头全选支持半选**（部分选中呈 indeterminate 横杠）；**选中行 `--accent-soft` 高亮**；选中即**联动操作卡**批量按钮由 `disabled` 转启用 + 显「已选 N 项」胶囊。批量删除二次确认**展示范围**（"确定删除选中的 N 项吗？…不可恢复"，§15.3）；批量编辑弹窗改**共同属性**（§16）；完成 `notify.success` + 刷新 + 清选。
- **与行内操作并存**：表格行内操作列（§13.3 单行编辑/删除/查看）**保留**，顶部批量是**增强非替代**。
- **精简操作卡**：只读但有导出的页（如统计看板）只渲染**右侧导出 io 组、无左侧数据操作组**；导出恒居操作卡，不并入查询卡（保 §12 查询卡纯条件）。

---

## 13. 表格规范 —— 灵动数据表

### 13.1 节奏与基础样式

更舒展的节奏，去除 zebra，靠发丝分隔线与悬停染色区分行。

| 属性 | 值 |
|---|---|
| 表头行高 | `48px` |
| 表头字号 | Subhead（13px / 600） |
| 表头背景 | `--surface-2`，sticky 时叠加 `--material-blur` |
| 表头文字 | `--text-secondary` |
| 数据行高 | `56px` |
| 数据行文字 | Callout（14px），色 `--text` |
| 行分隔线 | `--separator`（发丝） |
| 悬停行背景 | `--gray-100`（暗色 `--surface-2`），`--dur-1` 过渡 |
| 选中行背景 | `--accent-soft` |
| 数值列 | `font-variant-numeric: tabular-nums` |

- **表头固定（必须）**：滚动数据时表头**始终可见**，不随表体滚走。两种实现按场景择一：
  - *表体内部滚动*（推荐）：给 `el-table` 设 `height` / `max-height`，表体内滚、表头常驻；分页留在 `.data-card` 底部不参与滚动。
  - *页面级滚动*：表头 `position: sticky; top: {顶栏高度}`，吸顶时叠加 `--material-blur` 磨砂 + 底部 `--separator`。
  - 固定表头背景用 `--surface-2`，`z-index` 高于行内容；与横向固定列（`fixed="right"`）叠加时保证四角层级正确。
- **排序**：可排序表头 hover 显示排序 caret，切换时 caret 带 `--dur-1` 旋转 / 淡入。
- **进场**：数据载入按 §6.3 逐行 stagger 浮现。

### 13.2 加载态 —— 骨架屏优先

```html
<div v-if="loading" class="skeleton-rows">
  <div class="skeleton-row" v-for="n in 8" :key="n"></div>
</div>
```

- 首次加载用**骨架行**（含 `--dur-4` shimmer 微光扫过），替代整块遮罩 spinner，减少"闪白"。
- 翻页 / 刷新等已有内容的场景，可用轻量 `v-loading` 半透明遮罩。

### 13.3 操作列（固定右侧 · 不换行 · 超三项收纳）

统一 `size="small" link` 文字按钮，`fixed="right"`，单元格 `white-space: nowrap`：

```html
<el-table-column label="操作" fixed="right" :width="opsWidth">
  <template #default="{ row }">
    <!-- 前 3 个高频操作直接平铺 -->
    <el-button size="small" type="primary" link @click="edit(row)">编辑</el-button>
    <el-button size="small" type="primary" link @click="view(row)">查看</el-button>
    <el-button size="small" type="danger"  link @click="del(row)">删除</el-button>
    <!-- 第 4 个及以后收进「更多」，悬停展开 -->
    <el-popover v-if="row.moreOps?.length" trigger="hover" placement="bottom-end" :width="140">
      <template #reference>
        <el-button size="small" link class="ops-more">⋯</el-button>
      </template>
      <div class="ops-menu">
        <button class="ops-menu-item" @click="reset(row)">重置密钥</button>
        <button class="ops-menu-item danger" @click="disable(row)">停用</button>
      </div>
    </el-popover>
  </template>
</el-table-column>
```

**核心规则**
- **不换行**：单元格 `white-space: nowrap`（全局已对 `fixed="right"` 列设置），多个 link 按钮并排绝不折行。
- **至少完整展示 3 个操作项**：操作项 ≤3 时全部平铺。
- **超过 3 个 → 收纳**：仅平铺前 3 个高频操作，其余收进末尾「⋯」（更多）按钮；**鼠标悬停 `⋯`** 弹出 popover 菜单显示剩余操作（`trigger="hover"`，`placement="bottom-end"`），不占用行内横向空间。
- 更多菜单项遵语义色（危险操作 `danger`）；菜单项 hover 背景 `--surface-2`，圆角 `--r-xs`。
- **「⋯」菜单不被裁切**：在表格最后几行或靠近视口底部时，菜单必须完整显示，不能被表格、数据卡片（`.data-card`）或弹窗的边界裁切。实现方式可以是空间不足时自动向上展开，或者把菜单挂到页面最外层（如 `teleported`）。不得靠加大表格高度或给容器加留白来回避。
- **「⋯」菜单可用键盘操作**：键盘聚焦到 `⋯` 时同样能展开菜单，菜单项可以用 Tab 或方向键到达、按 Enter 触发，并有可见的聚焦环（§21）。鼠标悬停不是唯一的打开方式。
- 固定列左缘用 `--separator` + 材质渐隐，避免生硬切边；hover 行时按钮从 `--text-secondary` 提亮到全色。
- 禁止在操作列使用带背景 / 边框的普通按钮（防折行）。

**更多菜单样式（`<style scoped>`）**
```css
.ops-more { color: var(--text-secondary); font-weight: 700; letter-spacing: 1px; }
.ops-menu { display: flex; flex-direction: column; gap: 2px; }
.ops-menu-item {
  border: 0; background: none; text-align: left; cursor: pointer;
  padding: 7px 10px; border-radius: var(--r-xs); font-size: 13px; color: var(--text);
  transition: background var(--dur-1) var(--ease-standard);
}
.ops-menu-item:hover { background: var(--surface-2); }
.ops-menu-item.danger { color: var(--danger); }
```

**操作列列宽参考**

| 可见操作项 | 推荐列宽 |
|---|---|
| 1 | 88px |
| 2 | 130–170px |
| 3 | 170–210px |
| 3 + 更多（⋯） | 190–220px |

> 操作项 >3 时，列宽始终按"3 项 + ⋯"预留，**不因隐藏项增多而变宽**，保证各行操作列对齐。

### 13.4 长文本列

```html
<el-table-column prop="base_url" label="地址" min-width="240" show-overflow-tooltip />
```

---

## 14. 按钮规范

### 14.1 全局样式

```css
.btn {
  min-height: 36px;
  border-radius: var(--r-sm);            /* 10px */
  font-weight: 600; white-space: nowrap;
  transition: transform var(--dur-1) var(--ease-standard),
              box-shadow var(--dur-1) var(--ease-standard),
              background var(--dur-1);
}
.btn:hover  { transform: translateY(-1px); }
.btn:active { transform: scale(.97); }
.btn:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px;
  box-shadow: 0 0 0 4px var(--accent-soft);
}
```

### 14.2 类型

| 场景 | 类型 | 说明 |
|---|---|---|
| 页面主操作（查询、保存） | `type="primary"` 实心 | 填充 `--accent`，文字 `--accent-contrast` |
| 次要操作（同步、新增、重置） | 默认（无 type） | `--surface`，`1px --border` 或 `--gray-100` 底 |
| 幽灵 / 弱操作 | `.btn-ghost` / `link` | 无底，文字 `--text-secondary`，hover 显 `--gray-100` 底 |
| 危险操作（删除、批量删除） | `type="danger"` | `--danger` |
| 表格操作列 | `size="small" link` | 见 §13.3 |

### 14.3 禁止事项

- 表格操作列禁用普通（带背景 / 边框）按钮，防折行。
- 查询表单内非查询按钮加 `native-type="button"`，防 Enter 误触发。

---

## 15. 表单输入规范

### 15.1 输入框 / 下拉

用内阴影描边，聚焦时**绽放**聚焦环。

```css
.field {
  min-height: 36px;
  border-radius: var(--r-sm);
  background: var(--surface);
  box-shadow: 0 0 0 1px var(--border) inset;           /* 默认 */
  transition: box-shadow var(--dur-1) var(--ease-standard);
}
.field:hover { box-shadow: 0 0 0 1px var(--border-strong) inset; }
.field:focus-within {
  box-shadow: 0 0 0 1px var(--accent) inset, 0 0 0 4px var(--accent-soft);
}
```

**下拉搜索（强制）**：凡**数据来自后端数据库查询**的 `el-select`（如组织、用户、角色等动态列表），**必须开启 `filterable`**，让用户输入关键词过滤，禁止只靠滚动长列表选取。

```html
<!-- 后端来源下拉：必带 filterable -->
<el-select v-model="ownerId" filterable clearable placeholder="全部负责人">
  <el-option v-for="it in ownerOptions" :key="it.id" :label="it.name" :value="it.id" />
</el-select>
```

- 仅前端静态枚举（如"状态：正常/停用"等固定 3–6 项）**可不加** `filterable`，避免多余搜索框。
- 选项量大（>50）或需服务端搜索时，配 `remote` + `remote-method` 走接口过滤；数据总量小则本地 `filterable` 即可。
- 组织类查询条件走 §12.1 树形下拉（内置搜索框），不用普通 `el-select`。

### 15.2 查询条件宽度参考

| 控件 | 推荐宽度 |
|---|---|
| 关键词搜索框 | 240–280px |
| 单选下拉（状态、类型） | 160–200px |
| 日期区间 | Element Plus 默认 |

### 15.3 校验与反馈

- 字段校验错误：字段下方 `--danger` 红字，`blur` 实时触发 + 提交统一校验。
- 接口业务错误：能归到表单字段的，显示在该字段下方；归不到字段的，弹窗内按 §16.4 显示在弹窗里，页面上走 `notify.error`（§19.4）＋ 具体信息。
- 破坏性操作二次确认，文案："确定要{操作}吗？{后果说明}"。

### 15.4 一次性凭据的展示（强制 · **「展示一次后不可再取」须在界面上成立**）

**适用条件**：某值由系统生成、**只在生成的那一次响应里返回**、此后任何接口都不再返回它。

| 项 | 规则 |
|---|---|
| 承载形态 | **只用弹窗**（§16），**不得**渲染在表格列、详情页字段、列表行展开区或任何可被再次打开的只读面里 |
| 标题与定性 | 标题须写明这是一次性值；正文首行即**后果说明**：「**此{凭据名}只显示这一次，关闭后无法再次查看**」—— 用 §19.1 的 `warning` 语义色，**不用 info**（info 读作「顺便一提」） |
| 值的呈现 | 等宽字体（§3.3 数字排版同一口径），字号不小于 Body；**可选中可复制**，旁置「复制」按钮 + 复制成功 toast（§19.2） |
| 关闭的闸门 | **不设置自动关闭、不设置倒计时自动消失**；关闭须是用户的显式动作。若该值尚未被复制过，关闭前**再确认一次**（§15.3 模板） |
| 关闭之后 | 该值在**任何界面与任何接口响应中均不可再取**；界面须给出**下一步的可行做法**（如「忘了就重新签发一次」），**不留一条读不到结果的路** |
| 禁止事项 | ❌ 不写进 URL / query / localStorage / sessionStorage；❌ 不进任何日志或埋点；❌ 不随列表接口回显；❌ 不提供「再看一次」入口（**该入口不存在，不是置灰**） |
| 可验收形态 | ① 弹窗关闭后刷新页面与重新进入该对象 ⇒ 该值**不出现**；② 抓取该对象的全部读接口响应体 ⇒ **不含**该值的任何片段；③ DOM 中不存在「再次查看」节点 |

本产品哪些值属于一次性凭据，写在本工程实例 §15.4。

---

## 16. 弹窗规范

```css
.el-dialog {
  border-radius: var(--r-xl);            /* 20px */
  overflow: hidden;
  box-shadow: var(--elev-3);
  background: var(--surface);
  animation: dialog-in var(--dur-3) var(--ease-spring);   /* scale(.96)→1 + fade */
}
.el-overlay { backdrop-filter: blur(4px); background: rgba(0,0,0,.28); }
```

| 区域 | Padding | 说明 |
|---|---|---|
| 标题区 `__header` | `18px 24px 14px` | sticky，底部 `--separator` |
| 内容区 `__body` | `20px 24px` | 超高时内滚，页眉页脚吸附 |
| 按钮区 `__footer` | `14px 24px 18px` | sticky，顶部 `--separator` |

#### 16.1 尺寸约束（min / max · 强制）

弹窗**不得随内容无界撑大或缩小**，须设最小 / 最大约束：

| 维度 | 约束 | 说明 |
|---|---|---|
| 宽度基准 | `460px`（简单表单）/ `560–620px`（多字段）/ `min(1080px, 92vw)`（含表格） | 按内容档位选宽 |
| 最小宽度 | `min-width: 420px`（**仅 ≥768px 视口生效**） | 窄屏档（§4.1，`< 768px`）**必须解除该下限**，改 `width: 92vw`——手机视口 375–430px 时 `92vw` 恒小于 420px，若不解除，min-width 会在级联中胜出并撑破视口 |
| 最大宽度 | `max-width: 92vw` | 不贴屏、不溢出视口 |
| 最大高度 | `max-height: 86vh`，`__body` 内滚 | 页眉页脚吸附，内容区滚动；不顶满全屏 |
| 最小高度 | 由内容自然撑开，不强设 | —— |

```css
.el-dialog {
  min-width: 420px;
  max-width: 92vw;
}
.el-dialog__body {
  max-height: calc(86vh - 120px);   /* 减头/脚高度 */
  overflow: auto;
}
/* 窄屏解除最小宽度下限（必做，否则撑破视口） */
@media (width < 768px) {
  .el-dialog { min-width: 0; width: 92vw; }
}
```

> 含表格的大弹窗用 `width: min(1080px, 92vw)`；上述 min/max 兜底防溢出。

#### 16.2 弹窗内查询卡（遵 §12 布局，重置必带）

弹窗内若有查询条件，**遵守 §12 筛选栏三区布局**：查询条件左排、`.filter-actions` 靠右（`margin-left:auto`），**「查询」「重置」按钮右对齐，重置为必带项**（与列表页一致，不因在弹窗内而省略）。

```html
<form class="filter-bar" @submit.prevent="onSearch">
  <div class="filter-conditions"><!-- 查询条件 --></div>
  <div class="filter-actions">
    <el-button type="primary" native-type="submit">查询</el-button>
    <el-button native-type="button" @click="onReset">重置</el-button>
  </div>
</form>
```

#### 16.3 弹窗内数据卡（遵 §11.2，含卡片头）

**弹窗内的数据表同样封装为 `.data-card` 并遵守 §11.2**（含 §11.2.1 卡片头、内部分页规范）。

**固定表头（强制）**：弹窗内数据表格**必须固定表头**——`el-table` 设 `max-height`（推荐 `360`，即 `max-height="360"`）或 `height`，使表头吸顶、数据行区域独立滚动，避免整表随弹窗 body 滚动导致表头滚离视口。

#### 16.4 弹窗内的提交失败（表单弹窗与确认弹窗同用）

**每一次失败的提交都必须在弹窗内留下可见的原因，不得「点了没反应」。** 失败按能否归到本弹窗**渲染出来的**字段分两路：

| 失败 | 显示在哪 | 形态 |
|---|---|---|
| 能归到本弹窗渲染的某个字段 | 该字段下方 | §15.3 字段校验错误 |
| 归不到（系统繁忙、网络中断、安全校验失效、对象已不存在等，以及字段不在本弹窗内的错误） | **弹窗内容区底部、紧贴按钮区之上**的一条弹窗级错误 | `--danger-soft` 底 ＋ `--danger-ink` 字，`--r-md` 圆角，13px；`role="alert"` |

```html
<p v-if="formError" class="dialog-error" role="alert">{具体原因}</p>
```

- **不用 Toast、不用页顶提示**：Toast 数秒即消失且不在用户正看着的表单里；页顶提示被遮罩盖住。错误要留在弹窗里，直到下一次提交或关闭弹窗。
- **弹窗不关，填写的内容全部保留**；提交按钮退出 loading、恢复可点，用户可直接重试或取消。下一次提交开始时清掉上一次的弹窗级错误；关闭弹窗后再打开，不带旧错误。
- **文案给具体原因**（§19.2）。**结果不确定时不得断言「未完成」**：网络中断、超时等拿不到响应的情况，服务端可能已经执行 —— 文案须说明结果未确认、该去哪里核对，不能只写「请稍后重试」（否则重试会撞上「已存在」一类的拒绝，用户无从理解）。
- **登录失效（401）不在此列**，走全局的登录失效处理。
- **唯一例外：提交即移交全局临界流程的确认弹窗。** 同时满足三条才算：① 弹窗**没有用户填写的内容**（纯确认）；② 提交后由页面之外的全局流程接管，弹窗所在页面会被隔离或卸载，弹窗无法留在原处等结果；③ 该流程有自己的成功出口（如凭据弹窗或跳转）。此时确认弹窗可在提交时先关，但**失败原因仍须可见且具体**：明确被拒 ⇒ 回到原页面后在页顶提示（`role="alert"`，不用 Toast，不得为空文案），用户可重新发起；结果不确定 ⇒ 按该流程的出口给「结果未确认」及去向。**不满足三条的，一律按本节前文处理。**

---

## 17. 分页规范

```html
<el-pagination
  layout="total, sizes, prev, pager, next"
  :page-sizes="[10, 20, 50, 100]" … />
```

- 在 `.data-card` 内：`<div class="pagination">` 包裹，卡片底部，背景 `--surface-2`，顶部 `--separator`。
- 独立使用：直接 `class="pagination"`，渲染为独立抬起卡片。
- 当前页码使用 `--accent` 填充 pill；页码切换 hover / active 按 §6.2 反馈。

---

## 18. 空状态与加载

### 18.1 空状态

```html
<!-- status：'loading' | 'error' | 'loaded'，三态互斥（§18.3） -->
<p v-if="status === 'loaded' && rows.length === 0" class="empty-state">暂无{实体名称}数据</p>
```

- **只在「本次查询成功且 0 条」时出现。** 「暂无 X 数据」是对数据的断言；请求失败时并不知道有没有数据，此时显示空状态就是给用户一个假结论 —— 失败走 §18.3。

```css
.empty-state {
  padding: 48px 20px; text-align: center;
  color: var(--text-tertiary); font-size: 15px;
}
```

- 可在文案上方置一枚柔和的插画 / 单色图标（`--gray-300`），带 `--ease-out` 淡入。
- 位置：`el-table` 之后、`.pagination` 之前（`.data-card` 内）。

### 18.2 加载

- 列表首次加载：骨架屏（§13.2）。
- 局部刷新：轻量 `v-loading` 遮罩。
- 按钮提交中：禁用 + 内联 loading 图标。

### 18.3 加载失败

列表 / 详情的数据区**三态互斥**：**加载中**（§18.2）· **加载失败**（本节）· **已加载**（有数据 ⇒ 渲染数据；0 条 ⇒ 空状态 §18.1）。任一时刻只呈现其中一态。

```html
<div v-if="status === 'error'" class="load-error" role="alert">
  <span class="load-error-icon" aria-hidden="true"><!-- error 语义图标 --></span>
  <p>{具体原因}</p>
  <button type="button" class="btn btn-default" @click="reload">重新加载</button>
</div>
```

- **位置**：占据表体 / 空状态所在的内容区（`.data-card` 内，表头之下、分页之上）。**同一次失败只呈现一次**：不在页顶横幅或 Toast 里再报一遍；页顶提示与 Toast 留给用户动作（保存、删除、停用等）的失败。
- **内容**：`error` 语义图标（`--danger` / `--danger-soft` 圆底，同 §19.1）＋ **具体原因**（§15.3 / §19.2：说出没取到的是什么、能做什么，不写「加载失败」了事；无业务原因的网络中断写「请求未完成，请稍后重试」一类可行动文案）＋「重新加载」按钮。文案色 `--text-secondary`，居中，内边距同空状态；不新造令牌。
- **不留旧数据**：失败时不保留上一次查询的行 —— 旧行配新的筛选条件，会被读成新查询的结果。卡片头计数（§11.2.1 `.dch-count`）与分页里的总数**都不显示数字**（不得显示「共 0 条」，也不得沿用上一次的数），分页不可操作。
- **重新加载**：按**当前已生效的**筛选与页码重发；请求期间按 §18.2 显示加载态；成功后进入「已加载」，再次失败仍是本态。
- **登录失效不进本态**：会话失效（401）走全局的登录失效处理（跳登录页并提示），数据区不显示失败态。
- **弹窗内的数据区同样适用**（如确认前须先取回的统计、关联条目）：加载失败时**弹窗不关**，失败态占该数据区（具体原因 ＋「重新加载」，`role="alert"`），不在页顶另报；**依赖这些数据的提交按钮保持禁用**，直到重新加载成功；「取消」始终可用。这是读取失败，与 §16.4 的提交失败分开呈现，不混成一条。

---

## 19. 消息提示（Toast / 通知）

系统的瞬时反馈分四类，先明确**用哪一个**：

| 场景 | 组件 | 说明 |
|---|---|---|
| 用户操作的即时结果（保存成功、校验失败…） | **轻量 Toast** `ElMessage` | 顶部居中、单行、自动消失（§19.2） |
| 异步 / 系统事件（导出完成、后台任务、他人操作） | **通知卡片** `ElNotification` | 右上角、带标题+正文+可选操作（§19.3） |
| 破坏性操作前确认 | `ElMessageBox.confirm` | 见 §15.3，文案"确定要{操作}吗？{后果}" |
| 持久化通知列表 | 顶栏铃铛消息中心 | **所有有可能收到通知的身份**（可见性判据见 §8，**不按身份写死**）；形态见 §23.4 |

### 19.1 类型与语义

四种语义，图标 + 语义色统一，**颜色不单独承载信息**（必带图标）：

| 类型 | 图标色 / 软底 | 用途 |
|---|---|---|
| success | `--success` / `--success-soft` | 操作成功 |
| info | `--accent` / `--accent-soft` | 中性提示 |
| warning | `--warning` / `--warning-soft` | 需注意但未失败 |
| error | `--danger` / `--danger-soft` | 操作失败 / 异常 |

### 19.2 轻量 Toast（`ElMessage`）

- **位置**：顶部居中，距顶约 `24px`；多条纵向堆叠，间距 `12px`，增减时 spring reflow。
- **外观**：`--surface` + `--elev-2`，圆角 `--r-full`（胶囊）或 `--r-md`；左侧语义色图标（`-soft` 圆底）+ 单行文案（超长省略）；error 带关闭按钮。
- **动效**：进场 slide-down + fade（`--dur-3 --ease-spring`）；退场 fade + 上移收拢（`--dur-2 --ease-standard`）。
- **时长**：success / info `3s`；warning `4s`；**error 约 `4.5s` 且必带关闭按钮**（`showClose`，给足阅读时间）。
- **文案**：一句话、动宾结构、句末不加句号。成功如"已保存"；失败给**具体原因**，不要只写"操作失败"。

### 19.3 通知卡片（`ElNotification`）

- **位置**：右上角，宽约 `360px`，`--surface` + `--elev-3` + `--r-lg`。
- **结构**：语义色图标 + 标题（Headline 17）+ 正文（Footnote 13）+ 可选操作链接 + 关闭。
- **动效**：slide-in-right + spring 进场；多条堆叠 reflow。
- **时长**：默认停留 `4.5s`；**含操作按钮或 error 时不自动消失**，由用户手动关闭。

### 19.4 通用规则

- **去重**：相同内容短时间内不重复弹出，防刷屏。
- **数量上限**：同屏 Toast ≤ `3` 条，超出替换最旧。
- **无障碍**：容器 `role="alert"`、`aria-live="polite"`（error 用 `assertive`）；遵守 `prefers-reduced-motion`（§6.4，退化为直接显隐、无位移）。
- **全局封装**：统一 `notify.success / info / warn / error(msg)` 与 `notify.push({ title, body, action })`，各处调用封装，**禁止散调** `ElMessage`/`ElNotification`，以保证样式与文案一致。

---

## 20. 数据展示格式化

| 数据类型 | 显示格式 | 实现 |
|---|---|---|
| 大数计数 | 紧凑单位 K/M/B，如 `12.3K` | `formatCompactNumber(value)` |
| 金额 | 货币符号前缀 + 紧凑单位，如 `$1.23K`（币种见本工程实例 §20） | `formatCurrency(value)` |
| 日期时间 | `yyyy-MM-dd HH:mm:ss` | `formatDateTime(value)` |
| 纯日期 | `yyyy-MM-dd` | — |
| 平均耗时 | 整数毫秒 + `ms`，如 `234 ms` | `Math.round(value) + ' ms'` |
| 空值 | `-` | — |

- 格式化函数在各前端工程的工具文件里实现，**落点由该工程的 spec 定**，本规范不指定路径；同一工程内须集中一处，不在组件里各写一份。
- 所有数值以 `tabular-nums` 渲染（§3.3）。
- 本产品各业务指标归哪一类、用哪种格式，写在本工程实例 §20。

### 20.1 🔴 展示层红线：**凡是能直出事实的地方，就不要派生**

> **通则**：**派生出的每个词，都可能带上「派生那一刻」的语境。** 若后端已记录了事实本身，**直接显示那个事实**；不要从更底层的参数、开关或状态**推导**一个展示用的说法。

**判断标准（三问，任一为「是」即必须直出事实）**：

1. 派生出的文案里有没有**相对当下**的词？（`本月` / `今天` / `昨天` / `当前` / `最近`…）
2. 这条记录会不会在**产生它的那一刻之外**被读到？（审计、历史、日志、报表 —— **它们的定义就是「事后才读」**）
3. 后端有没有**已经记下那个事实**的字段？

**实例（某产品的手动聚合审计记录）**：

| | 派生（❌ 已作废） | 直出事实（✅ 现行） |
|---|---|---|
| 做法 | 由 `include_today` 布尔 + **阅读时**的「本月」推出「本月截至今天 / 昨天 / —」 | 直出后端记下的 `source_end_date`（如 `2026-07-17`） |
| 跨月阅读 | 🔴 **上月发起、当时真实生效过的参数，今天被抹成 `—`** | ✅ 恒显真实日期 |
| `—` 的含义 | 🔴「区间不含本月」——**会随时间变成假话** | ✅「该月尚未执行到」——**恒真** |
| 何时暴露 | 🔴 **下月 1 号起集体现形；今天全部测试都是绿的** | — |

> **为什么这条值得成为红线**：该缺陷**不是「现在错了」，是「时间一走就错」** —— 它会**通过全部测试**，然后在某个月初集体爆发。**单元测试、QA 回归、代码复跑都抓不到它**，因为它们全都跑在「今天」。

**它与下面两条边界同族（一并记住，都是「展示层混入了不属于它的东西」）**：

| 边界 | 防的是 |
|---|---|
| **别把后端参数名穿透到界面**（`include_today` ↛ 控件名「含当天」） | **接口语义**混进展示层 |
| **别把阅读时的语境烘焙进历史记录**（本条） | **时间语境**混进展示层 |
| **展示层的单位/文案不许泄漏进存储**（`万` ↛ token；降级文案 ↛ 后端映射） | 展示层**溢出**到存储层 |

### 20.2 🔴 术语红线：**一个词在产品里只能有一个外延**

若同一个词在两条规则下指**不同的集合**，**界面上一律不得使用该词**，改用**具体的、无歧义的表述**（如具体月份区间 `2026-01 ~ 2026-05：…`）。

**实例（某产品的月度统计页）**：「历史月」在一条规则（「是否含当天」的作用面）下 = **非当前月（含上月）**；在另一条规则（「快照即权威」的作用面）下 = **上上月及更早（不含上月）**。⇒ 同一屏用同一个词表达两个月份集合**必然误导** ⇒ 该词已被**全页禁用**，改回显具体月份区间。

> **给设计者的提醒**：这类冲突**极难自查** —— 它的三次出现是「跨文档 → 同文档隔 40 行 → **同一张表挨着的两行**」，**距离一次比一次近，三次都是被别人撞出来的**。⇒ **写界面文案时，凡引用上游的术语，先确认它在上游只有一个定义。**

---

## 21. 无障碍与降级（必做）

- **对比度**：正文文字与背景对比 ≥ 4.5:1（AA）；大字号 ≥ 3:1。暗色模式单独校验。**不设宽容带**——落在阈值 ±1% 内视同不过，因为过线与否取决于舍入而不取决于设计。执行方式见 §2.7：按承载矩阵逐格机械核算，不靠目视，也不靠巡检屏幕上碰巧出现的节点。
- **聚焦可见**：所有可交互元素在键盘焦点（`:focus-visible`）下，必须呈现 `2px solid var(--accent)` 实线轮廓，外偏移 `2px`；可同时保留 `0 0 0 4px var(--accent-soft)` 绽放柔光。**柔光、选中态、悬停态均不能单独充当聚焦指示**。亮暗主题分别核轮廓与其紧邻外侧背景的对比度 ≥ 3:1（同样不设 ±1% 宽容带），且轮廓完整可见、不被容器裁切；填充控件须保留偏移间隙，使轮廓与控件自身填充分离。
  - 复合输入（含日期范围）、分段控件、日期面板单元格及第三方组件一并适用，不保留浏览器默认描边色。隐藏 input 获得焦点时，轮廓须画在对应的**可见交互块**上（可用 `:has(:focus-visible)` 或等价焦点状态），不得画在透明 / 零尺寸 input 上；分段控件须能定位具体聚焦项，不能只显示整组已选背景。
  - 搜索框与 §15.1 输入示例的 `:focus-within` 内描边和柔光可继续用于输入反馈，键盘操作时须叠加上述实线轮廓；不得因复合控件自带 `outline: none` 而漏掉。键盘可完整操作，Tab / Shift+Tab 逐项核对可见指示，日期单元格另核方向键移动。
- **跳到主要内容**：每页第一个可聚焦元素是「跳到主要内容」链接，指向主内容区；平时视觉隐藏，获得焦点时可见。
- **换页焦点复位**：单页应用内每次路由切换到新页面（登录成功跳转、表单提交后跳转、导航切换、登录失效跳登录页、退出登录等），键盘焦点复位到文档起点，**下一次 Tab 落在「跳到主要内容」**，与整页载入一致；页面滚回顶部；复位不得在非交互元素上显示聚焦环。同一页内的查询、翻页、弹窗开关不是换页，不复位。
- **动效降级**：遵守 `prefers-reduced-motion`（§6.4）。
- **材质降级**：不支持 `backdrop-filter` 时回退不透明 `--surface`（§5.3）。
- **色彩不单独承载信息**：状态除颜色外辅以图标 / 文案。
- **命中区域**：可点元素命中区 ≥ 32×32px。**豁免**：处于正文或表格文本流内的行内文本链接不受此约束——32×32 是为触控目标写的，套到文本流内的行内链接上会与 §13.1 的 48/56 行节奏直接冲突。独立可点控件（按钮、图标钮、复选框、行操作）仍须 ≥ 32×32。

---

## 22. 新增页面检查清单

- [ ] 直接路由页面有 `.page-header h2`（Large Title）；嵌入 `el-tabs` 的组件不加；双模式用 `v-if="!isAdminMode"`
- [ ] 颜色 / 字体 / 间距 / 圆角 / 阴影 / 动效**全部引用令牌**，无硬编码 hex（§2.4 语义层）
- [ ] 亮色 + 暗色两套都视觉正常；对比度以本工程的对比度核算命令（见工程配置「命令」；或 §2.7 认可的等价单测）跑到 0 未达标为准（§2.7），目视不作数
- [ ] 文字与底色的组合落在 §2.7 承载矩阵内；新增组合先进矩阵、跑核算，再进实现
- [ ] 筛选用 `.filter-bar`（可换行），查询 `native-type="submit"`，其余按钮 `native-type="button"`
- [ ] 表格 + 分页封装在 `.data-card`，节奏 48/56，数值列 `tabular-nums`，**表头固定**（§13.1）
- [ ] 每个 `.data-card` **必带卡片头** `.data-card-header`（数据名标题 `.dch-title` + 计数 `.dch-count`）（§11.2.1）
- [ ] 数据操作（新增/批量/导入/导出）**内嵌卡片头**，不独立成卡；批量需行多选 + 半选 + 选中高亮 + 「已选 N 项」（§12.2）
- [ ] 首次加载用骨架屏；局部刷新用轻量 `v-loading`
- [ ] 数据区加载中 / 加载失败 / 已加载三态互斥：空状态只在查询成功且 0 条时出现；失败态在内容区呈现一次，带具体原因与「重新加载」，不留旧行、计数不显示数字（§18.3）
- [ ] 有「跳到主要内容」；单页应用换页后焦点复位到文档起点，下一次 Tab 落在它上面（§21）
- [ ] 操作列 `size="small" link` + `fixed="right"` + 不换行；至少展示 3 项，超 3 项收进「⋯」悬停菜单；「⋯」菜单在末行和视口底部都能完整显示，不被表格、卡片或弹窗裁切，键盘也能展开并选中菜单项（§13.3）
- [ ] 卡片用 `--elev-1` + 连续圆角，去除多余 1px 边框
- [ ] 交互元素具备 hover / press / focus 反馈（§6.2），并尊重 `prefers-reduced-motion`
- [ ] 顶栏 / 侧边栏 / sticky 表头使用磨砂材质，且有 `backdrop-filter` 降级
- [ ] 计数 / 金额 / 日期时间 / 耗时使用规定格式化（§20）；空值 `-`；空状态文案 `暂无{实体}数据`
- [ ] 提示反馈走统一 `notify.*` 封装（§19），error 必带关闭且文案含具体原因
- [ ] 仪表盘用 Bento + 单一 Hero；指标卡渐变图标（delta 可选，缺 delta 不判缺陷）；活力时刻只在焦点，主体保持克制（§0 原则 5 / §11.5 / §11.6）
- [ ] 卡片 / 浮层用玻璃表面（§5.5），Hero 保持实底；`backdrop-filter` 有降级
- [ ] 有状态流转的记录提供看板视图：分列 + 拖拽改状态 + 逾期标 + 详情抽屉（§10.3）
- [ ] 投屏 / 大屏：独立 `.board-shell`（无侧栏顶栏）+ Hero 放大 72px + 数据新鲜度标注 + 受限数据不上屏（隔离由服务端授权强制点保证，不由端点数量保证）；本工程实例声明不提供大屏的，不渲染任何入口（§10.4）
- [ ] 图表定库前用 SVG/CSS 手绘：取色映射 §2.5、正向 `--viz-4` / 告警 `--viz-6`、关键值不只靠颜色、进场遵 `prefers-reduced-motion`（§11.7）
- [ ] 趋势折线带 X/Y 坐标轴 + 数据点 + 末点数值常显（多序列时「序列名 + 值」）；单位三处统一（按 §20）；可键盘 `←/→` 遍历数据点，悬停不是唯一途径；文字与数据点用 HTML 图层、SVG 内只留线性几何（§11.7.1）
- [ ] **响应式只用 §4.1 断点阶**（768 / 1180 / 1440，投屏 ≥2560），同页各区共用同一组断点；不就地新造断点值
- [ ] 数据来自后端查询的下拉带 `filterable`（量大时 `remote`）（§15.1）
- [ ] 弹窗提交失败恒有可见原因：字段错误在字段下方，其余在弹窗内按钮区之上（`role="alert"`）；弹窗不关、内容保留，结果不确定时文案不断言「未完成」（§16.4；提交即移交全局临界流程的纯确认弹窗按该节例外处理）；弹窗内数据加载失败时弹窗不关、失败态占该数据区、依赖它的提交按钮禁用（§18.3）
- [ ] 弹窗设 min/max 约束（`min-width:420px` / `max-width:92vw` / `max-height:86vh` body 内滚）；内嵌查询卡重置必带、数据表套 `.data-card` + 固定表头（§16.1–16.3）
- [ ] 登录 / 全屏页：背景与卡片明确区分色系防撞色；登录方式以本工程实例 §7.1 为准（未启用的方式与可选项入口一律不渲染）；wordmark 纯文字标；窄屏降级为居中表单（§7.1）
- [ ] 组件内部结构色 ≤3 种，且优先取自数据可视化色板
- [ ] 移动端：断点与容器规则遵 §23；表格降级为卡片列表；导航改底部 Tab；弹窗解除 `min-width` 下限（§16.1）
- [ ] 该端不支持的功能，入口在 DOM 中**不渲染**（非置灰），可被"节点不存在"验收（§23.3）
- [ ] 通知中心：铃铛 + 未读角标（≤99 / `99+`）+ Drawer 倒序列表 + 逐条已读 + 全部已读（§23.4）
- [ ] 顶栏右侧**件数逐身份写死**（候选四件：主题切换 / 区域切换入口 / 铃铛 / 用户名下拉；区域切换入口只对能进入者渲染，不置灰；进出共用这一件、两区同位、文案随所在区变、任何区内都不带当前态，另一区侧栏不放返回项，§8 / §9.2）—— **每一种身份下 `.topbar-right` 的直接子元素数（`.topbar-right > *`，不含后代）与铃铛节点数各是一个常数，按 DOM 逐身份核**（**不数「按钮数」** —— 一件可以是一个内含多个 `button` 的容器，如三态主题切换）；**铃铛的可见性按「有可能收到通知的身份」判，不按身份写死**，且须写明失效条件（给他任一类通知即须回来）；下拉项**逐项声明、数量写死**、无业务入口、退出登录恒末位、受限态整条不渲染（§8 / §8.1）
- [ ] 一次性凭据：**只用弹窗**承载 + `warning` 语义 + 等宽可复制 + 不自动关闭 + 关闭后任何界面与接口均不可再取、无「再看一次」入口（§15.4）
- [ ] 富文本编辑器：工具栏能力集按需求逐项声明、不多给；附件区有类型/大小/总量限制与超限提示（§24）
- [ ] **凡后端已记录事实的地方，直出事实、不从参数派生**；派生文案中**不得含「本月/今天/昨天/当前」等相对当下的词** —— 尤其**审计 / 历史 / 日志类记录**（它们的定义就是「事后才读」，派生会随时间变成假话，且**今天测不出来**）（§20.1）
- [ ] **界面文案引用的每个上游术语，在上游只有一个外延** —— 若同一个词在两条规则下指不同集合，**禁用该词**、改用具体无歧义的表述（§20.2）

---

## 23. 移动端与响应式

桌面与移动**不是同一套信息架构的缩放**，而是**同一产品的两种形态**：移动端通常只承载功能子集。设计与实现须显式声明该子集，而非靠"能挤下就都放着"。

### 23.1 断点

| 断点 | 范围 | 形态 |
|---|---|---|
断点取值一律用 §4.1 的断点阶，本节只规定各档的移动端形态：

| 断点 | 范围（§4.1） | 形态 |
|---|---|---|
| `mobile` | 窄屏档 `< 768px` | 单列；底部 Tab 导航；表格降级为卡片列表；弹窗全宽 |
| `tablet` | 平板档 `768–1180px` | 侧边栏可收起为图标条；表格保留但列可收纳 |
| `desktop` | 桌面档及以上 `≥ 1180px` | §7 三层工作台完整形态（`≥ 1440px` 宽桌面 / 投屏限宽见 §4.1） |

- 断点值落主题令牌文件（位置见工程配置「项目规范」）供 JS / CSS 共用，禁止各页自定。
- 布局一律用 flex / grid + 相对单位；**页面主体永不横向滚动**，需要横向滚动的内容（宽表、图表）自带 `overflow-x:auto` 容器。

### 23.2 导航形态

§9 的「侧边栏 240px 常驻展开、不折叠」是**桌面端规则**——移动端视口 375–430px 无法容纳，改为：

| 元素 | 移动端形态 |
|---|---|
| L1 导航 | **底部 Tab Bar**，**3–5 项**（超出即说明移动端子集划得太宽，应收敛而非加 Tab）；高 `56px` + 安全区内边距；磨砂材质（§5.3）；激活态 accent 图标 + 文字 |
| L2 导航 | 进入 Tab 后的页内入口或页签（§10.1） |
| 顶栏 | 高 `48px`；左返回 / 页标题，右铃铛 + 用户；wordmark 让位给页标题 |
| 侧边栏 | **不渲染** |

### 23.3 组件降级

| 组件 | 移动端 |
|---|---|
| 表格（§13） | **降级为卡片列表**：每行一张卡，主字段（标题 / 状态 / 负责人 / 日期）纵向排布；不做横向滚动表格 |
| 筛选栏（§12） | 折叠为「筛选」按钮 → 全屏筛选面板；主搜索框常驻；已选条件仍以 filter-pill 回填 |
| 弹窗（§16） | `width: 92vw`，解除 `min-width`（§16.1）；字段多的表单改**全屏页**而非弹窗 |
| 操作列（§13.3） | 卡片右上「⋯」菜单 |
| Bento / Hero（§11.6） | 降为单列；Hero 跨满整行 |
| 命中区 | ≥ `44×44px`（高于 §21 的桌面基准 32px） |

**功能子集的呈现铁律**：该端不支持的功能，**入口在 DOM 中不渲染**，不用 `disabled` 置灰——置灰意味着"当前不可用、可设法变可用"，而换设备不是界面内的操作。此规则同时使"入口不可见"成为可被自动化验收的断言（查节点是否存在）。

### 23.4 通知中心（顶栏铃铛）

面向**所有有可能收到通知的身份**，**不是仅管理员** —— 入口的可见性判据在 §8（按通知收件人集合判，不按身份写死）；桌面端与移动端入口位置统一在顶栏右侧。

> **须守住「通知不是管理员功能」这层意思**：没有铃铛的只能是「一类通知都收不到」的身份，**「只给管理员铃铛」在任何产品里都会被 §8 那条判红**（管理员若一类都收不到，他恰是那个没有铃铛的身份）。
> **一条通知都收不到的身份不渲染铃铛** —— 恒空的入口是**通向不存在内容的死入口**（同 §23.3 末铁律与 §8.1「不可用项不渲染」）。

| 项 | 规则 |
|---|---|
| 入口 | 顶栏铃铛图标按钮（`36×36`，§8） |
| 未读角标 | 右上角红点数字（`--danger` 底 + 白字），**≤99 显数字，超出显 `99+`** |
| 列表 | 点击展开**右侧 Drawer**（玻璃浮层 §5.5、`--elev-3`）；按时间**倒序**；移动端 Drawer 改全屏页 |
| 条目 | 语义图标（§19.1）+ 标题（Body）+ 摘要（Footnote，两行截断）+ 相对时间；未读条目左侧 accent 圆点 + `--accent-soft` 微染底 |
| 已读 | 逐条点击即标记已读并跳转对象；顶部提供「全部已读」按钮 |
| 空状态 | 「暂无通知」（§18.1） |
| 加载 | 骨架行（§13.2）；滚动到底分页加载 |

> 与 §19 的四类瞬时反馈区分：Toast / 通知卡片是**瞬时**的，铃铛消息中心是**持久化**的。同一事件可两者都出（实时弹一次 + 落入列表），但文案由同一处生成，不各写一套。

---

## 24. 富文本编辑器（WYSIWYG）

用于长文正文录入（说明文档、长文备注等）。**编辑器的能力集不是越多越好——工具栏每多一个按钮，就多一种正文结构要在展示端、搜索端、导出端各处兼容。**

### 24.1 能力集声明（强制）

- 工具栏能力**由需求逐项声明**，编辑器只开启被声明的项，**不启用库的默认全量工具栏**。
- 未声明的能力（表格、字体、字号、文字色、背景色、公式等）一律关闭；粘贴内容中的未声明结构在**粘贴时即清洗**为纯文本或最近的已声明结构，避免"工具栏没有但正文里有"。

### 24.2 形态

| 区域 | 规则 |
|---|---|
| 工具栏 | 置于编辑区顶部，sticky；图标按钮 `32×32`，圆角 `--r-xs`，hover `--surface-2`，激活态 `--accent-soft` + `--accent` |
| 编辑区 | `--surface`，圆角 `--r-lg`，`--elev-1`；内边距 `var(--sp-5)`；正文排版遵 §3.2（Body 15/22），标题层级映射到 §3.2 字号阶 |
| 聚焦态 | 容器整体聚焦绽放（§15.1） |
| 只读态 | 工具栏**不渲染**（非置灰），编辑区去掉输入态描边，仅呈现排版后的正文 |
| 保存 | 自动保存 + 「已保存 HH:mm」footnote 提示；离开未保存时二次确认 |

### 24.3 附件区

| 项 | 规则 |
|---|---|
| 位置 | 编辑区下方独立分区，标题「附件」+ 计数 |
| 上传 | 拖拽 + 点击选择；上传中显示逐文件进度条 |
| 限制 | **类型白名单、单文件上限、单文档总量上限由需求声明**；界面须同时呈现总量用量（「已用 X / Y」进度条） |
| 超限 | 上传前即校验并拒绝，红字写明**是类型不符还是大小超限**，不写笼统的"上传失败"（§19.2 文案规则） |
| 条目 | 文件类型图标 + 文件名（省略号截断）+ 大小（`tabular-nums`）+ 下载 / 删除（删除二次确认） |
| 移动端 | 按 §23.3，若该产品未声明移动端支持富文本编辑，则整个编辑器与附件区在移动端呈**只读态** |
```

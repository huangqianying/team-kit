本项目的上下文持久规则统一维护在 **`AGENTS.md`** 文件中。

**项目级上下文规则请直接编辑 `AGENTS.md`**；角色正文、契约与 skill 在各自唯一事实源维护，本文件只保留入口。

> `AGENTS.md` 是 Claude、Codex 等 AI 助手的共享规范文件，Claude Code 在此仓库工作时应以 `AGENTS.md` 为准。

项目级 skill 存放在 **`skills/*/SKILL.md`**（`.claude/skills` 与 `.codex/skills` 均为软链），Claude Code 在执行任务前应扫描并使用匹配的 skill。

五角色协作契约见 **`docs/rules/团队协作契约.md`**：**SA 由当前值守会话承担**，PM / UI / SE / QA 的共享正文在 `docs/rules/roles/`，Claude 原生入口在 `.claude/agents/`，Codex 原生入口在 `.codex/agents/`。派活与取证依契约 §三。

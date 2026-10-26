# Task：填写目标

> 可直接用于任务消息、Issue 或 PR，不要求新增任务文档。短任务用简短段落表达必填内容即可。流程以 [CONTRIBUTING](../CONTRIBUTING.md) 为准。

## 必要内容

- 目标与可验证验收条件：填写。
- Task Scope / 非目标：填写。
- 当前 Human 授权与限制：填写或引用；注明只读、仅设计或允许实施。
- 风险：轻量 / 标准 / 高风险；说明影响与理由。
- 适用 canonical references 与关键依赖：引用；没有则明确说明。

## 按需内容

- 必要方案或重大待决问题：选项、trade-off、建议；是否已获批准。
- 输入版本：base branch / SHA。
- Write Scope 与唯一 Owner：单人执行可由明确执行者隐含；分工/交接必须显式。
- 多 Agent：仅需要时列依赖、隔离方式及整合负责人。
- Validation：匹配行为的检查、Required Gates；标准/高风险须 Independent Review。
- 风险、失败/回滚方案：按影响填写。

## Checkpoint（仅暂停或交接时）

引用现有记录，补充 branch/head、未提交改动与 ownership、验证版本/结果、剩余工作及下一步。不得用摘要代替仓库恢复，不把旧验证写成新 head PASS。

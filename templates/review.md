# Independent Review

> 用于适用的独立审核；结果优先写在原 PR。权威规则见 [CONTRIBUTING](../CONTRIBUTING.md#7-independent-review)。未实际审核不得勾选或预填通过。

## 版本、范围与独立性

- PR / Task：填写引用。
- Base SHA / reviewed head SHA：填写实际值。
- Reviewer 与独立性：确认未参与主要实现、使用独立 Context；否则明确这只是 self-check。
- 授权与审核范围：引用 Task、相关批准和 canonical docs。

## 实际检查与证据

- 实际 diff、相关实现及范围/ownership 边界：说明检查内容。
- 验收、失败边界、回归风险和文档同步：说明结果。
- 验证记录：实际 head、检查/命令、环境、结果、证据链接；区分亲自执行和核对已有结果。
- 临时 merge SHA（适用时）：记录实际 CI 执行版本与对应 PR head。
- 未执行、未配置或不能验证的事项：原因、影响，是否阻塞。

## Findings

每项列严重性、文件/位置、具体影响、所需修复和验证建议。没有发现时写“本范围未发现阻塞项”，不声称不存在任何缺陷。

## 结论与下一步

- 结论：无阻塞发现 / 需修复 / 无法完成审核。
- 覆盖 head SHA 与已知限制：填写。
- 修复后复核：新 head、增量范围、重跑验证与更新结论；旧结论不自动迁移。
- 下一 Gate：Human 最终接受与 Merge，或必要修复/验证。

Reviewer 默认只读。必需独立审核无法取得时明确阻塞；审核结论不代替 Human 决策或 Merge。

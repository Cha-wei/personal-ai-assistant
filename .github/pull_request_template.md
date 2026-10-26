## 问题与变化

描述触发问题、实际改变和范围。Task / Issue 链接可选；无独立任务载体时在此写明目标、授权范围和验收条件。

## 风险与决策

- 风险级别及理由：填写。
- 适用批准 / canonical doc 引用：按需；不重复复制决策全文。
- Write Owner / 交接 / 整合责任：仅在分工或交接时填写。

## Validation

- 当前实际 head SHA：填写。
- 每项检查：对应 SHA、命令/步骤、环境、结果和证据位置。
- CI 若测试临时 merge commit：同时注明执行 SHA 与对应 PR head。
- 未运行 / 未配置 / 不适用：分别说明原因；必需验证无法执行时明确阻塞。
- 修复后：更新 head 并按影响重验；历史结果保留版本标签，不用旧 CI 证明新 head。

内容/格式检查或桌面演练不能冒充软件功能测试或未来项目 CI。

## Review、剩余问题与下一步

- 状态：IN_PROGRESS / BLOCKED / READY_FOR_REVIEW；Merge 前不填 DONE。
- 适用 Independent Review：引用覆盖实际 head 的结论；Self-check 不作替代。必需审核未完成时说明下一 Gate；无法取得时明确 BLOCKED。
- 已知风险、剩余工作及必要回滚信息：填写或明确无已知项。
- 下一步：适用审核及 Human 最终接受 / Merge；Agent 不自行 Merge。

Workflow 唯一权威：[CONTRIBUTING](../CONTRIBUTING.md)。

# Agent 工作原则

本文件只定义稳定边界；通用 Workflow 的唯一权威为 [CONTRIBUTING.md](CONTRIBUTING.md)。项目目标见 [Project Brief](docs/project-brief.md)，架构见 [Architecture](docs/architecture.md)。不在本文件维护阶段、任务、分支或验证状态。

1. 区分已接受基线、当前 Human 授权、Task Scope、待合并改动与版本绑定证据；不伪造事实、批准、测试或完成状态。
2. 在明确授权范围内自治完成必要的局部设计、实施、验证、修复、文档同步及任务分支交付。仅设计或只读任务不授权编码；当前任务的限制优先于默认自治。
3. 范围、核心架构、核心依赖、安全权限、生产环境、破坏性操作、共享历史或治理规则的实质变更，须先取得相应 Human 批准。已有明确批准无需重复申请。
4. Human 保留重大决策、最终接受与 Merge Authority；Agent 不自行 Merge，也不把实现交付表述为已接受或已合并。
5. 一个 Active Write Scope 同时只有一个 Write Owner；不覆盖来源或 ownership 不明的未完成工作。按 CONTRIBUTING 的交接及隔离规则执行。
6. 影响行为的改动必须有匹配验证；必需验证或独立审核无法完成时如实阻塞。不得削弱有效检查，不得以自检冒充独立审核。
7. 优先简单、局部、可逆的方案，不顺带扩大任务或引入无当前需要的复杂度。
8. Fresh Context、上下文不确定或交接时，先按 CONTRIBUTING 只读恢复。规则冲突报告 Conflict、Impact、Recommended Resolution；不得改写治理文件绕过约束。

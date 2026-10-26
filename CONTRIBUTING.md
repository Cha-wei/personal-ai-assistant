# 通用开发 Workflow

本文是通用 Workflow 的唯一权威；[AGENTS.md](AGENTS.md) 定义稳定工作边界。模板不预设业务、架构、技术栈、测试工具或 AI 产品。

## 1. Authority 与规则边界

必须区分以下来源，不能互相替代：

| 来源 | 含义 |
| --- | --- |
| 已接受项目基线 | 已合并 `main` 的实际代码及适用 canonical docs；文档中的草案、未知项、历史记录仍保持各自状态，不因合并变成批准事实 |
| 当前 Human 授权 | 允许本次执行的动作与限制；可来自当前任务或可追溯的明确批准，不因分支、PR 或建议存在而自动产生 |
| Task Scope | 本次目标、允许修改的范围、非目标与验收条件；不等同于项目整体范围 |
| 待合并变更 | 工作树、任务分支与 PR 的候选内容；不得冒充 `main` 当前状态 |
| 版本绑定证据 | 对指定版本、范围、环境实际执行的验证或审核；不自动覆盖后续 head 或更大范围 |

Human 保留重大决策、最终接受与 Merge Authority。设计批准是否同时授权实施须明确；仅设计任务不授权编码。明确授权已满足审批要求时不反复申请。

AGENTS 的稳定边界约束本文；当前任务可以覆盖默认流程（例如只读、不 commit、不 push），不能以“更轻量”为由伪造证据或绕过必需验证、安全和 Human 决策边界。项目已批准决策在适用范围内生效；改变决策须获得相应批准。无法同时遵守的规则按第 9 节处理。

项目事实分别放在 [Brief](docs/project-brief.md) 与 [Architecture](docs/architecture.md)。Task/Issue 记录任务边界，PR 记录当前交付，Review 记录发现，自动化保留执行结果；引用已有权威位置，不复制全套内容。聊天中的想法和 Agent 总结不自动成为正式决策；需长期保留的 Human 决定在对应 canonical doc 记录批准依据。

## 2. 默认流程与风险

`Task → Readiness / Design（按需）→ Implementation → Validation → Review → Human Merge`

开始前能够说明目标、范围、可验证验收条件、必要依赖和授权即可；缺少重大决策时暂停相关部分，其他独立且已授权工作可继续。普通局部设计由 Agent 自主完成。

| 级别 | 适用情况 | 最小流程 |
| --- | --- | --- |
| 轻量（默认） | 局部、低风险、可逆的文档或实现修改 | 简短任务、匹配验证、PR、Human 检查与 Merge；不强制 Issue、单独设计审批、ADR、Coordinator 或额外 Agent |
| 标准 | 新行为、跨模块变更、接口或兼容性影响 | 明确验收条件、必要的简短方案、相关验证及 Independent Review |
| 高风险 | 核心架构/依赖、安全权限、生产操作、破坏性数据或较大影响范围 | 先提交选项、trade-off、建议及回滚/失败方案，取得 Human 批准；再实施、针对性验证及 Independent Review |

按影响而非代码行数分级；执行中风险升高时升级相关流程。范围或正式需求变化、治理规则实质修改、改写共享历史同样须先获 Human 批准，不得借普通修复顺带实施。重大决策可以在同一任务/PR 内批准和记录，不强制 registration-only PR 或额外 Code Start 审批。

Required Gate 来自当前任务/验收条件、适用正式规则、已配置的必需 CI/保护规则，以及证明所声称行为不可缺少的验证。标准和高风险任务的 Independent Review 是 Required Gate。风险分级不能用来降低已有要求。

## 3. 角色、Write Ownership 与并行

| 角色 | 职责 |
| --- | --- |
| Human | 重大决策、最终接受与 Merge |
| Coordinator（可选） | 拆分、依赖协调、分工和整合 |
| Implementation Agent / Write Owner | 在授权范围内实施、验证与交付 |
| Independent Reviewer | 默认只读，直接检查实际变更和证据 |

角色不绑定产品或模型。单 Agent 串行默认；简单任务无需 Coordinator。一个 Active Write Scope（文件、目录、模块或明确范围）同一时刻只有一个 Write Owner。写入包括生成、格式化、删除和覆盖。同一文件不同章节默认仍重叠。

并行写入仅在目标可独立描述、验收可独立验证、输入版本明确、依赖/接口稳定、范围不重叠时启用。独立执行上下文使用独立任务分支和隔离 workspace/worktree；同一 writable working tree 不同时交给多个 writer。数据库、服务、缓存、生成目录等共享可变资源须隔离或串行；不同分支不代表环境隔离。明确整合负责人，整合后验证组合结果；条件不满足则串行。

交接须先确认旧 Owner 停止写入，在已提交或其他可恢复边界明确新 Owner 和范围。新 Owner 从实际 Git 状态恢复，不仅依赖交接摘要。Reviewer 若需修改，显式转移 ownership，并按其修改的风险安排所需独立审核；不机械建立无限审核链。

## 4. Fresh Context、只读恢复与 Checkpoint

新 Context、压缩/重置、状态不确定或交接时，默认先只读：

1. 确认 repository root、工作目录、分支、head、working tree；保留未知来源的改动。
2. 读取 AGENTS 和本文适用章节，从 README 定位本任务所需 canonical docs。
3. 按需检查相关代码、commit、任务授权及 PR/CI；不默认扫描全部历史。
4. 确认基线、授权、Task Scope、Owner、未完成工作、版本绑定验证与下一步。

只读恢复不授权编辑、安装依赖、运行有副作用的命令、启动服务或写外部系统。恢复到可靠的既有授权后可继续，无需仅因 Context 新而重新申请；授权不明则澄清缺失部分。发现仓库与预期不一致先报告差异。

暂停、交接、上下文切换或关键边界时按需留 Checkpoint：任务/授权引用、branch/head、未提交改动及 ownership、验证版本与结果、剩余工作、下一步。优先用现有 Task/PR；已有可靠信息用链接引用，不创建固定 checkpoint 台账。未提交检查应注明其工作树状态，不能仅用 HEAD 代表未提交内容。

## 5. Git、PR 与 Bootstrap

正常开发从已核对的 `main` 创建任务分支，推荐 `codex/<task>`，不直接向 `main` 交付。一个逻辑完整、可理解、可验证、可回滚的变更形成对应 commit；提交前检查实际 diff/status，不混入他人或无关改动。远端存在且任务未限制时，自治 commit、push 并创建/更新 PR；Human 执行最终接受和 Merge。未经单独明确授权不得代为 Merge、启用自动 Merge、force push、改写共享历史或绕过保护规则。

Issue 可选：短任务可直接通过任务输入和 PR 定义边界；跨会话或多步骤工作需要时才建 Issue。使用 [Task 模板](templates/task.md) 为可选，不强制新增任务文件。修复默认留在原 Issue/分支/PR；只有独立范围、授权或回滚边界才拆分。Review 后更新当前 PR 摘要，保留历史证据的版本标签。

**首次 Bootstrap：** 新仓库尚无 `main`、PR、CI 或测试时，Human 的初始化授权可以直接覆盖必要的初始提交/推送，无须机械要求已有 PR。初始化不代表软件功能已通过验证，也不自动授权业务实现。若需保留首次模板内容供 Human Merge，可建立空的 bootstrap `main` 提交，再将文件放入任务分支 PR。初始基线与待审核内容须明确区分；仓库可见性和后续保护设置须明确记录，不声称未配置的限制已被强制执行。

## 6. Validation 与 head-bound evidence

按实际变更选择测试、回归、边界、集成、构建、人工检查或 AI Eval。新行为增加/更新相关测试；Bug 尽可能先复现并建立回归验证。Prompt/Agent/Tool 行为变化执行相关 Eval；文档改动检查内容、链接和一致性即可，不冒充功能测试。机械检查优先交自动化，Human 关注决策、风险和接受。

每项验证明确：**实际 head SHA、检查内容/命令或步骤、环境、结果、证据位置及限制**。本地未提交检查只能证明明确记录的工作树；提交后须核对内容对应实际 head。PR CI 可能测试临时 merge commit，应同时记录 PR head 与实际执行 SHA，不能混称相同版本。

修复产生新 head 后，按影响范围重新执行相关验证并检查必需 CI。旧 head 的 PASS 不能证明新 head 通过；不受影响证据如保留引用，须说明范围与理由，不能写成新 head 全部通过。必需审核同样绑定 head；后续修改后 Reviewer 检查增量及其影响，更新结论覆盖的新 head。

单项结果用 `PASS`、`FAIL`、`NOT RUN`（说明原因）、`N/A`（确实不适用）或 `NOT CONFIGURED`（尚不存在）。不存在的 CI、测试、Eval 不得写 PASS。缺少必需检查时，无论尚未配置还是无法运行，都须明确阻塞交付或下一 Gate，不能静默跳过。不得通过删除、跳过、弱化有效断言或反复重跑掩盖失败/不稳定结果。

## 7. Independent Review

按第 2 节风险与 Required Gate 适用；轻量任务可由 Human 直接检查真实 diff 和验证，不强制另开 Agent。Self-check 有价值，但不构成 Independent Review。

独立 Reviewer 未参与主要实现，使用独立 Context，核对 base/head、授权范围、实际 diff/相关代码、测试与验证证据，并检查失败边界和回归风险。不同模型不自动代表独立；Implementer summary 只作导航。使用 [Review 模板](templates/review.md)，结果优先留在原 PR，发现包含位置、影响和建议。

结论为“无阻塞发现”“需修复”或“无法完成审核”，注明覆盖版本、范围与限制。必需独立审核不可取得时停在 `BLOCKED`，不得以自检替代。修复由 Owner 在原 PR 完成，再按影响范围复核；审核结论不是 Human 最终接受或 Merge。

## 8. 交付与完成

PR 使用 [交付模板](.github/pull_request_template.md)，只摘要变化、验证、风险、剩余项和下一步，详细日志引用原证据。

- `IN_PROGRESS`：实施或适用验证尚未完成。
- `BLOCKED`：缺少必需信息、批准、验证或审核，并明确解除条件。
- `READY_FOR_REVIEW`：实施与相应验证完成，等待适用审核/Human 接受；不是 DONE。
- `DONE`：适用验证与审核完成、Human 已接受且代码任务已合并。仅设计/只读任务以其授权交付物被 Human 接受为完成条件，不虚构 Merge。

报告实际 branch/head、是否 push、PR 状态、验证范围和未解决问题。已合并不自动代表已部署、生产就绪或业务成功；版本绑定接受不能自动扩展到未来版本。

## 9. 冲突与复杂度控制

规则或授权有冲突时报告 **Conflict / Impact / Recommended Resolution**，必要时给出选项和 trade-off，暂停受影响实施等待 Human 决策；独立已授权部分可继续。不得静默选择便利规则或改写治理文件绕过约束。

优先局部、可替换、可回滚方案。只在实际需求出现时增加 ADR、专项规范或基础设施；普通任务不强制新增管理文档。正式行为、接口、配置、范围或架构变化时同步对应 canonical doc；内部改动不制造无意义登记。

# Personal AI Assistant

模块化、以本地使用为优先的个人 AI 工作空间，面向个人项目、任务与知识管理。

## 当前开发状态

当前处于项目 Bootstrap：建立开发规范与产品文档，尚无业务代码。产品规划不等于实施授权；模块功能须通过后续明确任务推进。

## 核心模块规划

- **模块 1：项目接入与上下文管理**：独立接入本地项目或 GitHub 仓库，也可关联两者；获取结构、文件、版本与变更事实。
- **模块 3：智能项目管理**：进度可视化、任务管理、主动进展感知、执行证据整理、智能预核验与人工确认。
- **模块 4：个人知识库**：资料收藏、基础分类、搜索、AI 总结及基于资料的问答。

统一工作空间与 AI 对话属于产品方向；具体交互尚未决定。长期方向见产品蓝图。

## 项目文档

- [Agent 原则](AGENTS.md)与[开发 Workflow](CONTRIBUTING.md)
- [Project Brief](docs/project-brief.md)：目标、范围、约束与未知项
- [Architecture](docs/architecture.md)：已明确方向与待决技术问题
- [产品蓝图](docs/product-blueprint.md)：规划与实施边界
- [Task 模板](templates/task.md)、[Review 模板](templates/review.md)、[PR 模板](.github/pull_request_template.md)

## 当前验证入口

当前仅有 Markdown 文档及 Git 忽略规则，可检查全文、相对链接、模板一致性、Git diff 和拟跟踪文件。没有软件运行入口，尚未配置构建、自动测试、AI Eval 或 CI；没有可声明通过的功能测试。

后续实际运行命令、环境要求及验证入口在此维护。尚未配置分支保护；没有选择开源许可证，公开可见不代表已授予开源许可。

## 规范来源

通用治理文件和任务、审核、PR 模板来自 personal-ai-dev-starter；项目说明与范围文档根据 Human 的初始化任务填写。未引入 Starter 的 Git 历史或业务资料。

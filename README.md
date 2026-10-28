# Personal AI Assistant

模块化、本地优先的个人 AI 工作空间，面向真实项目接入、版本变化感知、AI 项目理解、项目全景展示与个人知识管理。

## 当前开发状态

项目已完成独立 Git 仓库 Bootstrap，当前处于**产品与总体架构设计阶段**；需求、架构决策及设计文档本身属于项目成果，经过 Human 确认后通过 Git 进行版本管理。

T01 任务分支提供首个 Windows 本地只读 MCP 工具；交付与验收状态以对应 PR 的版本绑定证据为准。**设计共识及产品规划不自动授权功能实施**；后续业务开发须有明确的 Task Scope、验收条件及 Human 授权。

## 核心模块规划

- **模块 1：项目接入与上下文管理（近期重点）**：接入本地项目或 GitHub 仓库，也可显式关联；按需获取文件、Git 事实及已观察版本间的变化，不复制完整仓库或重复维护 Git 历史。
- **模块 2：智能项目管理**：以项目目标、模块与功能全景图为产品方向，区分设计与开发进展；先复用现有开发记录进行只读汇总，不另建 Agent 的任务派发、测试或验收系统。
- **模块 3：个人知识库**：独立资料收藏、基础分类、检索、AI 总结及按需项目关联。

统一工作空间提供项目导航、基础概览和 AI 对话。AI 可辅助理解项目、解释版本变化与生成可视化内容；丰富效果图按需提供，不替代真实项目事实和可交互信息。实施优先级与边界见产品蓝图。

## 项目文档

- [Agent 原则](AGENTS.md)与[开发 Workflow](CONTRIBUTING.md)
- [Project Brief](docs/project-brief.md)：目标、阶段、授权范围与未知项
- [Architecture](docs/architecture.md)：架构方向、模块边界与数据原则
- [产品蓝图](docs/product-blueprint.md)：模块功能、阶段安排与实施边界
- [Task 模板](templates/task.md)、[Review 模板](templates/review.md)、[PR 模板](.github/pull_request_template.md)

## 当前验证入口

T01 的运行与测试入口如下。尚未配置 CI 或 AI Eval，不将本地测试等同于完整模块验收。

### Windows 本地 MCP（T01）

要求：系统 Git CLI、Python 3.12+（实际验证 Python 3.14.4）、本地 Codex。PowerShell：

```powershell
Set-Location E:\AI-assistant
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe .\mcp_server.py --project E:\AI-assistant
```

最后一条命令启动 stdio 服务，等待 MCP 客户端输入；不监听网络端口，不能把等待输入误判为启动失败。正常使用由 Codex 启动，无需手动常驻服务。

先用 `codex mcp list` 确认名称未被占用，再注册（使用绝对路径，保留其他配置）：

```powershell
codex mcp add t01_project_status -- E:\AI-assistant\.venv\Scripts\python.exe E:\AI-assistant\mcp_server.py --project E:\AI-assistant
codex mcp get t01_project_status
```

在新建的本地 Codex 聊天中要求：“调用 t01_project_status 的 get_project_status，无参数，返回结果。”也可用 `codex exec -s read-only "调用 t01_project_status 的 get_project_status，不使用 shell，不修改文件，返回完整结果"` 验证真实模型工具调用。已有会话可能需要重新打开才能发现新工具。注册成功、Python 测试成功均不能替代真实 Codex 调用证据。[Codex 官方 MCP 说明](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。

工具只查询启动时指定的唯一仓库根目录，没有模型可选的路径或命令参数。返回 `ok`、项目路径、分支（detached 时为 null）、完整 HEAD、`clean`、暂存/未暂存/未跟踪/冲突数量、UTC 查询时间与 `local_git_cli` 来源。数量按状态分类，同一文件可以同时计入暂存和未暂存；冲突单独统计。错误返回 `ok=false` 和错误代码，不将失败表示为干净。无提交的仓库返回 Git 查询失败。

边界：不查询远端、不把 `origin/main` 当作实时 GitHub，不返回文件正文或文件名，不执行 Git 写入。忽略子模块内部状态（`submodule_contents_checked=false`）；`clean` 仅代表本次该查询范围。拒绝嵌套非仓库目录、gitfile/linked worktree、外部 Git 公共目录和对象 alternates；在 Git 调用前检查整个授权目录树，保守拒绝 symlink/junction（包括忽略目录内的链接）。本地 Git 配置只接受源码中列出的基本 core/remote/branch/user/init 字段；拒绝 include、filter、外部路径及其他未支持配置，系统和用户级 Git 配置不载入。关闭 fsmonitor、hooks、外部属性/忽略文件及延迟对象获取。不支持任意 Git 布局，目录类型检查的耗时随项目规模增长。查询不是原子快照，查询时应避免并发切换分支或编辑。Git 状态计算可能读取授权项目文件以判断修改，安全预检读取本地 Git 配置，但这些正文不进入 MCP 输出。

只有操作者可以更改启动授权目录；应仅注册自己信任并控制的仓库及系统 Git。此应用边界不是操作系统级隔离，不能抵御同一用户恶意并发替换目录或篡改 Git 安装。个人 Codex 配置保存在用户配置位置，`.venv` 与缓存不提交。移除本次接入使用 `codex mcp remove t01_project_status`，无需修改其他服务器。

后续实际运行命令、环境要求及验证入口在此维护。尚未配置分支保护；没有选择开源许可证，公开可见不代表已授予开源许可。

## 规范来源

### T03：GitHub 正式基线查询

stdio 启动参数增加 `--github-repository Cha-wei/personal-ai-assistant` 后启用无参数 `get_project_baseline_status`。不配置时保留 T01 工具列表与行为。操作者固定配置项目与仓库关联，模型不能输入路径或 URL；不从 origin 推断关联。

新工具复用本地查询，`local` 保留工作区状态，`remote` 包含 main SHA、GitHub 来源与 UTC 请求时间。`relation` 为 SAME/AHEAD/BEHIND/DIVERGED/UNKNOWN；计数仅描述已提交历史。只有本地完整提交图、远端 commit 对象可用且没有 shallow/replace/grafts 时计算关系，否则 UNKNOWN 并附原因。不会自动 fetch 或写入 Git。

仅匿名 HTTPS GET `api.github.com:443/repos/{配置仓库}/git/ref/heads/main`，验证 TLS，不跟随重定向，不读取令牌、代理环境或 Git credential helper。每次 socket 操作超时 10 秒，响应上限 64 KiB，不重试或缓存。HTTP 403/404/429、网络失败及无效响应不能表示“无变化”；404 不区分不存在与无权访问。不是原子快照，目录扫描和恶意并发限制沿用 T01。

保留现有注册，使用独立名称：

```powershell
codex mcp add t03_project_baseline -- E:\AI-assistant\.venv\Scripts\python.exe E:\AI-assistant\mcp_server.py --project E:\AI-assistant --github-repository Cha-wei/personal-ai-assistant
```

在新聊天中调用该服务器的两个工具核对兼容性；DeepSeek Harness 可复用同一 stdio 命令，但实际兼容性须另有证据。移除本次注册：`codex mcp remove t03_project_baseline`。

通用治理文件和任务、审核、PR 模板来自 personal-ai-dev-starter；项目说明与范围文档根据 Human 的项目需求和后续架构共识维护。未引入 Starter 的 Git 历史或业务资料。

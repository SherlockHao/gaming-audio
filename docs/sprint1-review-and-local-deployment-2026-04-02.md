# Sprint 1 代码检查与本地部署反馈

日期：2026-04-02  
检查环境：Windows 本地开发机  
仓库：`gaming-audio`  
目的：核对当前代码与 `Sprint 1` / `M1` 目标的一致性，并确认本地可运行状态。

---

## 1. 结论摘要

当前仓库已经具备以下基础能力：

- 后端 FastAPI 服务骨架可运行
- PostgreSQL 数据库模型和 Alembic 迁移可运行
- `Task CRUD`、规则基础接口、审计日志、状态机单元测试已落地
- 后端测试在本地通过
- 前端项目可以安装依赖并完成构建

但从 `Sprint 1 已完成` 的口径看，当前实现仍有几个需要尽快反馈给团队的问题：

- 存在一个明确的跨项目规则更新漏洞
- 若 `project_id` 非法，当前接口会直接抛数据库错误，而不是返回受控业务错误
- `Celery + Redis` 和 `MinIO` 目前更接近“脚手架已建”，还不能完全视为闭环验收完成
- 前端测试与 CI 配置没有落地到仓库
- `Style Bible / Category Rules` 的内容资产或初始化方式不明确

建议：这轮不要把这些问题理解成“推翻 Sprint 1”，而是作为 `Sprint 1 收尾 / M1 进入前门禁` 的修正项。

---

## 2. 已验证通过项

以下内容已在本地实际验证：

- Python 环境可用：`Python 3.11.9`
- Node 环境可用：`Node 24.14.0`
- pnpm 可用：`10.33.0`
- PostgreSQL 16 可用，服务运行在 `5433`
- 后端数据库迁移可执行：`alembic upgrade head`
- 后端测试通过：`44 passed`
- 前端构建通过：`pnpm build`
- 后端健康检查可访问：`/health`

从能力上看，当前仓库已满足“本地可拉取、可安装、可启动、可继续开发”的协作前提。

---

## 3. 已验证问题

### 3.1 跨项目规则更新漏洞

问题描述：

- 当前规则更新接口使用了路径参数 `project_id`
- 但更新时并没有校验该 `rule_id` 是否属于该 `project_id`
- 这意味着可以通过 `项目 B` 的路径去更新 `项目 A` 的规则

相关代码位置：

- `server/app/modules/rule/router.py`
- `server/app/modules/rule/service.py`

复现结果：

- 已在本地创建两个项目 `P1` 和 `P2`
- 先在 `P1` 下创建规则
- 再调用 `P2` 路径下的更新接口，仍然返回 `200`
- 返回结果中的 `project_id` 仍然指向 `P1`，说明确实发生了跨项目更新

影响：

- 这和架构文档中“按 `project_id` 隔离”的设计目标直接冲突
- 后续接入权限系统后，这会成为明显的数据隔离漏洞

建议：

- 更新接口查询条件应改为 `project_id + rule_id`
- Service 层不要只按 `rule_id` 查找旧规则
- 增加回归测试：禁止跨项目更新规则

优先级建议：高

---

### 3.2 非法 `project_id` 会直接抛数据库异常

问题描述：

- 当前创建任务和创建规则时，没有先检查 `project_id` 是否存在
- 一旦传入随机 UUID，会在数据库 `commit()` 时触发外键异常
- 该异常当前没有被转成受控业务响应

相关代码位置：

- `server/app/modules/task/service.py`
- `server/app/modules/rule/service.py`

本地复现结果：

- 创建任务时传入不存在的 `project_id`，抛出 `ForeignKeyViolationError`
- 创建规则时传入不存在的 `project_id`，同样抛出 `ForeignKeyViolationError`

影响：

- API 返回会变成未处理异常，而不是可预期的 `404` 或 `400`
- 前端后续接入时会遇到不稳定错误形态
- 测试环境和生产环境日志会出现大量底层数据库异常

建议：

- 在 Service 层先检查项目是否存在
- 或统一捕获 `IntegrityError` 并转成明确业务错误
- 增加接口级测试覆盖非法 `project_id` 场景

优先级建议：高

---

## 4. 建议确认项

### 4.1 `Celery + Redis` 目前仍是基础脚手架

当前状态：

- 已有 `celery_app.py`
- 已有 Broker / Backend 配置
- 但仓库中未看到实际任务定义、消费样例、worker smoke test 或健康检查路径

结论：

- 可以说“异步基础设施骨架已建”
- 但若按执行计划中的“测试任务可投递和消费”作为验收标准，目前证据还不充分

建议：

- 团队将当前状态表述为 `foundation ready`
- 或补一个最小异步任务闭环测试作为 Sprint 1 收口项

优先级建议：中

---

### 4.2 `MinIO` 目前仍是 SDK 封装，不是完整闭环

当前状态：

- 已有 `storage.py`
- 已有建桶、上传、下载、预签名函数
- 但未看到启动时自动建桶、上传 API 接入、集成测试或本地 smoke test

结论：

- 当前更像“文件存储适配器已准备”
- 还不能完全等同于“文件可上传和下载已通过验收”

建议：

- 如果 Sprint 1 目标只是打底，这个状态可以接受
- 如果要严格对应执行计划验收标准，建议补最小上传下载验证

优先级建议：中

---

### 4.3 前端测试与 CI 配置未见落地

当前状态：

- 前端可运行、可 build
- 但 `web/package.json` 中没有 `test` 脚本
- 仓库中未见前端测试配置
- 仓库中未见 `.github/workflows` 或其他 CI 工作流配置

结论：

- “测试框架搭建完毕，pytest + Jest + CI 配置” 这一条目前只能算后端部分完成

建议：

- 团队重新标注 Sprint 1 状态，避免高估完成度
- 尽快补前端测试基础配置和 CI 最小门禁

优先级建议：中

---

### 4.4 `Style Bible / Category Rules` 的内容资产来源不清楚

当前状态：

- 数据模型和 API 已支持 `style_bible`
- 规则 CRUD 接口已存在
- 但仓库中未看到明确的 `Style Bible v1`、规则 seed、初始化脚本或样例内容文件

结论：

- 代码支持“存规则”
- 但当前仓库不足以说明“规则内容已经准备好并可复现导入”

建议：

- 团队需要明确规则真源是：
  - 数据库初始化
  - 仓库中的 JSON/YAML 文件
  - 外部内容库
- 若规则由音频团队线下维护，建议至少提供样例或导入流程说明

优先级建议：中

---

## 5. 对 Sprint 1 完成度的判断

按“工程基础是否存在”来判断：

- 基本成立

按“执行计划中的验收门禁是否严格达成”来判断：

- 还未完全闭合

更准确的说法建议是：

- `Sprint 1 核心后端基础已完成`
- `M1 所需的规则内容、异步闭环、文件存储闭环、前端测试/CI 仍需继续补齐`

---

## 6. 本地部署状态

当前本地环境已可继续开发，状态如下：

- 仓库目录：`D:\codex\gaming-audio`
- 远程仓库：`origin -> https://github.com/SherlockHao/gaming-audio.git`
- Python：`3.11.9`
- Node：`24.14.0`
- pnpm：`10.33.0`
- PostgreSQL：`16.13`
- PostgreSQL 服务：`postgresql-x64-16`
- PostgreSQL 端口：`5433`

本地已经验证通过：

- `alembic upgrade head`
- `pytest`
- `pnpm build`

启动方式：

后端：

```powershell
cd D:\codex\gaming-audio\server
.\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --reload
```

前端：

```powershell
cd D:\codex\gaming-audio\web
pnpm dev --hostname 127.0.0.1 --port 3000
```

访问地址：

- 后端健康检查：`http://127.0.0.1:8000/health`
- 前端：`http://127.0.0.1:3000/tasks`

---

## 7. 说明

本轮反馈遵循以下原则：

- 以本地实际运行、实际复现为准
- 以建议形式反馈给团队
- 不直接改业务代码、不改远程仓库实现

补充说明：

- 当前本地工作区存在一个未提交改动：`server/pyproject.toml`
- 原因是原始仓库在本地执行 `pip install -e .[dev]` 时会失败，需要补 setuptools 打包配置
- 这一项建议作为团队统一修复项处理，而不是个人本地长期保留

---

## 8. 建议团队优先处理顺序

建议按下面顺序反馈和处理：

1. 修复跨项目规则更新漏洞
2. 统一处理非法 `project_id` 的错误返回
3. 明确 Sprint 1 中 `Celery / MinIO / CI / 前端测试` 的完成口径
4. 明确 `Style Bible / Category Rules` 的内容来源和初始化方式
5. 统一修复 `server` 本地 editable install 的打包配置


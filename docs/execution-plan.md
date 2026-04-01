# AI 游戏音频生产与集成系统 - MVP 执行计划 v1.0

---

## 1. 执行总览

### 1.1 MVP 目标回顾

MVP 不追求全品类、全自动、高艺术质量，而是验证以下核心命题：

- 专业音频前置建制后，系统能否稳定接收低门槛需求输入
- 系统能否把标准化 SFX/UI/基础环境循环音从需求走到 Wwise 和 UE
- 系统能否通过自动化 QA 与 Profile 诊断发现典型问题
- 系统能否以可追踪、可回滚方式完成一轮真实项目迭代

MVP 成功定义：至少打通 1 条完整链路（需求输入 -> 素材生成 -> 检测处理 -> Wwise 导入 -> UE 挂接 -> QA 检测），支持 3 类标准化资产（动作 SFX、UI 音效、简单环境循环），支持 1 套项目模板（动作游戏模板），QA 能自动识别至少 5 类常见问题。

### 1.2 总工期

- **8 个 Sprint，16 周**
- 每个 Sprint 为 2 周

### 1.3 里程碑对应关系

| 里程碑 | Sprint | 周次 | 核心目标 |
|--------|--------|------|----------|
| M1: 规则建制完成 | Sprint 1-2 | 第 1-4 周 | 基础架构就绪，规则/模板/映射库完成 |
| M2: 主链路可跑通 | Sprint 3-5 | 第 5-10 周 | 需求输入 -> 生成 -> Wwise -> UE -> 审批全链路打通 |
| M3: QA 闭环可用 | Sprint 6-7 | 第 11-14 周 | 自动化 QA + Profile 诊断 + 5 类问题自动识别 |
| M4: 内部试运行 | Sprint 8 | 第 15-16 周 | 真实功能域试跑 + 指标收集 + 复盘 |

### 1.4 团队角色分工

| 角色 | 缩写 | 职责范围 |
|------|------|----------|
| 产品经理 (PM) | PM | 需求优先级、验收标准、里程碑跟踪、试运行编排 |
| 音频设计师 (Audio Designer) | AD | Style Bible、Category Rules、QA 规则、审批标准 |
| 后端开发 (Backend Dev) | BE | 服务架构、数据模型、API、状态机、规则引擎、任务队列 |
| 音频工程师 (Audio Engineer) | AE | WAAPI 自动化、UE 挂接脚本、音频处理管线、Profile 抓取 |
| 前端开发 (Frontend Dev) | FE | 任务提交页、详情页、审批页、诊断页、后台配置页 |
| 测试工程师 (QA) | QA | 测试策略、用例设计、自动化测试、CI/CD 门禁 |

---

## 2. 里程碑定义

### M1: 规则建制完成（Sprint 1-2，第 1-4 周）

**目标描述**

系统基础架构搭建完毕，专业音频人员完成项目风格、规则、模板和流程建制。后台可管理所有规则配置，且规则版本可追溯。

**验收门禁（必须通过才能进入 M2）**

- [ ] 后端服务骨架可运行，Task CRUD 接口可用
- [ ] 数据库 ER 模型落地，所有核心表创建完毕
- [ ] 规则引擎框架可加载和执行规则（支持四级优先级）
- [ ] Style Bible v1 完成并入库
- [ ] 3 类 Category Rules（SFX、UI、Ambience Loop）完成并入库
- [ ] 动作游戏 Wwise 模板完成（Actor-Mixer Hierarchy、Bus 结构、Event 命名规则、Bank 分组策略）
- [ ] Mapping Dictionary v1 完成（动画名 -> Event 映射）
- [ ] QA 检测规则 v1 完成（5 类问题判定条件和阈值）
- [ ] 后台规则配置页可进行 CRUD 操作
- [ ] 单元测试框架搭建完毕，核心模块覆盖率 >= 50%

---

### M2: 主链路可跑通（Sprint 3-5，第 5-10 周）

**目标描述**

至少 1 条动作 SFX 任务可从"策划提交"走到"审批通过"，全程状态可追踪，产出物在 Wwise 和 UE 中可验证。

**验收门禁（必须通过才能进入 M3）**

- [ ] 策划可在任务提交页完成任务创建（含视频上传）
- [ ] 系统可自动生成 AudioIntentSpec（含置信度和待确认项）
- [ ] 系统可生成至少 3 个候选音频
- [ ] QC 可检测通过/失败并输出完整报告
- [ ] Wwise 中目标路径下存在 Sound 对象、Event、Bank
- [ ] UE 中目标 AnimMontage 上存在 AkEvent AnimNotify
- [ ] 审批功能可用（通过/拒绝，含审计日志）
- [ ] 素材版本可手动回滚
- [ ] 任务详情页可展示完整状态时间线
- [ ] 至少完成 1 次端到端集成测试

---

### M3: QA 闭环可用（Sprint 6-7，第 11-14 周）

**目标描述**

自动化 QA 可产出问题报告，诊断链路可对 5 类问题输出疑似根因，QA 报告可回溯到任务和 Wwise 对象。

**验收门禁（必须通过才能进入 M4）**

- [ ] 自动化跑测后可获取 Wwise Profile Capture 数据
- [ ] 至少能自动检测 5 类问题：Event 未触发、Voice 未创建、Voice 被 Kill、Bank 未加载、Media 缺失
- [ ] 诊断链路可对 5 类问题输出 root_cause_guess + evidence_refs
- [ ] QA 报告格式完整（问题 ID、时间点、类型、根因、建议修复）
- [ ] 诊断页可输入问题描述并输出诊断结果
- [ ] QA 步骤已集成进主链路状态机（UEBound -> QARun -> ReviewPending）
- [ ] 在模拟问题场景中，诊断根因命中率 >= 70%
- [ ] QA 误报率 <= 20%

---

### M4: 内部试运行（Sprint 8，第 15-16 周）

**目标描述**

选定一个真实功能域试跑，收集自动化率、通过率、人工介入点，输出 MVP 复盘报告。

**验收门禁（MVP 完成标准）**

- [ ] 完成至少 15 个真实任务的端到端试运行
- [ ] 输出量化指标报告（自动化成功率、QC 通过率、挂接正确率、QA 召回率）
- [ ] 标准化需求自动处理成功率达到可内部试用水平（建议 >= 60%）
- [ ] 输出 MVP 复盘报告和 Phase 2 优先级建议
- [ ] 全部 P0 功能通过验收标准

---

## 3. Sprint 详细计划

### Sprint 1（第 1-2 周）：基础架构与规则框架

**Sprint 目标：** 搭建项目工程骨架和规则引擎框架，启动音频建制工作。

**任务清单**

| 任务名称 | 负责角色 | 对应功能编号 | 前置依赖 | 产出物 | 验收标准 |
|----------|---------|-------------|---------|--------|---------|
| 搭建后端项目骨架（模块化单体架构） | BE | 基础设施 | 无 | gaming-audio-server 项目工程，含 8 个模块目录、FastAPI 入口、Docker Compose | 服务可启动，健康检查接口可访问 |
| 设计并创建数据库表结构 | BE | 基础设施 | 项目骨架 | PostgreSQL 全量 DDL + Alembic 迁移脚本 | 12 张核心表创建成功，ER 关系正确 |
| 实现 Task CRUD 接口 | BE | F-001 | 数据库表 | POST/GET/PATCH /api/v1/tasks | 可创建、查询、编辑任务；task_id 唯一 |
| 设计规则引擎框架 | BE | F-002 | 项目骨架 | Rule Service 模块，支持四级优先级、冲突记录 | 规则可加载、可执行、冲突可记录到 audit log |
| 搭建 Celery + Redis 任务队列 | BE | 基础设施 | 项目骨架 | Worker 进程可消费异步任务 | 测试任务可投递和消费 |
| 搭建 MinIO 文件存储 | BE | 基础设施 | 项目骨架 | MinIO 实例 + 上传/下载 SDK 封装 | 文件可上传和下载 |
| 音频负责人输出 Style Bible v1 | AD | 规则库 | 无 | Style Bible YAML/JSON 配置文件 | 包含听觉风格定义、参考作品、关键词库、禁用倾向 |
| 音频负责人输出 Category Rules v1（SFX） | AD | 规则库 | 无 | SFX Category Rule 配置 | 包含采样率/位深/声道/响度/频段/时长标准 |
| 搭建前端项目骨架 | FE | 基础设施 | 无 | Next.js 14 项目 + Ant Design + 路由框架 | 项目可启动，基础路由可访问 |
| 搭建测试框架 | QA | 基础设施 | 项目骨架 | pytest + Jest 框架 + CI 配置 | 可运行空测试套件 |

**Sprint 交付物**

- 可运行的后端服务骨架（含数据库、消息队列、文件存储）
- Task CRUD 接口
- 规则引擎框架 v0
- Style Bible v1
- SFX Category Rule v1
- 前端项目骨架
- 测试框架

**Sprint 风险提示**

- 数据库 ER 模型需要前期充分评审，后期修改成本高
- Style Bible 的质量直接影响后续所有 AI 生成效果，需音频负责人充分投入

---

### Sprint 2（第 3-4 周）：模板与映射建制

**Sprint 目标：** 完成所有规则/模板/映射库建制，后台配置页可用。

**任务清单**

| 任务名称 | 负责角色 | 对应功能编号 | 前置依赖 | 产出物 | 验收标准 |
|----------|---------|-------------|---------|--------|---------|
| 音频负责人输出 Category Rules v1（UI + Ambience） | AD | 规则库 | SFX Rule 完成 | UI 和 Ambience Loop Category Rule 配置 | 3 类规则完整覆盖技术标准 |
| 搭建 Wwise 动作游戏模板 | AD + AE | F-005 | 无 | Wwise 模板工程文件 | Actor-Mixer Hierarchy 完整、Bus 结构正确、命名规则可执行 |
| 定义 UE Mapping 规则 | AD + AE | F-008 | Wwise 模板 | Mapping Dictionary v1（动画名 -> Event 映射字典） | 覆盖常见动作动画命名模式 |
| 定义 QA 检测规则 v1 | AD + QA | F-010/F-011 | Category Rules | 5 类问题的判定条件和阈值配置 | 每类问题有明确的检测逻辑和通过/失败标准 |
| 实现规则 CRUD 接口 | BE | 规则库 | 规则引擎框架 | Style Bible/Category Rules/Template/Mapping 的 CRUD API | 规则可创建、查询、更新、版本化 |
| 实现命名规则引擎 | BE | F-005/F-006 | 规则引擎框架 | 命名规则解析和生成模块 | 给定 spec，可输出符合规则的 Event/对象命名 |
| 实现后台规则配置页 | FE | 配置后台 | 规则 CRUD 接口 | /admin/* 全部配置页面 | 可 CRUD Style Bible、Category Rules、Wwise 模板、Mapping Dictionary、QA 规则 |
| 实现审计日志写入框架 | BE | F-009 | 数据库表 | AuditLog 写入中间件 | 关键操作自动写入审计日志 |
| WAAPI 连接管理模块 | AE | F-006 | 项目骨架 | WAAPI 连接封装（长连接、心跳、重连） | 可连接 Wwise Authoring，调用 getInfo 成功 |
| 编写 Sprint 1-2 单元测试 | QA | 测试 | 各模块完成 | 规则引擎 + 状态机 + CRUD 接口测试用例 | 核心逻辑覆盖率 >= 50% |

**Sprint 交付物**

- 3 类完整 Category Rules
- Wwise 动作游戏模板
- Mapping Dictionary v1
- QA 检测规则 v1
- 后台规则配置页
- 审计日志框架
- WAAPI 连接模块

**Sprint 风险提示**

- Wwise 模板设计若不扎实，后续将放大工程结构问题，需音频专家充分评审
- Mapping Dictionary 的覆盖度依赖项目资源命名规范性

---

### Sprint 3（第 5-6 周）：需求输入与 Intent 生成

**Sprint 目标：** 策划可提交任务，系统可生成结构化 AudioIntentSpec。

**任务清单**

| 任务名称 | 负责角色 | 对应功能编号 | 前置依赖 | 产出物 | 验收标准 |
|----------|---------|-------------|---------|--------|---------|
| 实现任务提交页 UI | FE | F-001 | 前端骨架 + Task API | /tasks/create 页面 | 策划可在单页完成任务创建，含视频上传 |
| 实现文件上传服务（分片断点续传） | BE + FE | F-001 | MinIO | 基于 tus 协议的上传接口 + 前端 tus-js-client | 支持 500MB 视频上传，断点续传 |
| 实现需求结构化模块 | BE | F-002 | 规则引擎 + 规则库 | GenerateIntentSpec 接口 | 每个合法任务可生成 spec，含 confidence |
| 实现视频基础特征提取 | AE | F-002 | 项目骨架 | 视频时长/关键帧/基础节奏检测模块 | 可从视频提取 timing_points |
| 实现置信度计算与低置信度拦截 | BE | F-002 | 结构化模块 | SpecReviewPending 状态流转 | confidence < 0.6 自动暂停 |
| 实现任务状态机框架 | BE | F-009 | Task 模块 | 完整状态机（14 个状态 + 流转规则） | 非法状态流转被阻断 |
| 实现任务详情页 v0 | FE | F-009 | Task API | /tasks/:taskId 页面 + 状态时间线组件 | 可展示任务状态和基本信息 |
| 实现 SSE 实时推送框架 | BE + FE | 基础设施 | 项目骨架 | SSE 事件流接口 + 前端 EventSource | 状态变更可实时推送到前端 |
| 编写需求输入模块测试用例 | QA | 测试 | F-001/F-002 完成 | 7 个输入模块用例 + 8 个 Intent 生成用例 | 全部通过 |

**Sprint 交付物**

- 任务提交页（含视频上传）
- GenerateIntentSpec 接口
- 视频基础特征提取模块
- 任务状态机
- 任务详情页 v0
- SSE 实时推送

**Sprint 风险提示**

- 视频理解能力不足时需启用降级模式（仅凭策划填写的结构化字段生成 Intent）
- 置信度计算逻辑需要多轮调优，初期可先设为简单规则

---

### Sprint 4（第 7-8 周）：音频生成与 Wwise 导入

**Sprint 目标：** 系统可生成候选音频、通过 QC、导入 Wwise 并生成 Bank。

**任务清单**

| 任务名称 | 负责角色 | 对应功能编号 | 前置依赖 | 产出物 | 验收标准 |
|----------|---------|-------------|---------|--------|---------|
| 对接 AI 音频生成服务 | AE + BE | F-003 | Intent 生成模块 | GenerateAudioCandidates 接口 | 每任务生成 >= 3 个候选，每个有版本号和参数记录 |
| 实现 Prompt 管理模块 | AE | F-003 | Style Bible + Category Rules | Prompt 拼装和版本化存储 | Prompt 由 Spec + Style Bible + Category Rules 自动拼装 |
| 实现音频后处理管线 | AE | F-004 | 音频生成 | 切头尾 + 淡入淡出 + 响度标准化 + 格式转换模块 | 输出 48kHz/24-bit WAV，响度在目标区间 |
| 实现 QC 检测模块 | AE + BE | F-004 | 后处理管线 | RunAudioQC 接口 + QcReport 输出 | 报告含 6 项指标，QC 不通过阻断后续流程 |
| 实现 Wwise 对象创建 | AE | F-005/F-006 | WAAPI 连接 + Wwise 模板 | Actor-Mixer/Container/Sound 创建模块 | 对象创建在模板预期路径下 |
| 实现 Wwise 音频导入 | AE | F-006 | 对象创建模块 | ak.wwise.core.audio.import 封装 | 导入成功率 >= 95% |
| 实现 Event 创建和 Action 配置 | AE | F-006 | 对象创建模块 | Event + Play Action 创建 | Event 命名符合规则模板 |
| 实现 SoundBank 生成 | AE | F-007 | Event 创建 | BuildBank 接口 | Bank 文件实际生成，日志可追踪 |
| 实现候选试听组件 | FE | F-003/F-004 | 音频 API | AudioComparePlayer 组件 + 波形可视化 | 可试听/对比 3 个候选，显示波形和 QC 结果 |
| 实现审计日志贯穿 | BE | F-009 | 审计框架 | 每步操作写入 AuditLog | 从 Spec 生成到 Bank 生成每步有日志 |
| 编写音频生成 + Wwise 模块测试用例 | QA | 测试 | F-003~F-007 完成 | 8 个音频模块 + 8 个 Wwise 模块用例 | 全部通过 |

**Sprint 交付物**

- AI 音频生成集成
- 音频后处理管线
- QC 检测模块 + QcReport
- Wwise 自动化全套（对象创建 + 导入 + Event + Bank）
- 候选试听组件

**Sprint 风险提示**

- AI 生成服务可用性和质量是主要风险，需准备降级方案（如使用本地 AudioCraft）
- WAAPI 调用需在有 Wwise Authoring 的环境中测试，CI 环境需配置
- 单次 WAAPI 调用延迟约 10-50ms，批量操作需使用嵌套创建优化

---

### Sprint 5（第 9-10 周）：UE 挂接与审批闭环

**Sprint 目标：** UE AnimNotify 自动挂接可用，审批闭环打通，完成端到端集成测试。

**任务清单**

| 任务名称 | 负责角色 | 对应功能编号 | 前置依赖 | 产出物 | 验收标准 |
|----------|---------|-------------|---------|--------|---------|
| 实现 UE AnimNotify 自动挂接 | AE | F-008 | Wwise Event 已创建 + Mapping Dictionary | BindInUE 接口 + Python Editor 脚本 | 对命名规范的动画资源，匹配成功率 >= 90% |
| 实现 UnresolvedBindingQueue | BE + AE | F-008 | 挂接模块 | 未匹配项进入待审队列 | 100% 未匹配项进入队列，不静默跳过 |
| 实现审批流程 | BE | F-009 | 状态机 | ReviewPending -> Approved/Rejected 流转 + ReviewRecord | 审批操作后状态正确流转，有日志 |
| 实现审批页面 | FE | F-009 | 审批 API | /tasks/:taskId/review 页面 | 可试听候选、查看 manifest、通过/拒绝 |
| 实现素材版本手动回滚 | BE | F-009/F-015 | 版本快照 | 回滚接口 + RollbackPoint 记录 | 拒绝后可回退素材版本，有日志 |
| 实现任务详情页完整版 | FE | F-009 | 全链路 API | 详情页 Tab：概览/候选/Wwise/UE/QA/审计 | 全部 Tab 可展示对应数据 |
| UE 资产版本控制集成 | AE | F-008 | 挂接模块 | 修改前快照 + 原子提交 + Checkout 管理 | 资产修改可追踪、可回滚 |
| 端到端集成测试 | QA + 全员 | 全链路 | 全部 P0 功能 | 端到端测试报告 | 至少 1 个动作 SFX 任务从提交走到审批通过 |
| 编写 UE 挂接 + 审批模块测试用例 | QA | 测试 | F-008/F-009 完成 | 7 个 UE 模块 + 8 个审批模块用例 | 全部通过 |

**Sprint 交付物**

- UE AnimNotify 自动挂接
- 审批流程和页面
- 回滚能力 v0
- 任务详情页完整版
- 端到端集成测试通过

**Sprint 风险提示**

- UE Python Editor Scripting 对 AnimNotify 操作可能需要 C++ 辅助封装
- 不同 UE 版本的 AnimNotify API 可能存在差异
- 端到端测试需要 Wwise + UE 环境同时可用

---

### Sprint 6（第 11-12 周）：自动化 QA

**Sprint 目标：** 自动化跑测后可获取 Profile 数据，系统可自动检测 5 类常见问题。

**任务清单**

| 任务名称 | 负责角色 | 对应功能编号 | 前置依赖 | 产出物 | 验收标准 |
|----------|---------|-------------|---------|--------|---------|
| 对接自动化跑测系统 | AE + QA | F-010 | UE 挂接完成 | 跑测编排脚本 + 场景驱动层 | 可自动驱动游戏场景执行 |
| 实现 Wwise Profile 自动采集 | AE | F-010 | WAAPI 连接 | WAAPI profiler capture 封装 | 可自动启动/停止 Capture，导出 .prof 文件 |
| 实现 Profile 数据解析 | AE + BE | F-010 | Profile 采集 | Voice/Event/RTPC/Bus 状态提取脚本 | 提取的结构化数据可按时间/Event/对象检索 |
| 实现 5 类问题自动检测 | BE + AE | F-010 | Profile 解析 + QA 规则 | RunAudioQA 接口 | 检测 Event 未触发/Voice 未创建/Voice 被 Kill/Bank 未加载/Media 缺失 |
| 实现 QA 报告生成 | BE | F-010 | 问题检测 | QaReport + QaIssue[] 输出 | 报告含问题 ID、时间点、类型、关联对象 |
| 集成 QA 步骤到主链路状态机 | BE | F-010 | 状态机 | UEBound -> QARun -> ReviewPending 流转 | QA 完成后自动进入审批 |
| 实现 QA 报告展示页 | FE | F-010 | QA API | 任务详情 QA Tab | 可查看问题统计、问题列表、证据 |
| 构建诊断基准测试集 | QA | 测试 | 问题检测模块 | 每类问题 5+ 个模拟场景 | 场景可通过开关启用/禁用 |
| 编写 QA 模块测试用例 | QA | 测试 | F-010 完成 | 10 个 QA 诊断用例 | 全部通过 |

**Sprint 交付物**

- 自动化跑测集成
- Profile 自动采集和解析
- 5 类问题自动检测
- QA 报告生成和展示
- 诊断基准测试集

**Sprint 风险提示**

- Profile 数据获取依赖 Wwise Profiler Remote Connection 在游戏运行时可用
- 自动化跑测环境搭建可能耗时，需提前准备
- Profile 数据格式可能因 Wwise 版本不同而有差异

---

### Sprint 7（第 13-14 周）：问题诊断

**Sprint 目标：** 诊断链路可对 5 类问题输出疑似根因和修复建议。

**任务清单**

| 任务名称 | 负责角色 | 对应功能编号 | 前置依赖 | 产出物 | 验收标准 |
|----------|---------|-------------|---------|--------|---------|
| 实现诊断反查链路 | BE + AE | F-011 | Profile 解析 + QA 规则 | DiagnoseIssue 接口 | 支持 5 类问题的根因定位 |
| 实现诊断决策树 | BE | F-011 | 诊断链路 | Event->Voice->Volume->Bus->Bank->Media 逐层检查 | 按优先级逐层排查，输出第一个命中的根因 |
| 实现问题诊断页 | FE | F-011 | DiagnoseIssue API | /diagnosis/new + /diagnosis/:id 页面 | 可输入问题描述，可视化诊断链路和根因 |
| 完善 QA 规则集 | AD + AE | F-010/F-011 | QA 规则 v1 | 完善 RTPC 异常、Bus Mute、映射错误等检测规则 | 覆盖 Event 未触发/Voice 被 Kill/RTPC 异常/Bank 未加载/Media 缺失全部 5 类 |
| 实现通知系统 | FE + BE | 基础设施 | SSE 框架 | 通知推送 + 铃铛图标 + 通知中心页 | 审批请求、任务完成等事件可推送 |
| QA 闭环测试 | QA + 全员 | 测试 | 全 QA 链路 | 诊断准确率报告 | 模拟 5 类已知问题，根因命中率 >= 70% |
| 回归测试全量执行 | QA | 测试 | 全部模块 | 完整回归报告 | 所有已有测试用例通过 |
| 性能基准测试 | QA | 测试 | 全链路 | 性能报告 | 单任务端到端 <= 15 分钟，诊断 <= 60 秒 |

**Sprint 交付物**

- 诊断反查链路和决策树
- 问题诊断页
- 完善的 QA 规则集
- 通知系统
- 诊断准确率报告
- 性能基准报告

**Sprint 风险提示**

- 诊断准确率高度依赖 Profile 数据质量和映射关系完整度
- 决策树的规则可能需要多轮调优

---

### Sprint 8（第 15-16 周）：内部试运行

**Sprint 目标：** 在真实功能域上完成端到端试运行，输出 MVP 复盘报告。

**任务清单**

| 任务名称 | 负责角色 | 对应功能编号 | 前置依赖 | 产出物 | 验收标准 |
|----------|---------|-------------|---------|--------|---------|
| 选定试运行功能域和任务清单 | PM + AD | 试运行 | M3 完成 | 试运行任务清单（建议：1 个 Boss 战 + 10 个普通动作 + 5 个 UI） | 覆盖 3 类资产类型 |
| 策划批量提交需求 | 策划 | 试运行 | 任务清单 | 15-20 个真实任务 | 按正常工作流提交 |
| 全链路自动执行 | 系统 | 全链路 | 任务提交 | 运行日志 | 记录各环节成功率和耗时 |
| 音频负责人审批全部产出 | AD | 试运行 | 链路完成 | 审批记录 | 全部任务完成审批 |
| QA 自动化测试 + 人工验证 | QA | 试运行 | 审批完成 | QA 报告 | 自动化 + 人工双重验证 |
| 收集量化指标 | PM | 试运行 | 全部完成 | 指标汇总（成功率/通过率/正确率/召回率/介入点） | 数据完整 |
| Bug 修复和热调 | BE + AE + FE | 修复 | 试运行反馈 | 修复补丁 | 阻断级别 Bug 全部修复 |
| 输出 MVP 复盘报告 | PM | 试运行 | 指标汇总 | MVP 复盘报告 + Phase 2 优先级建议 | 含成功/失败/改进点分析 |
| CI/CD 门禁完善 | QA | 基础设施 | 全部测试 | 完整 CI/CD 质量门禁 | 代码/功能/部署三层门禁可用 |

**Sprint 交付物**

- 15-20 个真实任务的试运行记录
- 量化指标报告
- MVP 复盘报告
- Phase 2 优先级建议
- 完善的 CI/CD 门禁

**Sprint 风险提示**

- 真实数据可能暴露前期未覆盖的边界场景
- 试运行期间需预留 Bug 修复时间（建议 Sprint 8 前半段试跑，后半段修复和复盘）

---

## 4. 功能开发顺序

### 4.1 按层级排列的功能执行顺序

```
L0 基础设施层（Sprint 1-2）
├── F-001 需求提交
└── F-002 需求结构化

L1 生成层（Sprint 3-4）
├── F-003 音频候选生成
└── F-004 基础后处理与 QC

L2 Wwise 层（Sprint 4）
├── F-005 Wwise 模板派生
├── F-006 Wwise 导入与对象创建
└── F-007 SoundBank 生成

L3 UE 层（Sprint 5）
├── F-008 UE AnimNotify 自动挂接
└── F-009 任务追踪与审批（贯穿 Sprint 1-5，Sprint 5 闭环）

L4 QA 层（Sprint 6-7）
├── F-010 基础自动化 QA
└── F-011 基础诊断

L5 扩展层（Phase 2）
├── F-012 UI 批量任务导入（P1）
├── F-013 环境循环音专用处理（P1）
├── F-014 弱语义 UE 匹配（P1）
└── F-015 自动回滚（P1）

L6 增值层（Phase 2+）
├── F-016 自动修复建议（P2）
└── F-017 批量任务面板（P2）
```

### 4.2 功能依赖关系图

```
F-001（需求提交）
  └──> F-002（需求结构化）
         ├──> F-003（音频候选生成）
         │      └──> F-004（基础后处理与 QC）
         │             └──> F-006（Wwise 导入与对象创建）
         │                    └──> F-007（SoundBank 生成）
         │                           └──> F-008（UE AnimNotify 自动挂接）
         │                                  └──> F-010（基础自动化 QA）
         │                                         └──> F-011（基础诊断）
         └──> F-005（Wwise 模板派生）──> F-006

F-009（任务追踪与审批）贯穿全流程，从 F-001 开始伴随每个模块

F-012（UI 批量导入）──> F-001（扩展）
F-013（环境循环音处理）──> F-004（扩展）
F-014（弱语义 UE 匹配）──> F-008（增强）
F-015（自动回滚）──> F-009（增强）
F-016（自动修复建议）──> F-011（增强）
F-017（批量任务面板）──> F-009（增强）
```

### 4.3 P0/P1/P2 功能对照表

| 优先级 | 功能编号 | 功能名称 | 所属层级 | 计划 Sprint | 状态 |
|--------|---------|---------|---------|------------|------|
| **P0** | F-001 | 需求提交 | L0 | Sprint 1-3 | MVP |
| **P0** | F-002 | 需求结构化 | L0 | Sprint 3 | MVP |
| **P0** | F-003 | 音频候选生成 | L1 | Sprint 4 | MVP |
| **P0** | F-004 | 基础后处理与 QC | L1 | Sprint 4 | MVP |
| **P0** | F-005 | Wwise 模板派生 | L2 | Sprint 4 | MVP |
| **P0** | F-006 | Wwise 导入与对象创建 | L2 | Sprint 4 | MVP |
| **P0** | F-007 | SoundBank 生成 | L2 | Sprint 4 | MVP |
| **P0** | F-008 | UE AnimNotify 自动挂接 | L3 | Sprint 5 | MVP |
| **P0** | F-009 | 任务追踪与审批 | L3 | Sprint 1-5 | MVP |
| **P0** | F-010 | 基础自动化 QA | L4 | Sprint 6 | MVP |
| **P0** | F-011 | 基础诊断 | L4 | Sprint 7 | MVP |
| **P1** | F-012 | UI 批量任务导入 | L5 | Phase 2 | 延期 |
| **P1** | F-013 | 环境循环音专用处理 | L5 | Phase 2 | 延期 |
| **P1** | F-014 | 弱语义 UE 匹配 | L5 | Phase 2 | 延期 |
| **P1** | F-015 | 自动回滚 | L5 | Phase 2 | 延期 |
| **P2** | F-016 | 自动修复建议 | L6 | Phase 2+ | 延期 |
| **P2** | F-017 | 批量任务面板 | L6 | Phase 2+ | 延期 |

---

## 5. 关键路径分析

### 5.1 主链路关键路径（不可并行、不可跳过）

以下环节构成端到端关键路径，任何一个延迟都会直接影响整体进度：

```
Sprint 1: 数据库表结构 -> Task CRUD
Sprint 2: 规则引擎 -> Wwise 模板
Sprint 3: 需求提交 -> Intent 生成 -> 状态机
Sprint 4: 音频生成 -> QC -> Wwise 导入 -> Event/Bank
Sprint 5: UE 挂接 -> 审批闭环 -> 端到端集成测试
Sprint 6: Profile 采集 -> 问题检测
Sprint 7: 诊断链路 -> 诊断准确率验证
Sprint 8: 试运行 -> 复盘
```

**最长路径为 Sprint 3-5 的主链路串联**：Intent 生成 -> 音频生成 -> QC -> Wwise 导入 -> Bank -> UE 挂接 -> 审批。这 6 周是风险最高的阶段。

### 5.2 并行工作机会

| 时间段 | 可并行的工作流 |
|--------|---------------|
| Sprint 1-2 | 后端架构搭建 ‖ 音频规则建制 ‖ 前端项目骨架 ‖ 测试框架 |
| Sprint 3 | Intent 生成模块（BE）‖ 任务提交页（FE）‖ 视频特征提取（AE）|
| Sprint 4 | 音频生成+QC（AE）‖ Wwise 模板派生（BE）‖ 候选试听组件（FE）|
| Sprint 5 | UE 挂接（AE）‖ 审批页面（FE）‖ 任务详情页完整版（FE）|
| Sprint 6 | Profile 采集（AE）‖ 问题检测规则（BE）‖ QA 报告页面（FE）|
| Sprint 7 | 诊断链路（BE+AE）‖ 诊断页面（FE）‖ 通知系统（FE+BE）|

### 5.3 时间缓冲建议

| 环节 | 建议缓冲 | 理由 |
|------|---------|------|
| AI 音频生成集成（Sprint 4） | +3 天 | AI 服务可用性不确定，可能需要切换备选方案 |
| WAAPI 自动化（Sprint 4） | +2 天 | 需在有 Wwise 的环境中调试，首次集成可能遇到兼容性问题 |
| UE 挂接（Sprint 5） | +3 天 | AnimNotify Python 操作可能需要 C++ 辅助封装 |
| Profile 数据采集（Sprint 6） | +3 天 | 依赖自动化跑测环境就绪和 Wwise Profiler 远程连接 |
| 试运行（Sprint 8） | 预留 Sprint 后半段修复 | 真实数据可能暴露边界问题 |

---

## 6. 技术实施顺序

### 6.1 后端实施顺序

```
第 1 步: 项目骨架搭建
        ├── FastAPI + Python 3.11+ 项目结构（模块化单体）
        ├── 8 个模块目录创建（task/rule/intent/audio_pipeline/wwise/ue_binding/qa/audit）
        ├── Docker Compose（PostgreSQL + Redis + MinIO）
        └── 健康检查接口

第 2 步: 数据模型落地
        ├── SQLAlchemy 2.0 ORM 模型定义（12 张表）
        ├── Alembic 迁移脚本
        └── 索引策略实施

第 3 步: API 层搭建
        ├── RESTful 路由设计（/api/v1/*）
        ├── Pydantic v2 请求/响应模型
        ├── JWT 认证 + RBAC 权限（策划/音频/QA/管理员）
        └── 统一错误处理和响应格式

第 4 步: 状态机实现
        ├── 14 个状态定义 + 流转规则
        ├── 状态变更事件发布（进程内事件总线）
        └── 非法流转阻断

第 5 步: 规则引擎实现
        ├── 四级优先级（Task Override > Category > Template > Project）
        ├── 冲突检测和记录
        ├── 规则版本化管理
        └── 规则 CRUD 接口

第 6 步: 各模块集成
        ├── Intent 生成模块（规则匹配 + 置信度计算）
        ├── Audio Pipeline 编排（Celery 异步链）
        ├── Wwise 集成适配器（WAAPI 调用封装）
        ├── UE Binding 适配器（Python 脚本调度）
        ├── QA 检测模块（Profile 解析 + 规则检查）
        ├── 诊断模块（决策树 + 根因定位）
        └── 审批回滚模块（ReviewRecord + RollbackPoint）
```

### 6.2 前端实施顺序

```
第 1 步: 项目骨架
        ├── Next.js 14 (App Router) + TypeScript strict
        ├── Ant Design 5 + ProComponents
        ├── TanStack Query v5 + Zustand
        ├── 路由结构和 Layout 搭建
        └── RBAC 路由守卫

第 2 步: 任务提交页（Sprint 3）
        ├── TaskBasicInfoForm（资源类型/场景语义/播放方式）
        ├── TagSelector（多标签选择）
        ├── AssetUploader（tus 分片上传 + 进度条）
        ├── AssetPreviewPanel（视频预览）
        └── 表单校验和提交

第 3 步: 任务详情页（Sprint 3-5）
        ├── TaskStatusTimeline（状态时间线组件）
        ├── IntentSpecPanel（Spec 展示 + 低置信度高亮）
        ├── CandidatesTab（AudioComparePlayer + WaveformViewer）
        ├── WwiseTab（对象树 + Event 列表 + Bank 信息）
        ├── UEBindingTab（挂接表 + 未解决队列）
        └── AuditLogTab（操作日志时间线）

第 4 步: 审批页（Sprint 5）
        ├── ReviewSummary（任务摘要 + 试听 + QC 结果）
        ├── ManifestViewer（Wwise/UE 改动摘要）
        └── ReviewForm（通过/拒绝 + 备注）

第 5 步: 诊断页（Sprint 7）
        ├── DiagnosisForm（时间点 + 上下文 + 问题描述）
        ├── DiagnosisChain（链路可视化 - 逐层检查结果）
        ├── RootCauseCard（根因卡片）
        └── SuggestedActionsPanel（修复建议）

第 6 步: 后台配置页（Sprint 2，持续完善）
        ├── StyleBibleEditor（富文本 + 关键词管理）
        ├── CategoryRulesTable（ProTable CRUD + 版本对比）
        ├── WwiseTemplateTree（树形模板编辑）
        ├── UEMappingTable（映射关系表 + 正则编辑）
        └── QARulesEditor（条件 + 阈值 + 动作）
```

### 6.3 音频工程实施顺序

```
第 1 步: WAAPI 连接（Sprint 2）
        ├── WebSocket 长连接 + 心跳 + 自动重连
        ├── ak.wwise.core.getInfo 验证
        └── 连接管理封装

第 2 步: 对象创建（Sprint 4）
        ├── Actor-Mixer Hierarchy 路径检查/创建
        ├── Random Container 创建
        ├── Sound SFX 创建
        └── 嵌套创建优化（减少调用次数）

第 3 步: 音频导入（Sprint 4）
        ├── ak.wwise.core.audio.import 封装
        ├── 导入前校验（采样率/位深/声道/完整性）
        ├── 增量导入（查-补策略）
        └── Source 文件归档

第 4 步: Event/Bank（Sprint 4）
        ├── Event 创建 + Play Action 配置
        ├── SoundBank 关联（setInclusions）
        ├── Bank 生成（ak.wwise.core.soundbank.generate）
        └── 生成结果验证

第 5 步: UE 挂接（Sprint 5）
        ├── Python Editor Scripting 环境配置
        ├── 动画资源搜索和加载
        ├── AnimNotify 创建和写入
        ├── AkComponent 绑定（持续声音）
        └── 资产版本控制集成

第 6 步: Profile 抓取（Sprint 6）
        ├── ak.wwise.core.profiler.startCapture/stopCapture
        ├── .prof 文件导出
        ├── Voice/Event/RTPC/Bus 状态提取
        └── 结构化数据存储

第 7 步: 诊断（Sprint 7）
        ├── 诊断决策树实现
        ├── 时间点 -> Profile Capture 定位
        ├── 逐层检查（Event -> Voice -> Volume -> Bus -> Bank -> Media）
        └── 根因输出 + 证据引用
```

### 6.4 音频规则实施顺序

```
第 1 步: Style Bible（Sprint 1）
        ├── 项目听觉风格定义（一句话定位 + 美学支柱）
        ├── 参考作品列表
        ├── 关键词库（正面/负面）
        ├── 禁用倾向列表
        └── 审批并入库

第 2 步: Category Rules（Sprint 1-2）
        ├── SFX 规则：48kHz/24-bit/单声道/-18 LUFS/频段标准/时长范围
        ├── UI 规则：48kHz/24-bit/单声道/-22 LUFS/短时长/清晰瞬态
        ├── Ambience Loop 规则：48kHz/24-bit/立体声/-24 LUFS/循环标准
        └── 审批并入库

第 3 步: Wwise 模板（Sprint 2）
        ├── Actor-Mixer Hierarchy 结构（Combat/UI/Ambience 分层）
        ├── Master-Mixer / Bus 结构（SFX_Bus/UI_Bus/Amb_Bus）
        ├── Event 命名规则（Play_<Category>_<Character>_<Action>）
        ├── SoundBank 分组策略（按功能域切分）
        └── Conversion Setting 推荐配置

第 4 步: Mapping Dictionary（Sprint 2）
        ├── 动画名 -> Event 名映射规则
        ├── 正则匹配模式定义
        ├── 角色类别 -> 音频语义映射
        └── 示例数据填充

第 5 步: QA 规则（Sprint 2，Sprint 7 完善）
        ├── Event 未触发检测规则（时间窗口 +/- 200ms）
        ├── Voice 被 Kill 检测规则（生存时间 < 预期 20%）
        ├── RTPC 拉零检测规则（值在静音映射区间）
        ├── Bank 未加载检测规则（Load/Unload 记录交叉比对）
        └── Media 缺失检测规则（Media not found 记录）
```

### 6.5 测试实施顺序

```
第 1 步: 单元测试框架（Sprint 1）
        ├── pytest（后端）+ Jest（前端）
        ├── 覆盖率工具配置（coverage.py + istanbul）
        ├── 测试目录结构
        └── CI 集成（每次 PR 运行）

第 2 步: 集成测试（Sprint 2-5 逐步增加）
        ├── 模块间接口测试（Task -> Intent -> Audio -> Wwise -> UE）
        ├── WAAPI 集成测试（需 Wwise 环境）
        ├── UE Editor 脚本集成测试（需 UE 环境）
        └── 异常流覆盖

第 3 步: E2E 测试（Sprint 5）
        ├── 动作 SFX 完整链路
        ├── 审批拒绝与回滚
        └── 状态机完整流转

第 4 步: QA 自动化（Sprint 6-7）
        ├── 诊断基准测试集（每类问题 5+ 模拟场景）
        ├── 诊断准确率/召回率验证
        └── 问题场景开关管理

第 5 步: CI/CD 门禁（Sprint 7-8）
        ├── 代码质量门禁（Lint + Type Check + Coverage >= 85%）
        ├── 功能质量门禁（单元 100% + 集成 >= 95% + E2E >= 95%）
        ├── 冒烟测试（每次合入 main）
        └── 部署前检查清单
```

---

## 7. 验收标准总表

### 7.1 P0 功能量化验收标准

| 功能 | 验收项 | 量化标准 |
|------|--------|---------|
| **F-001 需求提交** | 必填校验 | 缺失任一必填字段时提交被阻止并提示 |
| | task_id 唯一性 | 100 次连续创建不产生重复 ID |
| | 素材可读性 | 30 秒内返回可读/不可读状态；支持 mp4/mov/avi，上限 500MB |
| | 响应时间 | 点击提交到 task_id 返回 <= 3 秒（不含上传） |
| **F-002 需求结构化** | Spec 生成率 | 100% 合法任务可生成 AudioIntentSpec |
| | 置信度标注 | 每个 Spec 含 confidence 字段（0.0-1.0）|
| | 低置信度拦截 | confidence < 0.6 自动进入 SpecReviewPending |
| | unresolved 标记 | 无法确定的字段标注字段名和原因 |
| **F-003 音频生成** | 候选数量 | 每任务 >= 3 个候选 |
| | 版本信息 | 每候选含 candidate_id/version/source_model/generation_params |
| | 生成耗时 | 单任务 3 候选 <= 5 分钟（SFX） |
| | 失败可重试 | 失败后状态为 AudioGenerationFailed，支持重新触发 |
| **F-004 后处理与 QC** | 切头尾 | < -60dBFS 超过 50ms 的头尾自动切除 |
| | 响度标准化 | SFX 输出 -18 LUFS +/- 2 LU |
| | QC 报告完整性 | 含 peak/loudness/spectrum/head_tail/format/qc_status |
| | QC 阻断 | 全部候选不通过时阻止进入 Wwise |
| | 格式合规 | 输出 48kHz / 24-bit WAV |
| **F-005 Wwise 模板派生** | 路径确定性 | 相同 type + scene 派生到相同 hierarchy 路径 |
| | manifest 完整性 | 含 object_type/object_path/event_name/bus_name/bank_name |
| | 模板覆盖 | 覆盖 SFX/UI/Ambience 三类 |
| **F-006 Wwise 导入** | 导入成功率 | >= 95%（Wwise 环境正常前提下）|
| | 对象可验证 | WAAPI 查询确认对象存在于预期路径 |
| | 命名合规 | Event 命名符合规则模板（正则可校验） |
| | 失败记录 | 日志含失败路径、错误码、错误信息 |
| **F-007 SoundBank** | Bank 可生成 | 输出 .bnk 文件 |
| | Bank 可加载 | UE 中可正常 Load |
| | 日志可追踪 | build log 含 Bank 名/Event 数/耗时/状态 |
| **F-008 UE 挂接** | 强规则匹配率 | 命名规范资源匹配成功率 >= 90% |
| | 挂接可验证 | AnimMontage 中可查到对应 AkEvent Notify |
| | unresolved 处理 | 100% 未匹配项进入队列 |
| | manifest 输出 | 含 target_asset_path/event_name/confidence |
| **F-009 追踪审批** | 状态完整性 | 详情页显示完整状态时间线 + 时间戳 |
| | 审计日志 | 每个关键步骤至少 1 条 audit log |
| | 审批功能 | 可执行通过/拒绝，状态正确流转 |
| | 回滚能力 | 素材可回退到上一版本，有日志 |
| **F-010 自动化 QA** | Profile 获取 | 获取成功率 >= 80% |
| | 问题检测 | 检测 5 类问题（Event 未触发/Voice 未创建/Voice 被 Kill/Bank 未加载/Media 缺失）|
| | 报告格式 | 含 qa_issue_id/timestamp/issue_type/related_event/related_actor |
| | 误报率 | <= 20% |
| **F-011 基础诊断** | 诊断覆盖 | 5 类问题的根因定位 |
| | 诊断输出 | 每次输出 root_cause_guess + evidence_refs |
| | 诊断耗时 | <= 60 秒 |
| | 诊断准确率 | 已知问题场景中根因命中率 >= 70% |

### 7.2 里程碑级验收标准

| 里程碑 | 核心验收标准 |
|--------|-------------|
| M1 | 后台可管理 5 类配置（Style Bible/Category Rules/Wwise 模板/Mapping/QA 规则），规则版本可追溯 |
| M2 | 至少 1 条动作 SFX 任务端到端跑通，产出物在 Wwise 和 UE 中可验证 |
| M3 | 自动化 QA 可产出问题报告，诊断链路命中率 >= 70%，误报率 <= 20% |
| M4 | 15+ 真实任务完成试运行，输出量化指标和复盘报告 |

### 7.3 MVP 整体成功标准

| 维度 | 成功标准 |
|------|---------|
| 链路打通 | 需求输入 -> 素材生成 -> QC -> Wwise 导入 -> UE 挂接 -> QA 检测完整闭环 |
| 资产覆盖 | 支持动作 SFX、UI 音效、简单环境循环 3 类 |
| 模板覆盖 | 动作游戏模板 1 套可用 |
| 自动化率 | 标准化需求自动处理成功率 >= 60% |
| QA 能力 | 自动识别 >= 5 类常见问题 |
| 可追踪性 | 每个任务有完整状态时间线和审计日志 |
| 可回滚性 | 素材版本可手动回滚 |

---

## 8. 风险登记与缓解计划

### 8.1 高风险项

| 编号 | 风险项 | 影响范围 | 概率 | 影响 | 缓解措施 | 降级方案 |
|------|--------|---------|------|------|---------|---------|
| R-01 | AI 音频生成质量不稳定 | F-003, 整体信任度 | 高 | 高 | 1. 准备多个生成服务（ElevenLabs + Stable Audio + AudioCraft）；2. Prompt 模板可配置可调优；3. 生成 3 候选取最优 | 使用预置音效素材库作为临时替代，手动上传音效走后续自动化流程 |
| R-02 | 视频理解能力不足 | F-002, Spec 准确率 | 高 | 中 | 1. MVP 视频理解限定为时长/关键帧/基础节奏；2. 策划显式提供标签和语义字段 | 降级模式：仅凭策划填写的结构化字段生成 Intent，不依赖视频分析 |
| R-03 | UE 挂接兼容性 | F-008 | 中 | 高 | 1. 优先 Python Editor Scripting；2. 为 AnimNotify 操作准备 C++ 辅助封装；3. 提前在目标 UE 版本上验证 | 生成"待手动绑定"清单，由音频 TA 批量确认 |

### 8.2 中风险项

| 编号 | 风险项 | 影响范围 | 概率 | 影响 | 缓解措施 | 降级方案 |
|------|--------|---------|------|------|---------|---------|
| R-04 | Wwise 版本兼容性 | F-005~F-007 | 中 | 中 | 1. 前置检查 Wwise 版本；2. WAAPI 调用封装层隔离版本差异；3. Undo Group 保护 | 对不兼容的 API 调用记录错误并进入人工处理队列 |
| R-05 | Profile 数据获取不稳定 | F-010/F-011 | 中 | 中 | 1. WAAPI profiler capture 封装含重试；2. 支持手动上传 .prof 文件 | 标记 ProfileUnavailable，允许人工补充定位信息 |
| R-06 | 项目资源命名不规范 | F-008 UE 匹配率 | 中 | 中 | 1. 强规则匹配支持正则模式；2. Mapping Dictionary 可持续扩展 | 低匹配率时全部进入 unresolved queue 人工处理 |
| R-07 | 自动化跑测环境搭建耗时 | F-010 进度 | 中 | 中 | Sprint 4 即开始准备跑测环境，不等到 Sprint 6 | 先用手动触发代替自动化编排 |
| R-08 | Wwise 模板设计不合理 | 全链路 | 低 | 高 | 音频专家充分评审模板，Sprint 2 结束时做模板评审会 | 发现问题后 Sprint 3-4 可快速迭代模板 |

### 8.3 通用缓解措施

- **每个外部系统交互都有适配器层隔离**，可快速切换实现
- **所有异步任务都有超时、重试和失败记录**
- **所有关键操作都有审计日志**，问题可追溯
- **Sprint 8 预留 Bug 修复时间**，不排满

---

## 9. 依赖清单

### 9.1 外部依赖

| 依赖项 | 用途 | 就绪时间要求 | 负责人 | 状态 |
|--------|------|-------------|--------|------|
| Wwise Authoring Application 许可 | WAAPI 自动化开发和测试 | Sprint 1 开始前 | AE | 待确认 |
| Wwise 版本号确认 | 确保模板和 WAAPI 兼容 | Sprint 1 开始前 | AE | 待确认 |
| Unreal Engine 版本号确认 | 确保 Python Scripting 和插件兼容 | Sprint 1 开始前 | AE | 待确认 |
| Wwise UE Integration Plugin 版本 | UE 挂接依赖 | Sprint 4 开始前 | AE | 待确认 |
| AI 音频生成 API 账号 | 音频候选生成 | Sprint 3 开始前 | BE | 待确认 |
| 多模态大模型 API 账号（GPT-4o/Gemini） | 视频理解 | Sprint 3 开始前 | BE | 待确认 |
| 服务器/开发机（含 GPU，如需本地生成） | 音频生成和视频分析 | Sprint 1 开始前 | 运维 | 待确认 |

### 9.2 内部依赖

| 依赖项 | 用途 | 就绪时间要求 | 负责人 | 状态 |
|--------|------|-------------|--------|------|
| 音频团队完成 Style Bible v1 | 所有生成和检测的基础 | Sprint 1 结束前 | AD | 待启动 |
| 音频团队完成 3 类 Category Rules | QC 检测和后处理参数 | Sprint 2 结束前 | AD | 待启动 |
| 音频团队完成 Wwise 模板 | Wwise 自动化基础 | Sprint 2 结束前 | AD + AE | 待启动 |
| 音频团队完成 Mapping Dictionary | UE 挂接基础 | Sprint 2 结束前 | AD + AE | 待启动 |
| 项目组提供测试用动画资源 | UE 挂接开发和测试 | Sprint 4 开始前 | 项目组 | 待确认 |
| 项目组提供测试用 UE 工程 | UE 挂接和跑测 | Sprint 4 开始前 | 项目组 | 待确认 |
| 自动化跑测脚本框架 | QA 自动化基础 | Sprint 5 结束前 | QA + AE | 待启动 |
| 自动化跑测环境（可编译游戏版本） | QA 跑测 | Sprint 6 开始前 | 项目组 | 待确认 |

### 9.3 依赖就绪时间要求汇总

| 时间点 | 必须就绪的依赖 |
|--------|---------------|
| Sprint 1 开始前 | Wwise 许可 + 版本确认、UE 版本确认、服务器/开发机 |
| Sprint 1 结束时 | Style Bible v1 |
| Sprint 2 结束时 | Category Rules x3、Wwise 模板、Mapping Dictionary、QA 规则 v1 |
| Sprint 3 开始前 | AI 生成 API 账号、多模态大模型 API 账号 |
| Sprint 4 开始前 | 测试用动画资源、测试用 UE 工程、Wwise UE Integration Plugin |
| Sprint 6 开始前 | 自动化跑测环境（可编译游戏版本） |

---

## 10. 待确认决策项

### 10.1 开放问题汇总

| 编号 | 问题 | 来源 | 建议决策时间 | 建议方案 |
|------|------|------|-------------|---------|
| D-01 | 第一阶段是否只选动作游戏模板？ | PRD 18 | Sprint 1 开始前 | 是，MVP 只支持 1 套动作游戏模板 |
| D-02 | 视频理解采用哪些输入源与标注格式？ | PRD 18 | Sprint 2 结束前 | MVP 限定为时长/关键帧/基础节奏检测，策划显式提供标签 |
| D-03 | 审批节点由音频负责人还是功能负责人签收？ | PRD 18 | Sprint 1 开始前 | MVP 合并为单审批节点，由音频负责人签收 |
| D-04 | 规则库与模板库的维护责任归属？ | PRD 18 | Sprint 1 开始前 | 音频负责人定义，音频 TA 维护 |
| D-05 | 输入视频理解是否由独立服务承担？ | FSD 14 | Sprint 2 结束前 | MVP 阶段作为 intent 模块子功能，不独立服务 |
| D-06 | 规则和模板采用配置文件还是后台管理？ | FSD 14 | Sprint 1 期间 | 后台管理（数据库 + 管理页面），支持版本化 |
| D-07 | UE 挂接优先支持 Editor 脚本还是插件？ | FSD 14 | Sprint 2 结束前 | Python Editor Scripting 为主，C++ 辅助 |
| D-08 | QA 与现有自动化平台如何对接？ | FSD 14 | Sprint 4 期间 | 通过任务队列投递跑测任务，结果回写数据库 |
| D-09 | 审批与回滚记录是否需要与项目管理系统联动？ | FSD 14 | Sprint 5 期间 | MVP 不联动，Phase 2 考虑 |
| D-10 | AI 音频生成服务选哪家？ | 技术调研 | Sprint 2 结束前 | 优先 ElevenLabs/Stable Audio API，备选 AudioCraft 本地 |
| D-11 | MVP 的 FSD 状态机中 SpecReviewPending 是否纳入？ | PM 调研 C-04 | Sprint 1 期间 | 纳入，低置信度时暂停 |
| D-12 | MVP 选定候选的逻辑（自动 vs 手动）？ | PM 调研 C-07 | Sprint 3 期间 | 默认选 QC 通过的最高评分候选，审批时可覆盖 |
| D-13 | Wwise Worker 和 UE Worker 需要 Windows 环境？ | 后端调研 | Sprint 1 开始前 | 是，WAAPI 和 UE Editor 通常在 Windows 运行，Worker 节点需混合 OS 部署 |

### 10.2 决策时间线

```
Sprint 1 开始前（第 0 周）: D-01, D-03, D-04, D-13
Sprint 1 期间（第 1-2 周）: D-06, D-11
Sprint 2 结束前（第 4 周）: D-02, D-05, D-07, D-10
Sprint 3 期间（第 5-6 周）: D-12
Sprint 4 期间（第 7-8 周）: D-08
Sprint 5 期间（第 9-10 周）: D-09
```

---

## 附录 A：MVP 功能边界澄清

以下为 PM 调研中识别的模糊/矛盾点及其 MVP 决策：

| 编号 | 模糊点 | MVP 决策 |
|------|--------|---------|
| C-01 | PRD 提出是否只选一个项目模板 | MVP 只支持 1 套动作游戏模板 |
| C-02 | 视频理解的深度 | 限定为时长/关键帧/基础节奏检测 + 降级模式 |
| C-03 | 审批是一个节点还是两个 | MVP 合并为单审批节点 |
| C-04 | SpecReviewPending 是否纳入状态机 | 纳入，低置信度时暂停 |
| C-05 | 回滚范围 | MVP 只做素材版本手动回滚 + 重新执行链路 |
| C-06 | UE 挂接是否支持弱语义匹配 | MVP 仅强规则匹配，弱语义为 P1 |
| C-07 | 谁选择最终候选 | 默认自动选择 QC 最优，审批时可覆盖 |

## 附录 B：技术栈总览

| 层面 | 技术选型 |
|------|---------|
| 后端框架 | Python 3.11+ / FastAPI |
| 数据库 | PostgreSQL + JSONB |
| 任务队列 | Celery + Redis |
| 文件存储 | MinIO（S3 兼容） |
| ORM | SQLAlchemy 2.0 + Alembic |
| 数据校验 | Pydantic v2 |
| 前端框架 | Next.js 14 (App Router) + TypeScript |
| UI 组件库 | Ant Design 5 + ProComponents |
| 状态管理 | TanStack Query v5 + Zustand |
| 音频播放 | Web Audio API + Howler.js |
| 波形渲染 | wavesurfer.js v7 |
| 频谱分析 | Web Audio API AnalyserNode + D3.js |
| 文件上传 | tus 协议 + tus-js-client |
| 实时推送 | SSE (Server-Sent Events) |
| 音频处理 | FFmpeg + librosa + pydub + pyloudnorm |
| Wwise 自动化 | WAAPI (waapi-client Python SDK) |
| UE 自动化 | Python Editor Scripting + C++ 辅助封装 |
| AI 生成 | ElevenLabs / Stable Audio API（主）+ AudioCraft（备）|
| 视频理解 | GPT-4o / Gemini 1.5 Pro（主）+ 关键帧提取 + CLIP/BLIP（备）|
| 监控 | Prometheus + Grafana |
| CI/CD | GitHub Actions / GitLab CI |

---

*文档版本：v1.0*
*生成日期：2026-04-01*
*状态：待评审*

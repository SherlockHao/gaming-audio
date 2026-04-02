# AI 游戏音频生产与集成系统 - 整体架构文档 v1.0

---

## 1. 项目概述

### 1.1 项目目标

本系统面向长周期游戏研发中前期，由专业音频人员在项目初期完成规则、模板与流程建制，之后利用 AI 驱动的自动化流水线接管标准化音频生产、Wwise 集成、UE 挂接和 QA 诊断工作，最小化中前期音频人力投入，并为后期正式音频量产与精修保留衔接空间。

核心命题：
- 专业音频前置建制后，系统能否稳定接收低门槛需求输入
- 系统能否把标准化 SFX/UI/基础环境循环音从需求走到 Wwise 和 UE
- 系统能否通过自动化 QA 与 Profile 诊断发现典型问题
- 系统能否以可追踪、可回滚方式完成一轮真实项目迭代

### 1.2 产品定位

产品不是"让非音频人员替代音频团队"，而是"由专业音频前置建制后，利用 AI 接管中前期标准化音频生产和集成工作"。三阶段使用模式：

1. **音频前置建制期** -- 专业音频人员建立风格规范、类别标准、Wwise 模板、UE mapping 规则、QA 规则
2. **AI 量产迭代期** -- 策划或相关制作人员提供低门槛输入，系统自动完成标准化音频工作
3. **人工精修收尾期** -- 正式音频团队接管高质量资源替换、复杂实时系统设计与终混

### 1.3 MVP 范围

- **资产类型**：动作 SFX、UI 音效、简单环境循环
- **项目模板**：动作游戏模板 1 套
- **核心链路**：需求输入 → Intent 生成 → 素材生成 → QC → Wwise 导入 → UE 挂接 → QA 检测 → 审批

### 1.4 目标用户

| 角色 | 职责 |
|------|------|
| 音频总监/高级音频设计师 | 前期风格建制、规则维护、关键审批 |
| 音频技术设计师/TA | 系统配置、Wwise 模板、UE mapping、自动化流程维护 |
| 策划/关卡/战斗策划 | 提交低门槛需求，提供视频/动画/UI 录屏 |
| QA | 运行自动化测试、提交问题描述供系统诊断 |

---

## 2. 系统架构总览

### 2.1 架构模式：模块化单体（Modular Monolith）

选择理由：
- MVP 阶段团队规模小、迭代速度优先，微服务运维复杂度过高
- 模块间存在强数据耦合（Task 是全局主线，所有实体以 task_id 为外键串联）
- 模块内部按清晰边界组织，后续可按需拆分为独立服务
- 与外部系统（Wwise WAAPI、UE Editor、AI 生成服务）通过任务队列天然异步解耦

### 2.2 系统模块全景图（7 大模块）

```
┌─────────────────────────────────────────────────────────────────────┐
│                         前端 (Next.js 16)                           │
│  任务提交页 │ 任务详情页 │ 审批页 │ 诊断页 │ 后台配置页             │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ REST API + SSE
┌───────────────────────────▼─────────────────────────────────────────┐
│                      API 网关 (FastAPI)                              │
│                  认证 │ 路由 │ 序列化                                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                     核心业务模块层                                    │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ 1.需求输入│→│2.Intent  │→│3.素材生成 │→│4.Wwise   │            │
│  │  模块    │  │ 生成模块 │  │  与QC模块 │  │ 自动化   │            │
│  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘            │
│                                                   │                  │
│  ┌──────────┐  ┌──────────┐               ┌──────▼─────┐           │
│  │7.QA与    │←│6.审批追踪│←─────────────│5.UE自动   │           │
│  │ 诊断模块 │  │ 回滚模块 │               │  挂接模块  │           │
│  └──────────┘  └──────────┘               └────────────┘           │
│                                                                      │
│  ┌─────────────────────────────────────────────────────┐            │
│  │              规则引擎 (贯穿所有模块)                   │            │
│  │  Style Bible │ Category Rules │ 模板 │ Mapping Dict  │            │
│  └─────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ Celery   │  │PostgreSQL│  │  MinIO   │
      │ Workers  │  │ + Redis  │  │ 文件存储 │
      └──────────┘  └──────────┘  └──────────┘
              │             │
       ┌──────┼──────┐      │
       ▼      ▼      ▼      │
   ┌──────┐┌──────┐┌──────┐ │
   │Wwise ││ UE   ││ AI   │ │
   │WAAPI ││Editor││生成   │ │
   └──────┘└──────┘└──────┘
```

### 2.3 模块间数据流

```
策划提交 → [需求输入] → Task + InputAssetRef
                           ↓
                    [Intent 生成] → AudioIntentSpec (含 confidence)
                           ↓ (confidence >= 0.6 继续，否则进入 SpecReviewPending)
                    [素材生成与QC] → CandidateAudio[] + QcReport
                           ↓ (至少 1 个候选通过 QC)
                    [Wwise 自动化] → WwiseObjectManifest + BankManifest
                           ↓
                    [UE 自动挂接] → BindingManifest + UnresolvedBindingQueue
                           ↓
                    [QA 与诊断] → QaReport + QaIssue[]
                           ↓
                    [审批追踪回滚] → ReviewRecord + AuditLog + RollbackPoint
                           ↓
                        Approved / Rejected
```

---

## 3. 技术栈

### 3.1 后端

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| 语言与框架 | Python 3.11+ / FastAPI | 与 AI/ML 生态无缝衔接；Pydantic 天然适合复杂结构体校验；WAAPI Python SDK 直接可用 |
| 数据库 | PostgreSQL + JSONB | 核心实体关系型建模；灵活字段（generation_params、timing_points 等）用 JSONB；支持 GIN 索引 |
| 任务队列 | Celery + Redis (Broker) | 音频生成、Wwise 导入、Bank 构建等长时间任务异步执行；支持重试、超时、优先级、任务链 |
| 缓存/锁 | Redis | Celery Broker、缓存、分布式锁（防止并发回滚） |
| 文件存储 | MinIO (S3 兼容) | 私有化部署，后续可迁移至云 S3/OSS；按 `/{project_id}/{task_id}/{stage}/{filename}` 组织 |
| ORM | SQLAlchemy 2.0 (async) | 配合 FastAPI 异步模式 |
| 数据库迁移 | Alembic | 标准 Python 生态方案 |
| 状态机 | Python transitions 库 | 声明式、支持条件守卫和回调、轻量 |
| 日志 | structlog | 结构化日志，便于审计 |
| 监控 | Prometheus + Grafana | 任务成功率、队列积压、处理时长 |

### 3.2 前端

> **Note**: The actual versions installed are Next.js 16 and Ant Design 6 (due to using latest at time of setup). This architecture document has been updated accordingly.

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| 框架 | Next.js 16 (App Router) | SSR/SSG 混合渲染；文件系统路由适合按角色拆分 Layout；API Routes 可作 BFF 层 |
| UI 库 | Ant Design 6 | 内部工具型产品，表单密度高、表格功能强；ProTable/ProForm 减少开发量 |
| 状态管理 | TanStack Query v5 (服务端状态) + Zustand (客户端状态) | TanStack Query 管理 API 数据缓存/失效/轮询；Zustand 管理音频播放器全局状态和表单草稿 |
| 类型系统 | TypeScript (strict) | 确保前后端数据契约一致 |
| 音频播放 | Web Audio API + Howler.js | 精确时间控制和音频分析 + 跨浏览器兼容 |
| 波形渲染 | wavesurfer.js v7 | Canvas/WebGL 渲染、缩放、区域选择、多轨道 |
| 频谱可视化 | Web Audio API AnalyserNode + D3.js | 实时 FFT 数据 + 专业频谱图绘制 |
| 大文件上传 | tus-js-client (tus 协议) | 分片断点续传，支持视频上传 |
| 实时推送 | SSE (Server-Sent Events) | 单向推送，开销小，自动重连 |

### 3.3 音频处理

| 组件 | 用途 |
|------|------|
| FFmpeg | 格式转换、头尾裁切、基础音频操作 |
| librosa | 音频特征提取、频谱分析 |
| pyloudnorm | ITU-R BS.1770 响度测量与标准化 |
| pydub | 淡入淡出、格式处理辅助 |
| numpy/scipy | DSP 运算基础 |

### 3.4 Wwise 集成

| 组件 | 用途 |
|------|------|
| WAAPI (Wwise Authoring API) | WebSocket 协议与 Wwise Authoring 通信 |
| waapi-client (Python) | 官方 Python SDK，对象创建/导入/Event/Bank 操作 |
| Wwise Console / CLI | Bank 生成、工程验证 |

### 3.5 UE 集成

| 组件 | 用途 |
|------|------|
| Python Editor Scripting | AnimNotify 写入、资产查询与修改 |
| C++ Editor Utility (备选) | 高性能批量操作场景 |
| Wwise UE Integration Plugin | AkEvent、AkComponent 等音频组件 |

### 3.6 AI 生成

| 组件 | 用途 |
|------|------|
| 多模态大模型 | 视频理解、语义提取（MVP 降级为辅助标注） |
| 音频生成 API | AI SFX/UI/Amb 候选生成（保留人工上传替代路径） |

---

## 4. 数据模型

### 4.1 ER 关系总览

```
projects 1───N tasks
tasks    1───N input_asset_refs
tasks    1───1 audio_intent_specs
tasks    1───N candidate_audios
tasks    1───N qc_reports
tasks    1───N wwise_object_manifests (多版本)
tasks    1───N binding_manifests (多版本)
tasks    1───N qa_issues
tasks    1───N audit_logs
tasks    1───N review_records
tasks    1───N rollback_points

candidate_audios 1───N qc_reports
audio_intent_specs N───1 category_rules
audio_intent_specs N───1 wwise_templates
```

### 4.2 核心表结构（12 张表）

#### projects

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| project_id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | |
| style_bible | JSONB | | 风格圣经配置 |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

#### tasks

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| task_id | UUID | PK | |
| project_id | UUID | FK → projects | |
| title | VARCHAR(255) | NOT NULL | |
| requester | VARCHAR(128) | NOT NULL | |
| asset_type | VARCHAR(32) | NOT NULL | sfx / ui / ambience_loop |
| semantic_scene | VARCHAR(64) | NOT NULL | 场景语义 |
| play_mode | VARCHAR(16) | NOT NULL | one_shot / loop |
| tags | JSONB | | 标签数组 |
| notes | TEXT | | |
| priority | SMALLINT | DEFAULT 0 | |
| status | VARCHAR(32) | NOT NULL | 状态机当前状态 |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

索引：`(project_id, status)`、`(requester)`、`(created_at DESC)`

#### input_asset_refs

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| input_asset_id | UUID | PK | |
| task_id | UUID | FK → tasks CASCADE | |
| asset_kind | VARCHAR(32) | NOT NULL | video / animation / ui_recording / vfx_preview / path_ref |
| asset_path | VARCHAR(1024) | NOT NULL | |
| asset_version | VARCHAR(64) | | |
| checksum | VARCHAR(128) | | SHA-256 |

#### audio_intent_specs

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| intent_id | UUID | PK | |
| task_id | UUID | FK → tasks, UNIQUE | 一个 task 对应一个 spec |
| content_type | VARCHAR(32) | NOT NULL | |
| semantic_role | VARCHAR(64) | | |
| intensity | VARCHAR(16) | | light / medium / heavy / epic |
| material_hint | VARCHAR(64) | | |
| timing_points | JSONB | | 时间点数组 |
| loop_required | BOOLEAN | NOT NULL | |
| variation_count | SMALLINT | DEFAULT 3 | |
| design_pattern | VARCHAR(64) | | |
| category_rule_id | UUID | FK → category_rules | |
| wwise_template_id | UUID | FK → wwise_templates | |
| ue_binding_strategy | VARCHAR(32) | | rule / semantic / manual |
| confidence | NUMERIC(4,3) | | 0.000 ~ 1.000 |
| unresolved_fields | JSONB | | |

#### candidate_audios

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| candidate_id | UUID | PK | |
| task_id | UUID | FK → tasks | |
| version | SMALLINT | NOT NULL | |
| source_model | VARCHAR(128) | | AI 模型标识 |
| generation_params | JSONB | | |
| file_path | VARCHAR(1024) | NOT NULL | |
| duration_ms | INTEGER | | |
| stage | VARCHAR(16) | NOT NULL | source / processed / mastered |
| selected | BOOLEAN | DEFAULT FALSE | |
| created_at | TIMESTAMPTZ | NOT NULL | |

#### qc_reports

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| qc_report_id | UUID | PK | |
| task_id | UUID | FK → tasks | |
| candidate_id | UUID | FK → candidate_audios | |
| peak_result | JSONB | | |
| loudness_result | JSONB | | |
| spectrum_result | JSONB | | |
| head_tail_result | JSONB | | |
| format_result | JSONB | | |
| qc_status | VARCHAR(16) | NOT NULL | passed / failed |
| created_at | TIMESTAMPTZ | NOT NULL | |

#### wwise_object_manifests

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| manifest_id | UUID | PK | |
| task_id | UUID | FK → tasks | |
| version | SMALLINT | NOT NULL | |
| object_entries | JSONB | NOT NULL | 对象数组 |
| import_status | VARCHAR(16) | NOT NULL | |
| build_log | TEXT | | |
| created_at | TIMESTAMPTZ | NOT NULL | |

#### binding_manifests

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| binding_manifest_id | UUID | PK | |
| task_id | UUID | FK → tasks | |
| version | SMALLINT | NOT NULL | |
| bindings | JSONB | NOT NULL | |
| unresolved_bindings | JSONB | | |
| created_at | TIMESTAMPTZ | NOT NULL | |

#### qa_issues

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| qa_issue_id | UUID | PK | |
| task_id | UUID | FK → tasks, NULLABLE | |
| project_id | UUID | FK → projects | |
| timestamp_sec | NUMERIC(10,3) | | 游戏内时间点 |
| issue_type | VARCHAR(64) | NOT NULL | |
| related_actor | VARCHAR(128) | | |
| related_skill | VARCHAR(128) | | |
| related_event | VARCHAR(256) | | |
| root_cause_guess | TEXT | | |
| suggested_fix | TEXT | | |
| evidence_refs | JSONB | | |
| resolution_status | VARCHAR(32) | NOT NULL | open / investigating / resolved / wont_fix |
| created_at | TIMESTAMPTZ | NOT NULL | |

#### category_rules

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| rule_id | UUID | PK | |
| project_id | UUID | FK → projects | |
| category | VARCHAR(32) | NOT NULL | sfx / ui / ambience_loop |
| rule_level | VARCHAR(16) | NOT NULL | project / template / category |
| rule_body | JSONB | NOT NULL | 规则内容 |
| version | SMALLINT | NOT NULL | |
| is_active | BOOLEAN | DEFAULT TRUE | |
| created_at | TIMESTAMPTZ | NOT NULL | |

#### wwise_templates

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| template_id | UUID | PK | |
| project_id | UUID | FK → projects | |
| name | VARCHAR(128) | NOT NULL | |
| template_type | VARCHAR(32) | NOT NULL | |
| template_body | JSONB | NOT NULL | |
| version | SMALLINT | NOT NULL | |
| is_active | BOOLEAN | DEFAULT TRUE | |

#### audit_logs

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| log_id | BIGSERIAL | PK | |
| task_id | UUID | NULLABLE | |
| project_id | UUID | | |
| actor | VARCHAR(128) | NOT NULL | 操作人或系统标识 |
| action | VARCHAR(64) | NOT NULL | task_created / spec_generated / approved 等 |
| old_state | VARCHAR(32) | | |
| new_state | VARCHAR(32) | | |
| detail | JSONB | | 变更详情快照 |
| error_context | JSONB | | 失败时的错误上下文 |
| created_at | TIMESTAMPTZ | NOT NULL | |

索引：`(task_id, created_at)`、`(project_id, action, created_at)`

#### review_records

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| review_id | UUID | PK | |
| task_id | UUID | FK → tasks | |
| review_type | VARCHAR(32) | NOT NULL | audio_review / binding_review / spec_review |
| reviewer | VARCHAR(128) | NOT NULL | |
| decision | VARCHAR(16) | NOT NULL | approved / rejected |
| comments | TEXT | | |
| created_at | TIMESTAMPTZ | NOT NULL | |

#### rollback_points

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| rollback_id | UUID | PK | |
| task_id | UUID | FK → tasks | |
| snapshot_type | VARCHAR(32) | NOT NULL | audio / wwise / ue_binding / full |
| snapshot_data | JSONB | NOT NULL | |
| created_at | TIMESTAMPTZ | NOT NULL | |

---

## 5. 核心模块设计

### 5.1 需求输入模块

**职责**：以低门槛方式接收音频需求，将非结构化输入整理为标准任务。

**输入**：任务名称、资源类型、场景语义、播放方式、标签、输入素材（视频/动画/UI 录屏/美术特效预览/资源路径引用）、备注。

**输出**：Task 对象 + InputAssetRef + 提交日志。

**核心技术方案**：
- 表单校验：必须选择资源类型、播放方式、场景语义，必须提供至少一个输入素材
- 素材上传：基于 tus 协议分片断点续传，支持 mp4/mov/avi 格式，单文件上限 500MB
- 校验失败时阻止提交，素材不可读时标记为 `invalid_input`

**关键接口**：
- `POST /api/v1/tasks` -- 创建任务
- `PATCH /api/v1/tasks/{task_id}` -- 编辑草稿
- `POST /api/v1/tasks/{task_id}/submit` -- 提交任务

### 5.2 Intent 生成模块

**职责**：将任务转换为后续模块可执行的结构化音频意图 (AudioIntentSpec)。

**输入**：Task + InputAssetRef + Style Bible + Category Rules + Mapping Dictionary。

**输出**：AudioIntentSpec（含 confidence）+ UnresolvedFields。

**核心技术方案**：
- 按优先级查询 Mapping Dictionary：精确 skill_id → 资源路径匹配 → 动作名匹配 → 角色类别组合推断 → UI/环境功能匹配
- 依据资源类型决定默认类别，依据播放方式决定 loop_required，依据场景语义估算 intensity 和 design_pattern
- confidence < 0.6 时自动进入 SpecReviewPending，不继续后续链路
- MVP 阶段视频理解降级为"辅助标注"：策划需手动填写关键 timing_points，系统仅提取视频时长和基础节奏作为参考

**关键接口**：
- `POST /api/v1/tasks/{task_id}/intent` -- 生成 Spec
- `PATCH /api/v1/tasks/{task_id}/intent` -- 人工修正 Spec

### 5.3 素材生成与 QC 模块

**职责**：根据 AudioIntentSpec 生成候选音频，执行后处理和质量检测。

**输入**：AudioIntentSpec + Category Rules + Style Bible + 输入素材。

**输出**：CandidateAudio[]（source/processed/mastered）+ QcReport。

**核心技术方案**：
- 默认生成 3 个候选，每个候选记录 version 和 generation_params
- 后处理链路：切除静音头尾 → 基础淡入淡出 → 响度标准化 → 频段检测
- QC 检测 8 项指标：采样率、位深、声道数、Integrated LUFS、True Peak、时长、静音头尾、频谱异常
- QC 全部不通过时阻断后续流程，标记 QCFailed
- AI 生成保留人工上传替代路径（高风险缓解措施）

**关键接口**：
- `POST /api/v1/tasks/{task_id}/audio/generate` -- 触发生成（异步）
- `POST /api/v1/tasks/{task_id}/audio/qc` -- 触发 QC
- `POST /api/v1/tasks/{task_id}/audio/{candidate_id}/select` -- 选定候选

### 5.4 Wwise 自动化模块

**职责**：通过模板和规则完成 Wwise 对象创建、音频导入和 Bank 生成。

**输入**：AudioIntentSpec + ProcessedAudio[] + WwiseTemplate + Category Rules。

**输出**：WwiseObjectManifest + ImportManifest + BankManifest + BuildLog。

**核心技术方案**：
- 通过 WAAPI WebSocket 长连接与 Wwise Authoring 通信，心跳 10s，断开后指数退避重连
- 创建顺序：Actor-Mixer 路径确认/创建 → Random Container → Sound SFX → 音频导入 → Event 创建 → Event Action 配置 → SoundBank 关联与生成
- 增量更新：先查目标路径已有子对象，仅创建缺失项
- MVP 自动化对象范围：Sound SFX、Random Container、基础 Actor-Mixer、基础 Bus、Event、SoundBank

**关键接口**：
- `POST /api/v1/tasks/{task_id}/wwise/import` -- 触发导入（异步）
- `POST /api/v1/tasks/{task_id}/wwise/build-bank` -- 触发 Bank 生成（异步）

### 5.5 UE 自动挂接模块

**职责**：将 Wwise Event 自动绑定到 UE 中的目标对象。

**输入**：AudioIntentSpec + BindingRules + Wwise Event 信息 + UE AssetRef。

**输出**：BindingManifest + NotifyMappingReport + UnresolvedBindingQueue。

**核心技术方案**：
- MVP 仅使用强规则匹配（动画名、技能 ID、资源路径直接匹配 Event），弱语义匹配为 P1 功能
- 挂接目标：AnimNotify（动画触发类）、AkComponent（持续类声音）
- 低置信度项 100% 进入 UnresolvedBindingQueue，不静默跳过
- 重复挂接幂等：不产生重复 AnimNotify
- 通过 UE Python Editor Scripting 操作动画资产

**关键接口**：
- `POST /api/v1/tasks/{task_id}/ue/bind` -- 触发挂接（异步）
- `GET /api/v1/tasks/{task_id}/ue/unresolved` -- 查询未解析队列

### 5.6 审批追踪回滚模块

**职责**：记录全过程状态和关键变更，提供审批和回滚能力。

**输入**：任务状态变化、资产版本变化、Wwise/UE 清单变化、QA 结果。

**输出**：AuditLog + VersionRecord + ReviewRecord + RollbackPoint。

**核心技术方案**：
- MVP 合并为单一审批节点（任务走完全链路后由音频负责人一次性审批）
- 审计日志覆盖全部关键操作（创建/Spec/生成/QC/Wwise/Bank/UE/QA/审批/回滚），长期保留
- 回滚快照在每个关键状态转换成功后自动创建
- MVP 只做素材版本手动回滚 + 重新执行链路；Wwise/UE 精确回滚为 P1 功能
- 回滚不删除文件和记录，只标记无效并创建新版本
- 并发保护：Redis 分布式锁防止同一任务并发回滚

**关键接口**：
- `POST /api/v1/tasks/{task_id}/review` -- 提交审批
- `POST /api/v1/tasks/{task_id}/rollback` -- 触发回滚
- `GET /api/v1/tasks/{task_id}/audit-log` -- 查询审计日志

### 5.7 QA 与诊断模块

**职责**：从自动化跑测和 Profile 数据中发现问题并定位疑似根因。

**输入**：自动化跑测结果、Profile Capture、WwiseObjectManifest、BindingManifest、问题描述。

**输出**：QaReport + QaIssue[] + DiagnosisReport。

**核心技术方案**：
- 通过 WAAPI Profiler 接口启动 Capture，实时获取 Voice/Event/Bus/RTPC 数据
- MVP 支持 9 种问题类型检测：Event 未触发、Event 触发但无 Voice、Voice 被 Kill、Voice 被 Virtualize、RTPC 导致音量为 0、Bus Mute/音量异常、Bank 未加载、Media 缺失、映射对象错误
- 诊断链路：接收问题描述 → 定位 Profile Capture → 映射目标 Wwise 对象 → 逐层检查（Event→Voice→Volume→Bus→Bank→Media）→ 输出根因和建议
- Profile 缺失时标记 ProfileUnavailable，不产出误导性结果

**关键接口**：
- `POST /api/v1/tasks/{task_id}/qa/run` -- 触发 QA（异步）
- `POST /api/v1/tasks/{task_id}/qa/diagnose` -- 触发诊断

---

## 6. 规则体系

### 6.1 Style Bible 结构

Style Bible 是系统规则引擎的顶层约束，定义项目整体听觉风格边界。

```
StyleBible
├── meta                        # 元信息（version, author, status）
├── sonic_identity              # 听觉身份
│   ├── one_line_summary        # 一句话听觉定位
│   ├── aesthetic_pillars[]     # 听觉美学支柱（3-5 条）
│   ├── emotional_arc           # 情感弧线
│   ├── world_material_palette  # 世界观材质调色板
│   └── era_tech_level          # 时代与科技水平
├── reference_works[]           # 参考作品（title, category, relevance_aspect, notes）
├── keyword_library             # 关键词库
│   ├── positive_keywords[]     # 鼓励倾向（keyword, category, weight 1-5）
│   └── negative_keywords[]     # 回避倾向（keyword, category, severity: soft_avoid/hard_ban）
├── prohibition_list[]          # 禁用倾向（description, reason, scope: global/sfx/ui/ambience）
├── category_style_overrides    # 按类别风格微调
└── approval_history[]          # 审批记录
```

### 6.2 Category Rules 详细规格

#### SFX（动作/技能/特效音效）

| 项目 | 规格 |
|------|------|
| 采样率 | 48000 Hz |
| 位深 | 24-bit |
| 声道 | 单声道优先 |
| Integrated LUFS | -18 ~ -12 LUFS（依 intensity 分级） |
| True Peak | ≤ -1.0 dBTP |
| 时长 | 50ms ~ 5000ms（Boss 技能可放宽至 8000ms） |
| 低频 | 30Hz 以下 HPF 切除 |
| 淡入 | 默认不加（保持瞬态）；DC offset 导致 click 时加 0.5-2ms |
| 淡出 | 5-30ms（尾韵类 50-200ms） |
| 静音头部 | ≤ 10ms |
| 静音尾部 | ≤ 50ms |

#### UI 音效

| 项目 | 规格 |
|------|------|
| 采样率 | 48000 Hz |
| 位深 | 24-bit |
| 声道 | 单声道 |
| Integrated LUFS | -24 ~ -18 LUFS |
| True Peak | ≤ -1.0 dBTP |
| 时长 | 20ms ~ 1500ms（hover/滚动类 20-300ms，确认/取消类 100-800ms，弹窗/转场类 300-1500ms） |
| 低频 | 80Hz 以下 HPF 切除 |
| 淡入 | 0-1ms |
| 淡出 | 5-20ms |
| 静音头部 | 0ms（不允许） |
| 静音尾部 | ≤ 20ms |

#### 环境循环音（Ambience Loop）

| 项目 | 规格 |
|------|------|
| 采样率 | 48000 Hz |
| 位深 | 24-bit |
| 声道 | 立体声 |
| Integrated LUFS | -30 ~ -20 LUFS |
| True Peak | ≤ -1.0 dBTP |
| 时长 | 8000ms ~ 60000ms（推荐 15s-60s） |
| 频段 | 全频段允许（30Hz-20kHz），低频显著能量需人工确认 |
| 循环处理 | 首尾无缝拼接（zero-crossing 对齐或 crossfade），拼接点 peak 差 < 0.01 |
| 静音头尾 | 0ms（不允许，否则破坏循环） |
| 命名标记 | 文件名须含 `_loop` |

### 6.3 Wwise 模板架构（动作游戏模板）

**Actor-Mixer Hierarchy**：
```
ActionGame
├── Characters
│   ├── Player（Melee/Ranged/Skill/Movement/Hit）
│   ├── Enemy_Normal（Attack/Hit/Death）
│   └── Enemy_Boss（Boss_{ID}_Attack/Skill/Hit/Death）
├── Weapons（Sword/GreatSword/Spear/Bow/Shield）
├── Environment
│   ├── Env_Ambience（Forest/Dungeon/Castle/Battlefield）
│   ├── Env_Interactive（Door/Chest/Lever/Trap）
│   └── Env_Destruction（Wood/Stone/Metal）
├── UI（Navigation/Confirm/Popup/System）
└── Cinematics（预留）
```

**Bus 结构**：
```
Master Audio Bus
├── Bus_SFX（Player/Enemy/Weapon/Environment 子总线）
├── Bus_Ambience（Base/Detail）
├── Bus_UI
├── Bus_Music（预留）
├── Bus_VO（预留）
└── Bus_Cinematic（预留）
```

**Event 命名规则**：`Play_{Category}_{Subject}_{Action}_{Variant}`，使用 PascalCase。Category 枚举：Char/Wpn/Env/UI/Mus/VO。

**SoundBank 分组策略**：
| Bank | 加载策略 |
|------|---------|
| Bank_Init | 启动时常驻 |
| Bank_Player | 进入游戏后常驻 |
| Bank_Enemy_Normal | 进入关卡时加载 |
| Bank_Boss_{ID} | 进入 Boss 区域时加载，离开卸载 |
| Bank_Env_{LevelID} | 按关卡加载/卸载 |
| Bank_UI | 启动后常驻 |

**Conversion Setting**：SFX 常规 Vorbis Q4、Boss 音效 Vorbis Q6、UI Vorbis Q2、Ambience Vorbis Q4。

### 6.4 Mapping Dictionary 结构

映射字典核心组件：
- **character_class_map** -- 角色类别 → 音频语义角色 + 默认 intensity + Wwise 层级前缀
- **action_map** -- 动作名模式 → 动作类别 + content_type + Event 命名模板 + category_rule_id
- **skill_map** -- 技能 ID → 精确 Event 名 + timing_hint + variation_count
- **resource_name_map** -- UE 资源路径模式 → 解析后的动作/主体/Event
- **ui_function_map** -- UI 功能 ID → Event 名 + category_rule_id
- **environment_map** -- 关卡/区域 → Play/Stop Event + Bank 名

查询优先级：精确 skill_id > 资源路径匹配 > 动作名匹配 > 角色+动作组合推断 > UI/环境功能匹配。confidence < 0.7 时进入 SpecReviewPending。

### 6.5 规则引擎优先级与冲突处理

四层优先级（从高到低）：
1. **Task Override** -- 任务级覆盖
2. **Category Level Rule** -- 按资产类型
3. **Template Level Rule** -- 按 Wwise 模板
4. **Project Level Rule** -- 项目全局默认

冲突处理：高优先级覆盖低优先级；冲突记录到 audit_logs；关键字段冲突且无法自动决策时进入 SpecReviewPending。

---

## 7. API 设计

### 7.1 RESTful API 路由总表

所有路由前缀：`/api/v1`

| 模块 | 方法 | 路由 | 说明 |
|------|------|------|------|
| **任务** | POST | `/tasks` | 创建任务 |
| | GET | `/tasks` | 查询列表（分页/筛选） |
| | GET | `/tasks/{task_id}` | 查询详情 |
| | PATCH | `/tasks/{task_id}` | 编辑草稿 |
| | POST | `/tasks/{task_id}/submit` | 提交任务 |
| **Intent** | POST | `/tasks/{task_id}/intent` | 生成 Spec |
| | GET | `/tasks/{task_id}/intent` | 查询 Spec |
| | PATCH | `/tasks/{task_id}/intent` | 人工修正 |
| **音频** | POST | `/tasks/{task_id}/audio/generate` | 触发生成（异步，返回 202） |
| | GET | `/tasks/{task_id}/audio/candidates` | 查询候选列表 |
| | POST | `/tasks/{task_id}/audio/qc` | 触发 QC |
| | GET | `/tasks/{task_id}/audio/qc-reports` | 查询 QC 报告 |
| | POST | `/tasks/{task_id}/audio/{candidate_id}/select` | 选定候选 |
| **Wwise** | POST | `/tasks/{task_id}/wwise/import` | 触发导入（异步） |
| | POST | `/tasks/{task_id}/wwise/build-bank` | 触发 Bank 生成（异步） |
| | GET | `/tasks/{task_id}/wwise/manifest` | 查询对象清单 |
| **UE** | POST | `/tasks/{task_id}/ue/bind` | 触发挂接（异步） |
| | GET | `/tasks/{task_id}/ue/manifest` | 查询挂接清单 |
| | GET | `/tasks/{task_id}/ue/unresolved` | 查询未解析队列 |
| **QA** | POST | `/tasks/{task_id}/qa/run` | 触发 QA（异步） |
| | GET | `/tasks/{task_id}/qa/report` | 查询报告 |
| | POST | `/tasks/{task_id}/qa/diagnose` | 触发诊断 |
| | GET | `/qa/issues` | 项目级问题查询 |
| **审批** | POST | `/tasks/{task_id}/review` | 提交审批 |
| | POST | `/tasks/{task_id}/rollback` | 触发回滚 |
| | GET | `/tasks/{task_id}/audit-log` | 查询审计日志 |
| **规则** | GET/POST | `/projects/{project_id}/rules/categories` | 类别规则 CRUD |
| | GET/POST | `/projects/{project_id}/rules/templates` | Wwise 模板 CRUD |
| | GET/POST | `/projects/{project_id}/rules/mappings` | 映射字典 CRUD |
| | GET/PUT | `/projects/{project_id}/style-bible` | 风格圣经管理 |
| **异步任务** | GET | `/jobs/{job_id}` | 查询异步任务状态/结果 |

### 7.2 认证与权限

- **认证**：JWT Token（内部 SSO 签发），请求头 `Authorization: Bearer <token>`
- **角色**：

| 角色 | 权限范围 |
|------|---------|
| admin | 全部权限 |
| audio_lead | 规则/模板管理、审批、回滚、全部查询 |
| audio_ta | 规则/模板管理、任务管理、全部查询 |
| planner | 任务创建/编辑/提交、查询自己的任务 |
| qa | QA 相关接口、问题诊断、查询 |
| viewer | 只读查询 |

- **项目隔离**：所有数据按 project_id 隔离，JWT payload 携带可访问的 project_id 列表

---

## 8. 前端架构

### 8.1 页面清单与路由

```
/login                              # 登录
/tasks                              # 任务列表（支持过滤、搜索、状态筛选）
/tasks/create                       # 任务提交（策划视角）
/tasks/batch-create                 # 批量导入（P1）
/tasks/:taskId                      # 任务详情（全角色，含 Tab 切换）
/tasks/:taskId/review               # 审批操作（音频负责人）
/tasks/:taskId/candidates           # 候选音频对比试听
/tasks/:taskId/wwise                # Wwise 导入详情
/tasks/:taskId/ue-binding           # UE 挂接详情
/tasks/:taskId/qa                   # QA 报告
/tasks/:taskId/rollback             # 回滚操作
/diagnosis                          # 诊断列表
/diagnosis/new                      # 新建诊断
/diagnosis/:diagnosisId             # 诊断结果
/admin/style-bible                  # 风格库管理
/admin/category-rules               # 类别规则管理
/admin/wwise-templates              # Wwise 模板管理
/admin/ue-mapping                   # UE mapping 管理
/admin/qa-rules                     # QA 规则管理
/admin/versions                     # 版本与回滚管理
```

### 8.2 核心页面交互概要

**任务提交页**：左右两栏布局，左栏表单（资源类型/场景语义/播放方式/标签/备注），右栏素材预览（上传后实时视频预览 + 文件元信息）。选择资源类型后场景语义下拉动态过滤。草稿自动保存到 localStorage。

**任务详情页**：顶部任务基本信息卡片 + 水平状态时间线，下方 Tab 切换各阶段详情（Overview / Candidates / Wwise / UE / QA / AuditLog）。失败阶段标红可点击跳转。TanStack Query 并行拉取数据，SSE 实时更新进行中阶段。

**审批页**：上方展示任务摘要 + 候选音频试听 + QC/Wwise/UE 改动概要，下方为通过/拒绝表单。支持与上一版本 diff 对比。

**问题诊断页**：输入时间点 + 关卡/角色/技能（级联选择）+ 问题描述。结果展示为垂直诊断链路图，每个节点显示检查结果（绿色通过/红色异常），根因卡片突出显示。

### 8.3 音频专业组件

- **AudioComparePlayer**：多候选 A/B 切换试听，保持 playhead 位置不变，键盘快捷键 1/2/3 快速切换
- **WaveformViewer**：wavesurfer.js v7，支持标准波形/频谱图/多轨道模式，QC 异常区域自动标红
- **SpectrumChart**：D3.js 绘制频谱图，叠加 Category Rule 参考线
- **LoudnessChart**：D3.js 绘制响度时间曲线，叠加目标响度区间
- **TaskStatusTimeline**：基于 Ant Design Timeline 定制，支持失败分支和回滚路径展示

### 8.4 实时更新与文件上传

- **实时推送**：SSE 为主（任务状态变更/生成进度/审批通知），收到事件后 TanStack Query 做按需缓存失效
- **大文件上传**：tus 协议分片断点续传，50MB 以下不分片，50-500MB 按 5MB 分片，500MB 以上按 10MB 分片，并发 3 路
- **进度持久化**：上传 ID 和进度持久化到 IndexedDB，刷新页面后可恢复

---

## 9. 任务状态机

### 9.1 完整状态定义

```
Draft → Submitted → SpecGenerated → AudioGenerated → QCReady →
WwiseImported → BankBuilt → UEBound → QARun → ReviewPending → Approved

分支状态：
Submitted → SpecReviewPending（confidence 不足）
AudioGenerated → QCFailed（全部候选不合规）
SpecGenerated → AudioGenerationFailed（生成失败）
QCReady → WwiseImportFailed
WwiseImported → BankBuildFailed
BankBuilt → UEBindFailed / BindingReviewPending
ReviewPending → Rejected → RolledBack
```

### 9.2 状态流转规则

| 触发 | 来源 | 目标 | 条件 |
|------|------|------|------|
| submit | Draft | Submitted | 字段校验通过 |
| spec_ok | Submitted | SpecGenerated | confidence ≥ 0.6 |
| spec_review | Submitted | SpecReviewPending | confidence < 0.6 |
| spec_confirmed | SpecReviewPending | SpecGenerated | 人工确认 |
| audio_ok | SpecGenerated | AudioGenerated | 候选生成成功 |
| audio_fail | SpecGenerated | AudioGenerationFailed | 生成失败 |
| qc_pass | AudioGenerated | QCReady | 至少 1 个候选通过 QC |
| qc_fail | AudioGenerated | QCFailed | 全部不通过 |
| wwise_ok | QCReady | WwiseImported | 导入成功 |
| wwise_fail | QCReady | WwiseImportFailed | 导入失败 |
| bank_ok | WwiseImported | BankBuilt | Bank 生成成功 |
| bank_fail | WwiseImported | BankBuildFailed | Bank 失败 |
| ue_ok | BankBuilt | UEBound | 挂接成功 |
| ue_fail | BankBuilt | UEBindFailed | 挂接失败 |
| qa_done | UEBound | QARun | QA 完成 |
| review_ready | QARun | ReviewPending | 生成报告 |
| approve | ReviewPending | Approved | 审批通过 |
| reject | ReviewPending | Rejected | 审批拒绝 |
| rollback | Rejected | RolledBack | 回滚成功 |

**重试路径**：各 Failed 状态可通过 retry 触发回到前一步重新执行。

### 9.3 异常处理与重试策略

- 所有失败状态为"可停留"状态，不自动清除，必须人工重试或干预
- 失败时记录审计日志（错误原因 + 输入参数快照）
- Celery 任务设置 soft_time_limit 和 time_limit，超时后标记 Failed
- 每次任务执行前检查状态合法性（幂等性保障）
- 自动触发：Worker 完成后回调状态机；人工触发：审批/确认/重试通过 API

---

## 10. 测试策略

### 10.1 测试金字塔

| 层级 | 比例 | 覆盖目标 | 覆盖率标准 |
|------|------|----------|-----------|
| 单元测试 | ~55% | 核心逻辑、规则引擎、状态机 | 核心模块行覆盖 ≥ 85%，状态机 ≥ 95% |
| 集成测试 | ~30% | 模块间数据流、WAAPI 交互、UE 脚本 | 模块间接口 100%，异常流 ≥ 90% |
| E2E 测试 | ~15% | 端到端完整链路、诊断链路 | 4 个核心场景全部覆盖 |

### 10.2 关键测试场景

- **场景 A**：动作 SFX 完整链路（提交→生成→QC→Wwise→UE→QA→审批）
- **场景 B**：UI 音效批量链路（5 个 UI 需求全部自动处理）
- **场景 C**：环境循环音链路（loop 生成→Wwise loop 属性→AkComponent 绑定）
- **场景 D**：问题诊断链路（预埋问题→Profile→诊断报告）
- **场景 E**：审批拒绝与回滚（Wwise/UE 产出物正确移除）

### 10.3 诊断准确性验证

- 为每种问题类型构建 ≥ 5 个已知根因测试 Case
- 目标：准确率 ≥ 80%，召回率 ≥ 85%，首位命中率 ≥ 70%

### 10.4 CI/CD 质量门禁

| 检查项 | 通过标准 | 阻断级别 |
|--------|---------|---------|
| Lint + Type Check | 0 error | 阻断合入 |
| 单元测试 | 100% 通过，覆盖率 ≥ 85% | 阻断合入 |
| 集成测试 | ≥ 95% 通过 | 阻断发布 |
| 冒烟 E2E | 100% 通过 | 阻断部署 |
| 完整 E2E | ≥ 95% 通过 | 阻断发布 |
| 诊断准确率回归 | 准确率 ≥ 80%，召回率 ≥ 85% | 阻断发布 |
| 安全扫描 | 无 Critical/High 漏洞 | 阻断合入 |

---

## 11. 技术风险与缓解

| 风险 | 等级 | 影响范围 | 缓解方案 |
|------|------|---------|---------|
| **AI 音频生成质量与可控性** | 高 | 素材生成模块 | 采用"AI 生成 + 人工上传"双轨模式，AI 生成仅作辅助候选，不影响后续 Wwise/UE/QA 链路 |
| **视频理解准确度** | 高 | Intent 生成模块 | MVP 降级为"辅助标注"而非"自动决策"，策划需手动填写关键 timing_points |
| **UE 弱语义匹配准确率** | 高 | UE 挂接模块 | MVP 仅用强规则匹配，弱语义匹配结果一律标记 review_required，不自动提交 |
| **Wwise 模板设计质量** | 中 | Wwise 自动化模块 | 模板由资深音频 TA 在前期精心设计并经审批；模板版本化管理 |
| **Profile 数据获取稳定性** | 中 | QA 诊断模块 | Profile 缺失时标记 ProfileUnavailable；支持人工补充；QA 检测目标 ≥ 80% 获取成功率 |
| **UE 版本间接口差异** | 中 | UE 挂接模块 | 通过适配器层封装 UE API，版本差异在适配器内处理 |
| **规则库建设不完整** | 中 | 全系统 | 规则库由音频负责人在 M1 阶段完成并审批，系统对缺失规则给出明确警告而非静默失败 |
| **项目资源命名不规范** | 中 | UE 挂接 + 映射 | Mapping Dictionary 支持正则/通配符匹配；未匹配项进入人工队列 |
| **Wwise WAAPI 连接中断** | 低 | Wwise 自动化模块 | 长连接心跳检测 + 指数退避重连（最多 5 次）；失败任务可手动重试 |
| **AI 生成素材一致性** | 中 | 素材生成模块 | QC 环节强制检测；不通过则阻断；保留人工替代路径 |

---

## 12. MVP 功能边界

### 12.1 做什么 / 不做什么 总结表

| 维度 | MVP 做 | MVP 不做 |
|------|--------|---------|
| 资产类型 | 动作 SFX、UI 音效、简单环境循环 | VO、音乐、复杂交互音效 |
| 项目模板 | 动作游戏模板 1 套 | RPG/开放世界/卡通等模板 |
| 视频理解 | 时长提取、基础节奏检测 + 降级模式（策划手动标注） | 深度动作语义识别、自动材质判断 |
| AI 音频生成 | 3 个候选 + 人工上传替代路径 | 高品质商业级原创音乐 |
| 后处理 | trim、fade、响度标准化、基础频段检测 | 复杂母带处理 |
| QC | 8 项指标自动检测 | 主观听感评估 |
| Wwise 对象 | Sound SFX、Random Container、Actor-Mixer、Event、Bank | Music Segment/Playlist、复杂 State/Switch/RTPC、Snapshot |
| UE 挂接 | AnimNotify/AkComponent 强规则匹配 | 弱语义匹配（P1）、复杂蓝图逻辑 |
| 审批 | 单节点合并审批 | 双节点分离审批（P1） |
| 回滚 | 素材版本手动回滚 + 重新执行链路 | Wwise/UE 状态精确自动回滚（P1） |
| QA 诊断 | 9 种常见问题自动诊断 | 自动修复（P2）、复杂混音链路诊断 |
| 界面 | 任务提交/详情/审批/诊断/后台配置 | 批量任务面板（P2）、可视化仪表盘 |
| 批量操作 | UI 批量任务导入（P1） | 复杂批次管理 |

### 12.2 MVP 里程碑

| 里程碑 | 周期 | 目标 |
|--------|------|------|
| **M1 规则建制** | Sprint 1-2（4 周） | Style Bible v1、Category Rules v1、动作游戏模板、Mapping Dictionary v1、后台配置页 |
| **M2 主链路跑通** | Sprint 3-5（6 周） | 需求提交→生成→QC→Wwise→UE→审批完整链路 |
| **M3 QA 闭环** | Sprint 6-7（4 周） | Profile 自动抓取、5 类问题检测、诊断链路 |
| **M4 内部试运行** | Sprint 8（2 周） | 15-20 个真实任务端到端试跑，输出量化指标和复盘报告 |

### 12.3 MVP 成功标准

- 至少打通 1 条完整链路：需求输入 → 素材生成 → Wwise 导入 → UE 挂接 → QA 检测
- 支持 3 类标准化资产
- 支持 1 套项目模板（动作游戏）
- 关键结果具备任务追踪、审批记录和回滚能力
- QA 能自动识别至少 5 类常见问题

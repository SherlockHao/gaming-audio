# AI 游戏音频生产与集成系统 FSD v0.1

## 1. 文档目标

本文件用于描述 AI 游戏音频生产与集成系统在 MVP 阶段的功能规格，覆盖系统模块、输入输出、数据流、状态机、接口边界、异常流和非功能需求，作为研发实现与技术评审基础。

关联文档：

- [AI_Game_Audio_PRD_v0.1.md](AI_Game_Audio_PRD_v0.1.md)
- [AI_Game_Audio_MVP_v0.1.md](AI_Game_Audio_MVP_v0.1.md)

---

## 2. 系统概览

系统由七个核心模块组成：

1. 需求输入模块
2. 需求结构化与 Intent 生成模块
3. 素材生成与 QC 模块
4. Wwise 自动化模块
5. UE 自动挂接模块
6. 审批追踪回滚模块
7. QA 与诊断模块

系统核心原则：

- 规则先于生成
- 模板先于派生
- 追踪先于自动化
- 审批先于入库

---

## 3. 架构边界

### 3.1 系统内职责

- 接收任务
- 管理规则与模板
- 生成结构化意图
- 编排音频生成流程
- 执行 Wwise 自动化
- 执行 UE 自动挂接
- 记录状态、版本和审计日志
- 执行 QA 检测与诊断

### 3.2 系统外依赖

- 音频生成能力提供方
- 音频基础处理能力提供方
- Wwise Authoring / WAAPI / Wwise Console
- Unreal Editor 工具能力
- 自动化跑测系统
- 文件存储与任务存储系统

---

## 4. 模块规格

### 4.1 需求输入模块

**目标**

- 用低门槛方式接收音频需求
- 将非结构化输入整理为标准任务

**输入**

- 任务名称
- 资源类型
- 场景语义
- 播放方式
- 标签
- 输入素材引用
- 备注

**输出**

- Task
- InputAssetRef
- 提交日志

**功能点**

- 创建任务
- 编辑任务
- 上传或关联输入素材
- 校验必填字段
- 分配 task_id

**校验规则**

- 必须选择资源类型
- 必须提供至少一个输入素材或资源引用
- 必须选择播放方式
- 场景语义不能为空

**失败处理**

- 字段缺失时阻止提交
- 输入素材不可读取时标记为 invalid_input

### 4.2 需求结构化与 Intent 生成模块

**目标**

- 将任务转换为后续模块可执行的结构化音频意图

**输入**

- Task
- InputAssetRef
- Style Bible
- Category Rules
- Mapping Dictionary

**输出**

- StructuredRequest
- AudioIntentSpec
- UnresolvedFields

**功能点**

- 解析任务字段
- 提取输入素材基本特征
- 根据规则生成 spec
- 计算置信度
- 标记待确认字段

**关键逻辑**

- 依据资源类型决定默认类别
- 依据播放方式决定 loop_required
- 依据场景语义估算 intensity 和 design_pattern
- 依据模板映射输出 wwise_template_id 与 ue_binding_strategy

**失败处理**

- 若置信度低于阈值，任务进入 `SpecReviewPending`
- 若缺少匹配规则，记录 unresolved_fields

### 4.3 素材生成与 QC 模块

**目标**

- 生成候选音频并输出基础合规版本

**输入**

- AudioIntentSpec
- Category Rules
- Style Bible
- 输入素材

**输出**

- CandidateAudio[]
- ProcessedAudio[]
- QcReport

**功能点**

- 生成多个候选音频
- 执行切头尾、淡入淡出、响度标准化
- 进行基础频段与格式检测
- 输出可导入版本

**规则**

- 默认生成 3 个候选
- 每个候选必须写入 version 和 generation_params
- QC 不通过时不得进入 Wwise 导入流程

**失败处理**

- 生成失败进入 `AudioGenerationFailed`
- QC 不通过进入 `QCFailed`

### 4.4 Wwise 自动化模块

**目标**

- 通过模板和规则完成对象创建、导入和 Bank 生成

**输入**

- AudioIntentSpec
- ProcessedAudio[]
- WwiseTemplate
- Category Rules

**输出**

- WwiseObjectManifest
- ImportManifest
- BankManifest
- BuildLog

**功能点**

- 选择模板
- 解析对象目标路径
- 创建或获取目标对象
- 导入音频
- 创建 Event
- 设置基础 Bus 和命名
- 生成 SoundBank

**关键逻辑**

- 相同类型任务进入固定 hierarchy 路径
- Event 命名遵循规则模板
- 若目标容器已存在则执行更新或增量导入

**失败处理**

- 导入失败进入 `WwiseImportFailed`
- Bank 生成失败进入 `BankBuildFailed`

### 4.5 UE 自动挂接模块

**目标**

- 将 Wwise Event 自动绑定到 UE 中的目标对象

**输入**

- AudioIntentSpec
- BindingRules
- Wwise Event 信息
- UE AssetRef

**输出**

- BindingManifest
- NotifyMappingReport
- UnresolvedBindingQueue

**功能点**

- 规则匹配目标资产
- 生成挂接方案
- 写入 AnimNotify 或组件绑定
- 输出匹配结果和置信度

**关键逻辑**

- 先做强规则匹配
- 未命中则做弱语义匹配
- 低置信度不自动提交，进入待审队列

**失败处理**

- 挂接失败进入 `UEBindFailed`
- 匹配失败进入 `BindingReviewPending`

### 4.6 审批追踪回滚模块

**目标**

- 记录全过程状态和关键变更
- 提供审批和回滚基础能力

**输入**

- 任务状态变化
- 资产版本变化
- Wwise/UE 清单变化
- QA 结果

**输出**

- AuditLog
- VersionRecord
- ReviewRecord
- RollbackPoint

**功能点**

- 记录状态变更
- 记录版本信息
- 保存关键清单
- 创建审批节点
- 执行回滚

**回滚范围**

- 素材版本
- Wwise 对象导入状态
- UE 绑定状态

### 4.7 QA 与诊断模块

**目标**

- 从自动化跑测和 profile 数据中发现问题并定位疑似根因

**输入**

- 自动化跑测结果
- Profile Capture
- WwiseObjectManifest
- BindingManifest
- 问题描述

**输出**

- QaReport
- QaIssue[]
- DiagnosisReport

**功能点**

- 抓取 profile/capture
- 读取关键事件、voice 和对象状态
- 检测常见问题
- 根据时间点和对象做反查诊断

**支持问题类型**

- Event 未触发
- Event 触发但无 Voice
- Voice 被 Kill
- Voice 被 Virtualize
- RTPC 导致音量异常
- Bank 未加载
- Media 缺失
- 映射对象错误

**失败处理**

- Profile 缺失时记录 `ProfileUnavailable`
- 诊断失败时记录 `DiagnosisIncomplete`

---

## 5. 数据模型

### 5.1 Task

- task_id
- project_id
- title
- requester
- asset_type
- semantic_scene
- play_mode
- tags
- notes
- status
- created_at
- updated_at

### 5.2 InputAssetRef

- input_asset_id
- task_id
- asset_kind
- asset_path
- asset_version
- checksum

### 5.3 AudioIntentSpec

- intent_id
- task_id
- content_type
- semantic_role
- intensity
- material_hint
- timing_points
- loop_required
- variation_count
- design_pattern
- category_rule_id
- wwise_template_id
- ue_binding_strategy
- confidence

### 5.4 CandidateAudio

- candidate_id
- task_id
- version
- source_model
- generation_params
- file_path
- duration_ms

### 5.5 QcReport

- qc_report_id
- task_id
- asset_id
- peak_result
- loudness_result
- spectrum_result
- head_tail_result
- format_result
- qc_status

### 5.6 WwiseObjectManifest

- manifest_id
- task_id
- object_entries[]

`object_entries` 字段包含：

- object_type
- object_path
- source_audio_path
- event_name
- bus_name
- bank_name
- operation_type

### 5.7 BindingManifest

- binding_manifest_id
- task_id
- bindings[]

`bindings` 字段包含：

- target_asset_path
- binding_type
- event_name
- confidence
- review_required

### 5.8 QaIssue

- qa_issue_id
- task_id
- timestamp
- issue_type
- related_actor
- related_skill
- related_event
- root_cause_guess
- evidence_refs
- resolution_status

---

## 6. 状态机

### 6.1 任务主状态机

- Draft
- Submitted
- SpecGenerated
- SpecReviewPending
- AudioGenerated
- AudioGenerationFailed
- QCReady
- QCFailed
- WwiseImported
- WwiseImportFailed
- BankBuilt
- BankBuildFailed
- UEBound
- UEBindFailed
- BindingReviewPending
- QARun
- ReviewPending
- Approved
- Rejected
- RolledBack

### 6.2 状态流转规则

- `Submitted -> SpecGenerated`
  条件：spec 成功生成且置信度达标
- `Submitted -> SpecReviewPending`
  条件：spec 生成但存在关键 unresolved 字段
- `SpecGenerated -> AudioGenerated`
  条件：候选音频生成成功
- `AudioGenerated -> QCReady`
  条件：至少一个候选通过 QC
- `AudioGenerated -> QCFailed`
  条件：全部候选未通过 QC
- `QCReady -> WwiseImported`
  条件：Wwise 导入成功
- `WwiseImported -> BankBuilt`
  条件：Bank 生成成功
- `BankBuilt -> UEBound`
  条件：UE 绑定成功
- `UEBound -> QARun`
  条件：自动化 QA 完成
- `QARun -> ReviewPending`
  条件：生成 QA 报告
- `ReviewPending -> Approved`
  条件：审批通过
- `ReviewPending -> Rejected`
  条件：审批拒绝
- `Rejected -> RolledBack`
  条件：执行回滚成功

---

## 7. 核心流程规格

### 7.1 流程 A：标准动作音效链路

1. 用户创建任务
2. 系统校验输入
3. 生成 AudioIntentSpec
4. 生成 3 个候选音频
5. 执行 QC
6. 选择通过版本进入 Wwise
7. 派生路径并导入
8. 创建 Event 和 Bank
9. 执行 UE 挂接
10. 触发自动化 QA
11. 输出任务报告
12. 进入审批

### 7.2 流程 B：问题诊断链路

1. 用户输入时间点和问题说明
2. 系统定位 profile 记录
3. 匹配目标对象和 Event
4. 校验触发与 voice 生命周期
5. 查询音量与通路贡献
6. 输出疑似根因和证据

---

## 8. 接口规格

以下为逻辑接口定义，实际可由服务接口、脚本接口或任务编排器实现。

### 8.1 CreateTask

**输入**

- title
- asset_type
- semantic_scene
- play_mode
- tags
- asset_refs
- notes

**输出**

- task_id
- status

### 8.2 GenerateIntentSpec

**输入**

- task_id

**输出**

- intent_id
- confidence
- unresolved_fields

### 8.3 GenerateAudioCandidates

**输入**

- intent_id

**输出**

- candidate_ids[]
- generation_log

### 8.4 RunAudioQC

**输入**

- candidate_ids[]

**输出**

- qc_report_ids[]
- passed_candidate_ids[]

### 8.5 ImportToWwise

**输入**

- task_id
- selected_audio_id

**输出**

- wwise_manifest_id
- import_status

### 8.6 BuildBank

**输入**

- task_id

**输出**

- bank_manifest_id
- build_status

### 8.7 BindInUE

**输入**

- task_id

**输出**

- binding_manifest_id
- unresolved_bindings[]

### 8.8 RunAudioQA

**输入**

- task_id

**输出**

- qa_report_id
- qa_issue_ids[]

### 8.9 DiagnoseIssue

**输入**

- task_id
- timestamp
- issue_description

**输出**

- diagnosis_report_id
- root_cause_guess
- evidence_refs

---

## 9. 规则引擎规格

### 9.1 规则层级

- Project Level Rule
- Template Level Rule
- Category Level Rule
- Task Override

优先级从高到低：

1. Task Override
2. Category Level Rule
3. Template Level Rule
4. Project Level Rule

### 9.2 规则冲突处理

- 高优先级覆盖低优先级
- 冲突规则须记录到 audit log
- 关键字段冲突进入 review pending

---

## 10. 日志与审计规格

### 10.1 必须记录的日志

- 任务创建日志
- spec 生成日志
- 音频生成日志
- QC 日志
- Wwise 导入日志
- Bank 生成日志
- UE 挂接日志
- QA 执行日志
- 诊断执行日志
- 审批日志
- 回滚日志

### 10.2 审计要求

- 每个关键步骤必须可定位责任人或调用来源
- 每次修改都必须保留时间戳
- 每次失败都必须保留错误原因和上下文

---

## 11. 异常流规格

### 11.1 输入异常

- 输入素材无法读取
- 缺少必填字段
- 资源类型不支持

处理：

- 阻止任务提交或转为 invalid_input

### 11.2 生成异常

- 候选生成失败
- 生成结果为空

处理：

- 标记 AudioGenerationFailed
- 允许重新执行

### 11.3 QC 异常

- 所有候选不合规

处理：

- 标记 QCFailed
- 阻止进入导入流程

### 11.4 Wwise 异常

- 路径创建失败
- 导入失败
- Event 创建失败
- Bank 生成失败

处理：

- 记录失败对象
- 停止后续链路

### 11.5 UE 异常

- 目标资源未找到
- 写入通知失败
- 匹配结果低置信度

处理：

- 进入 unresolved queue 或 BindingReviewPending

### 11.6 QA 异常

- 未拿到 profile
- capture 与任务时间点无法对齐

处理：

- 标记 ProfileUnavailable
- 允许人工补充定位信息

---

## 12. 非功能需求

### 12.1 可追踪性

- 所有任务、资产、对象和问题必须具备唯一 ID

### 12.2 可恢复性

- 任一关键步骤失败后，系统需保留可恢复状态

### 12.3 可配置性

- 风格规则、类别规则、模板和映射应可版本化配置

### 12.4 可扩展性

- 后续可扩展到 VO、音乐和更复杂的 Wwise/UE 接入场景

### 12.5 可审计性

- 所有关键操作必须能形成审计记录

---

## 13. 开发拆分建议

### 13.1 服务拆分

- Task Service
- Rule Service
- Audio Pipeline Service
- Wwise Integration Service
- UE Binding Service
- QA Diagnostics Service
- Review & Audit Service

### 13.2 实施顺序

1. 任务与规则
2. spec 生成
3. 音频生成与 QC
4. Wwise 导入与 Bank
5. UE 挂接
6. QA 抓取与诊断
7. 审批回滚

---

## 14. 开放问题

- 输入视频理解是否由独立服务承担
- 规则和模板是否采用配置文件形式还是后台管理
- UE 挂接是否优先支持 Editor 脚本还是插件
- QA 与现有自动化平台通过何种协议或任务编排接入
- 审批与回滚记录是否需要与项目管理系统联动


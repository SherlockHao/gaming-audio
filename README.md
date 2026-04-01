# AI 游戏音频生产与集成系统

面向游戏开发中前期的 AI 音频流水线 —— 从需求提交到 Wwise/UE 集成再到 QA 诊断的端到端自动化系统。

## 项目定位

由专业音频人员前置建制规则和模板后，利用 AI 接管中前期标准化音频生产和集成工作，让策划通过"上传视频 + 打标签"的低门槛方式触发全链路自动化流程。

**三阶段使用模式：**

1. **音频前置建制期** — 专业音频人员建立风格规范、Wwise 模板、UE mapping 规则
2. **AI 量产迭代期** — 策划低门槛输入，系统自动完成标准化音频生产与集成
3. **人工精修收尾期** — 正式音频团队接管高质量替换与终混

## 核心链路

```
策划提交需求 → 视频理解 → Audio Intent Spec → AI 生成候选音频(x3)
→ 后处理/QC → Wwise 导入(对象/Event/Bank) → UE AnimNotify 挂接
→ 自动化 QA + Profile 诊断 → 审批/回滚
```

## MVP 范围

- **资产类型：** 动作 SFX、UI 音效、简单环境循环
- **项目模板：** 动作游戏模板
- **QA 能力：** Event 未触发、Voice 被 Kill、RTPC 拉零、Bank 未加载、Media 缺失等 5+ 类问题自动诊断

## 技术栈

| 层面 | 技术选型 |
|------|---------|
| 后端 | Python 3.11+ / FastAPI / PostgreSQL / Celery / Redis / MinIO |
| 前端 | Next.js 14 / Ant Design 5 / TanStack Query / Zustand |
| 音频处理 | FFmpeg / librosa / pyloudnorm / pydub |
| Wwise 集成 | WAAPI (waapi-client) / WebSocket |
| UE 集成 | Python Editor Scripting + C++ Editor Utility |
| AI 生成 | 多模态大模型 (视频理解) + 音频生成 API |

## 项目文档

| 文档 | 说明 |
|------|------|
| [AI_Game_Audio_PRD_v0.1.md](AI_Game_Audio_PRD_v0.1.md) | 产品需求文档 |
| [AI_Game_Audio_FSD_v0.1.md](AI_Game_Audio_FSD_v0.1.md) | 功能规格文档 |
| [AI_Game_Audio_MVP_v0.1.md](AI_Game_Audio_MVP_v0.1.md) | MVP 需求清单 |
| [architecture.md](architecture.md) | 整体架构文档 |
| [execution-plan.md](execution-plan.md) | MVP 执行计划 (8 Sprint / 16 周) |

## Agent 团队

项目配备 7 个 AI Agent 角色（定义在 `.claude/agents/`），通过 Claude Code 的 `/agent` 命令调用：

| Agent | 职责 |
|-------|------|
| **Director** (总导演) | 任务分发、协调、进度跟踪、质量把关 |
| **PM** (产品经理) | 需求分析、优先级排序、用户故事、验收标准 |
| **Audio Designer** (音频设计师) | 风格规范、Category Rules、Wwise 模板、QC 规则 |
| **Backend Dev** (后端开发) | 服务架构、API、数据模型、状态机、规则引擎 |
| **Audio Engineer** (音频工程) | WAAPI 自动化、UE 挂接、音频管线、Profile 诊断 |
| **Frontend Dev** (前端开发) | 页面设计、音频组件、实时更新、文件上传 |
| **QA** (测试) | 测试策略、自动化 QA、诊断系统、CI/CD 门禁 |

## MVP 里程碑

| 里程碑 | 周期 | 目标 |
|--------|------|------|
| M1 规则建制 | Sprint 1-2 (第 1-4 周) | Style Bible + Category Rules + Wwise 模板 + Mapping 字典 |
| M2 主链路跑通 | Sprint 3-5 (第 5-10 周) | 需求 → 生成 → Wwise → UE → 审批 端到端可用 |
| M3 QA 闭环 | Sprint 6-7 (第 11-14 周) | Profile 抓取 + 5 类问题自动诊断 |
| M4 内部试运行 | Sprint 8 (第 15-16 周) | 真实场景试跑 + 复盘报告 |

"use client";

import { Button, Card, Descriptions, Space, Steps, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useParams } from "next/navigation";
import { useTask, useIntentSpec, useAuditLogs, useGenerateIntent, useCandidates, useGenerateAudio, useSelectCandidate, useWwiseManifest, useImportWwise, useBuildBank, useRunQc } from "@/lib/hooks";
import { useTaskSSE } from "@/lib/useTaskSSE";
import { STATUS_COLORS, PIPELINE_STEPS } from "@/lib/constants";
import type { CandidateAudio } from "@/lib/types";

export default function TaskDetailPage() {
  const params = useParams<{ taskId: string }>();
  const taskId = params.taskId as string;
  const { data: task, isLoading: taskLoading } = useTask(taskId);
  const { data: spec } = useIntentSpec(taskId);
  const { data: logs = [] } = useAuditLogs(taskId);
  const generateIntent = useGenerateIntent();

  const { data: candidates = [] } = useCandidates(taskId);
  const { data: wwiseManifest } = useWwiseManifest(taskId);
  const generateAudio = useGenerateAudio();
  const selectCandidate = useSelectCandidate();
  const importWwise = useImportWwise();
  const buildBank = useBuildBank();
  const runQc = useRunQc();

  useTaskSSE(taskId);

  if (taskLoading) return <div style={{ padding: 24 }}>Loading...</div>;
  if (!task) return <div style={{ padding: 24 }}>Task not found</div>;

  const currentStepIndex = PIPELINE_STEPS.indexOf(task.status);
  const isFailed = task.status.includes("Failed");
  const isPending = task.status.includes("Pending");

  const handleGenerateIntent = async () => {
    try {
      await generateIntent.mutateAsync(taskId);
      message.success("Intent spec generated");
    } catch (e) {
      message.error(e instanceof Error ? e.message : "Failed to generate intent");
    }
  };

  const handleGenerateAudio = async () => {
    try {
      await generateAudio.mutateAsync(taskId);
      message.success("Audio candidates generated");
    } catch (e) {
      message.error(e instanceof Error ? e.message : "Failed to generate audio");
    }
  };

  const handleSelectCandidate = async (candidateId: string) => {
    try {
      await selectCandidate.mutateAsync({ taskId, candidateId });
      message.success("Candidate selected");
    } catch (e) {
      message.error(e instanceof Error ? e.message : "Failed to select candidate");
    }
  };

  const handleImportWwise = async () => {
    try {
      await importWwise.mutateAsync(taskId);
      message.success("Imported to Wwise");
    } catch (e) {
      message.error(e instanceof Error ? e.message : "Failed to import to Wwise");
    }
  };

  const handleBuildBank = async () => {
    try {
      await buildBank.mutateAsync(taskId);
      message.success("Bank built");
    } catch (e) {
      message.error(e instanceof Error ? e.message : "Failed to build bank");
    }
  };

  const handleRunQc = async () => {
    try {
      await runQc.mutateAsync(taskId);
      message.success("QC completed");
    } catch (e) {
      message.error(e instanceof Error ? e.message : "QC failed");
    }
  };

  const candidateColumns: ColumnsType<CandidateAudio> = [
    { title: "Version", dataIndex: "version", key: "version", width: 80 },
    { title: "File", dataIndex: "file_path", key: "file_path",
      render: (v: string) => <Typography.Text code style={{ fontSize: 11 }}>{v.split("/").pop()}</Typography.Text>,
    },
    { title: "Model", dataIndex: "source_model", key: "source_model", render: (v: string | null) => v || "-" },
    {
      title: "Duration (ms)",
      dataIndex: "duration_ms",
      key: "duration_ms",
      render: (v: number | null) => (v !== null ? v : "-"),
    },
    { title: "Stage", dataIndex: "stage", key: "stage" },
    {
      title: "Selected",
      dataIndex: "selected",
      key: "selected",
      render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "Yes" : "No"}</Tag>,
    },
    {
      title: "Action",
      key: "action",
      render: (_: unknown, record: CandidateAudio) => (
        <Button
          size="small"
          type={record.selected ? "default" : "primary"}
          disabled={record.selected || selectCandidate.isPending}
          onClick={() => handleSelectCandidate(record.candidate_id)}
        >
          {record.selected ? "Selected" : "Select"}
        </Button>
      ),
    },
  ];

  const showGenerateAudio = task.status === "SpecGenerated";
  const showCandidates =
    candidates.length > 0 ||
    ["AudioGenerated", "QCReady", "WwiseImported", "BankBuilt", "UEBound", "QARun", "ReviewPending", "Approved"].includes(task.status);
  const showImportWwise = task.status === "QCReady";
  const showBuildBank = task.status === "WwiseImported";

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
      <Space style={{ marginBottom: 16 }} align="center">
        <Typography.Title level={3} style={{ margin: 0 }}>{task.title}</Typography.Title>
        <Tag color={STATUS_COLORS[task.status] || "default"}>{task.status}</Tag>
      </Space>

      {/* Pipeline Timeline */}
      <Card title="Pipeline Status" style={{ marginBottom: 16 }}>
        <Steps
          current={currentStepIndex >= 0 ? currentStepIndex : 0}
          status={isFailed ? "error" : isPending ? "wait" : "process"}
          size="small"
          items={PIPELINE_STEPS.map((step) => ({
            title: step.replace(/([A-Z])/g, " $1").trim(),
          }))}
        />
      </Card>

      {/* Task Info */}
      <Card title="Task Details" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Task ID">{task.task_id}</Descriptions.Item>
          <Descriptions.Item label="Requester">{task.requester}</Descriptions.Item>
          <Descriptions.Item label="Asset Type"><Tag color="blue">{task.asset_type}</Tag></Descriptions.Item>
          <Descriptions.Item label="Scene">{task.semantic_scene}</Descriptions.Item>
          <Descriptions.Item label="Play Mode"><Tag>{task.play_mode}</Tag></Descriptions.Item>
          <Descriptions.Item label="Priority">{task.priority}</Descriptions.Item>
          <Descriptions.Item label="Tags" span={2}>
            {task.tags?.map((t) => <Tag key={t}>{t}</Tag>) || "-"}
          </Descriptions.Item>
          {task.notes && <Descriptions.Item label="Notes" span={2}>{task.notes}</Descriptions.Item>}
          <Descriptions.Item label="Created">{new Date(task.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Updated">{new Date(task.updated_at).toLocaleString()}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Actions */}
      {task.status === "Submitted" && (
        <Card title="Actions" style={{ marginBottom: 16 }}>
          <Button type="primary" onClick={handleGenerateIntent} loading={generateIntent.isPending}>
            Generate Intent Spec
          </Button>
        </Card>
      )}

      {/* Intent Spec */}
      {spec && (
        <Card title={`Intent Spec (confidence: ${spec.confidence})`} style={{ marginBottom: 16 }}>
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="Content Type">{spec.content_type}</Descriptions.Item>
            <Descriptions.Item label="Semantic Role">{spec.semantic_role || "-"}</Descriptions.Item>
            <Descriptions.Item label="Intensity"><Tag color={spec.intensity === "heavy" ? "red" : spec.intensity === "medium" ? "orange" : "blue"}>{spec.intensity || "-"}</Tag></Descriptions.Item>
            <Descriptions.Item label="Material Hint">{spec.material_hint || "-"}</Descriptions.Item>
            <Descriptions.Item label="Loop Required">{spec.loop_required ? "Yes" : "No"}</Descriptions.Item>
            <Descriptions.Item label="Variations">{spec.variation_count}</Descriptions.Item>
            <Descriptions.Item label="UE Binding">{spec.ue_binding_strategy || "-"}</Descriptions.Item>
            <Descriptions.Item label="Confidence">
              <Tag color={spec.confidence && spec.confidence >= 0.6 ? "green" : "red"}>
                {spec.confidence?.toFixed(3)}
              </Tag>
            </Descriptions.Item>
            {spec.unresolved_fields && spec.unresolved_fields.length > 0 && (
              <Descriptions.Item label="Unresolved" span={2}>
                {spec.unresolved_fields.map((f) => <Tag color="orange" key={f}>{f}</Tag>)}
              </Descriptions.Item>
            )}
          </Descriptions>
        </Card>
      )}

      {/* Generate Audio button */}
      {showGenerateAudio && (
        <Card title="Audio Generation" style={{ marginBottom: 16 }}>
          <Button type="primary" onClick={handleGenerateAudio} loading={generateAudio.isPending}>
            Generate Audio
          </Button>
        </Card>
      )}

      {/* Run QC button */}
      {task.status === "AudioGenerated" && (
        <Card title="Actions" style={{ marginBottom: 16 }}>
          <Button type="primary" onClick={handleRunQc} loading={runQc.isPending}>
            Run QC Check
          </Button>
        </Card>
      )}

      {/* Audio Candidates */}
      {showCandidates && (
        <Card title="Audio Candidates" style={{ marginBottom: 16 }}>
          <Table<CandidateAudio>
            dataSource={candidates}
            columns={candidateColumns}
            rowKey="candidate_id"
            size="small"
            pagination={false}
            locale={{ emptyText: "No candidates yet" }}
          />
        </Card>
      )}

      {/* Wwise Import button */}
      {showImportWwise && (
        <Card title="Wwise Integration" style={{ marginBottom: 16 }}>
          <Button type="primary" onClick={handleImportWwise} loading={importWwise.isPending}>
            Import to Wwise
          </Button>
        </Card>
      )}

      {/* Build Bank button */}
      {showBuildBank && (
        <Card title="Wwise Bank" style={{ marginBottom: 16 }}>
          <Button type="primary" onClick={handleBuildBank} loading={buildBank.isPending}>
            Build Bank
          </Button>
        </Card>
      )}

      {/* Wwise Manifest */}
      {wwiseManifest && (
        <Card title={`Wwise Manifest (v${wwiseManifest.version} — ${wwiseManifest.import_status})`} style={{ marginBottom: 16 }}>
          <Typography.Text strong>Object Entries</Typography.Text>
          <pre style={{ background: "#f5f5f5", padding: 12, borderRadius: 4, overflowX: "auto", fontSize: 12, marginTop: 8, marginBottom: 16 }}>
            {JSON.stringify(wwiseManifest.object_entries, null, 2)}
          </pre>
          {wwiseManifest.build_log && (
            <>
              <Typography.Text strong>Build Log</Typography.Text>
              <pre style={{ background: "#f5f5f5", padding: 12, borderRadius: 4, overflowX: "auto", fontSize: 12, marginTop: 8 }}>
                {wwiseManifest.build_log}
              </pre>
            </>
          )}
        </Card>
      )}

      {/* Audit Log */}
      {logs.length > 0 && (
        <Card title="Audit Log">
          {logs.map((log) => (
            <div key={log.log_id} style={{ padding: "4px 0", borderBottom: "1px solid #f0f0f0", fontSize: 13 }}>
              <Tag>{log.action}</Tag>
              <span style={{ color: "#999" }}>{new Date(log.created_at).toLocaleString()}</span>
              {log.old_state && <span> {log.old_state} -&gt; {log.new_state}</span>}
              <span style={{ marginLeft: 8 }}>by {log.actor}</span>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

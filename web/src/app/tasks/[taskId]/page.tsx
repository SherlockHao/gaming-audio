"use client";

import { Button, Card, Descriptions, Space, Steps, Tag, Typography, message } from "antd";
import { useParams } from "next/navigation";
import { useTask, useIntentSpec, useAuditLogs, useGenerateIntent } from "@/lib/hooks";

const STATUS_COLORS: Record<string, string> = {
  Draft: "default", Submitted: "processing", SpecGenerated: "success",
  SpecReviewPending: "warning", AudioGenerated: "success", AudioGenerationFailed: "error",
  QCReady: "success", QCFailed: "error", WwiseImported: "success", WwiseImportFailed: "error",
  BankBuilt: "success", BankBuildFailed: "error", UEBound: "success", UEBindFailed: "error",
  BindingReviewPending: "warning", QARun: "processing", ReviewPending: "warning",
  Approved: "success", Rejected: "error", RolledBack: "default",
};

// Main pipeline steps for timeline display
const PIPELINE_STEPS = [
  "Draft", "Submitted", "SpecGenerated", "AudioGenerated", "QCReady",
  "WwiseImported", "BankBuilt", "UEBound", "QARun", "ReviewPending", "Approved",
];

export default function TaskDetailPage() {
  const params = useParams<{ taskId: string }>();
  const taskId = params.taskId as string;
  const { data: task, isLoading: taskLoading } = useTask(taskId);
  const { data: spec } = useIntentSpec(taskId);
  const { data: logs = [] } = useAuditLogs(taskId);
  const generateIntent = useGenerateIntent();

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
            {task.tags?.map((t) => <Tag key={t}>{t}</Tag>) || "—"}
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
            <Descriptions.Item label="Semantic Role">{spec.semantic_role || "—"}</Descriptions.Item>
            <Descriptions.Item label="Intensity"><Tag color={spec.intensity === "heavy" ? "red" : spec.intensity === "medium" ? "orange" : "blue"}>{spec.intensity || "—"}</Tag></Descriptions.Item>
            <Descriptions.Item label="Material Hint">{spec.material_hint || "—"}</Descriptions.Item>
            <Descriptions.Item label="Loop Required">{spec.loop_required ? "Yes" : "No"}</Descriptions.Item>
            <Descriptions.Item label="Variations">{spec.variation_count}</Descriptions.Item>
            <Descriptions.Item label="UE Binding">{spec.ue_binding_strategy || "—"}</Descriptions.Item>
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

      {/* Audit Log */}
      {logs.length > 0 && (
        <Card title="Audit Log">
          {logs.map((log) => (
            <div key={log.log_id} style={{ padding: "4px 0", borderBottom: "1px solid #f0f0f0", fontSize: 13 }}>
              <Tag>{log.action}</Tag>
              <span style={{ color: "#999" }}>{new Date(log.created_at).toLocaleString()}</span>
              {log.old_state && <span> {log.old_state} → {log.new_state}</span>}
              <span style={{ marginLeft: 8 }}>by {log.actor}</span>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

"use client";

import { Button, Card, Form, Input, message, Radio, Select, Space, Typography, Upload } from "antd";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ProjectSelector } from "@/components/ProjectSelector";
import { useCreateTask, useSubmitTask } from "@/lib/hooks";
import type { TaskCreate } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const ASSET_TYPES = [
  { label: "SFX (动作/技能/特效)", value: "sfx" },
  { label: "UI 音效", value: "ui" },
  { label: "环境循环音", value: "ambience_loop" },
];

const SCENES = ["Boss", "Player", "Enemy", "Weapon", "SystemUI", "Navigation", "Confirm", "Environment"];
const TAG_OPTIONS = ["heavy", "light", "rare", "magic", "metal", "melee", "ranged"];

export default function TaskCreatePage() {
  const router = useRouter();
  const [form] = Form.useForm();
  const [projectId, setProjectId] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const createTask = useCreateTask();
  const submitTask = useSubmitTask();

  const buildTaskData = (values: Record<string, unknown>): TaskCreate => ({
    project_id: projectId,
    title: values.title as string,
    requester: values.requester as string,
    asset_type: values.asset_type as "sfx" | "ui" | "ambience_loop",
    semantic_scene: values.semantic_scene as string,
    play_mode: values.play_mode as "one_shot" | "loop",
    tags: values.tags as string[] | undefined,
    notes: values.notes as string | undefined,
    priority: (values.priority as number) || 0,
  });

  const uploadAsset = async (taskId: string) => {
    if (!uploadFile) return;
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("asset_kind", "video");
    await fetch(`${API_BASE}/tasks/${taskId}/upload`, {
      method: "POST",
      body: formData,
    });
  };

  const handleSaveDraft = async () => {
    if (!projectId) {
      message.error("Please select a project");
      return;
    }
    try {
      const values = await form.validateFields();
      const taskData = buildTaskData(values);
      const task = await createTask.mutateAsync(taskData);
      await uploadAsset(task.task_id);
      message.success("Draft saved");
      router.push(`/tasks/${task.task_id}`);
    } catch (e) {
      if (e instanceof Error) {
        message.error(e.message);
      }
    }
  };

  const handleSubmit = async (values: Record<string, unknown>) => {
    if (!projectId) {
      message.error("Please select a project");
      return;
    }
    try {
      const taskData = buildTaskData(values);
      const task = await createTask.mutateAsync(taskData);
      message.success("Task created");

      await submitTask.mutateAsync(task.task_id);
      message.success("Task submitted for processing");

      await uploadAsset(task.task_id);

      router.push(`/tasks/${task.task_id}`);
    } catch (e) {
      message.error(e instanceof Error ? e.message : "Failed to create task");
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
      <Typography.Title level={3}>Create Audio Task</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <ProjectSelector value={projectId} onChange={setProjectId} />
      </Card>

      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item name="title" label="Task Name" rules={[{ required: true }]}>
          <Input placeholder="e.g., Boss Slam Attack" />
        </Form.Item>

        <Form.Item name="requester" label="Requester" rules={[{ required: true }]}>
          <Input placeholder="Your name" />
        </Form.Item>

        <Form.Item name="asset_type" label="Asset Type" rules={[{ required: true }]}>
          <Select options={ASSET_TYPES} placeholder="Select type" />
        </Form.Item>

        <Form.Item name="semantic_scene" label="Scene Context" rules={[{ required: true }]}>
          <Select placeholder="Select scene">
            {SCENES.map((s) => <Select.Option key={s} value={s}>{s}</Select.Option>)}
          </Select>
        </Form.Item>

        <Form.Item name="play_mode" label="Play Mode" rules={[{ required: true }]} initialValue="one_shot">
          <Radio.Group>
            <Radio value="one_shot">One Shot</Radio>
            <Radio value="loop">Loop</Radio>
          </Radio.Group>
        </Form.Item>

        <Form.Item name="tags" label="Tags">
          <Select mode="multiple" placeholder="Select tags">
            {TAG_OPTIONS.map((t) => <Select.Option key={t} value={t}>{t}</Select.Option>)}
          </Select>
        </Form.Item>

        <Form.Item name="notes" label="Notes">
          <Input.TextArea rows={3} placeholder="Additional notes for audio team" />
        </Form.Item>

        <Form.Item name="priority" label="Priority" initialValue={0}>
          <Select options={[
            { label: "Low (0)", value: 0 },
            { label: "Normal (1)", value: 1 },
            { label: "High (2)", value: 2 },
            { label: "Urgent (3)", value: 3 },
          ]} />
        </Form.Item>

        <Form.Item label="Input Asset (Video/Animation)">
          <Upload.Dragger
            beforeUpload={(file) => {
              setUploadFile(file);
              return false; // prevent auto upload
            }}
            onRemove={() => setUploadFile(null)}
            maxCount={1}
            accept=".mp4,.mov,.avi,.wav,.webm"
          >
            <p>Click or drag file to upload</p>
            <p style={{ color: "#999", fontSize: 12 }}>Supports: MP4, MOV, AVI, WAV, WebM (max 500MB)</p>
          </Upload.Dragger>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button
              onClick={handleSaveDraft}
              loading={createTask.isPending}
              disabled={submitTask.isPending}
            >
              Save Draft
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={createTask.isPending || submitTask.isPending}
            >
              Create &amp; Submit
            </Button>
            <Button onClick={() => router.push("/tasks")}>Cancel</Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
}

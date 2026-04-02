"use client";

import { Card, Modal, Table, Tag, Typography, Button } from "antd";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface WwiseTemplate { template_id: string; project_id: string; name: string; template_type: string; template_body: Record<string, unknown>; version: number; is_active: boolean; }
interface Project { project_id: string; name: string; }

export default function WwiseTemplatesPage() {
  const [templates, setTemplates] = useState<WwiseTemplate[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [detail, setDetail] = useState<WwiseTemplate | null>(null);

  useEffect(() => { apiFetch<Project[]>("/projects").then(setProjects).catch(() => {}); }, []);
  useEffect(() => { if (projects.length > 0 && !selectedProject) setSelectedProject(projects[0].project_id); }, [projects, selectedProject]);
  useEffect(() => {
    if (selectedProject) apiFetch<WwiseTemplate[]>(`/projects/${selectedProject}/rules/wwise-templates`).then(setTemplates).catch(() => {});
  }, [selectedProject]);

  return (
    <div>
      <Typography.Title level={3}>Wwise Templates</Typography.Title>
      {projects.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <span>Project: </span>
          <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)} style={{ padding: "4px 8px" }}>
            {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
          </select>
        </Card>
      )}
      <Table dataSource={templates} columns={[
        { title: "Name", dataIndex: "name", key: "name" },
        { title: "Type", dataIndex: "template_type", key: "template_type", render: (v: string) => <Tag>{v}</Tag> },
        { title: "Version", dataIndex: "version", key: "version" },
        { title: "Action", key: "action", render: (_: unknown, r: WwiseTemplate) => <Button type="link" onClick={() => setDetail(r)}>View</Button> },
      ]} rowKey="template_id" pagination={false} />
      <Modal title="Template Detail" open={!!detail} onCancel={() => setDetail(null)} footer={null} width={700}>
        {detail && <pre style={{ maxHeight: 500, overflow: "auto" }}>{JSON.stringify(detail.template_body, null, 2)}</pre>}
      </Modal>
    </div>
  );
}

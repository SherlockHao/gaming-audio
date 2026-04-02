"use client";

import { Button, Card, Modal, Table, Tag, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface CategoryRule {
  rule_id: string;
  project_id: string;
  category: string;
  rule_level: string;
  rule_body: Record<string, unknown>;
  version: number;
  is_active: boolean;
}

interface Project {
  project_id: string;
  name: string;
}

export default function CategoryRulesPage() {
  const [rules, setRules] = useState<CategoryRule[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [detailRule, setDetailRule] = useState<CategoryRule | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<Project[]>("/projects").then(setProjects).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedProject) {
      setLoading(true);
      apiFetch<CategoryRule[]>(`/projects/${selectedProject}/rules/categories`)
        .then(setRules)
        .catch(() => message.error("Failed to load rules"))
        .finally(() => setLoading(false));
    }
  }, [selectedProject]);

  useEffect(() => {
    if (projects.length > 0 && !selectedProject) {
      setSelectedProject(projects[0].project_id);
    }
  }, [projects, selectedProject]);

  const columns = [
    { title: "Category", dataIndex: "category", key: "category", render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: "Level", dataIndex: "rule_level", key: "rule_level" },
    { title: "Version", dataIndex: "version", key: "version" },
    { title: "Active", dataIndex: "is_active", key: "is_active", render: (v: boolean) => v ? <Tag color="green">Active</Tag> : <Tag>Inactive</Tag> },
    {
      title: "Action",
      key: "action",
      render: (_: unknown, record: CategoryRule) => (
        <Button type="link" onClick={() => setDetailRule(record)}>View Detail</Button>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={3}>Category Rules</Typography.Title>
      {projects.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <span>Project: </span>
          <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)} style={{ padding: "4px 8px" }}>
            {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
          </select>
        </Card>
      )}
      <Table dataSource={rules} columns={columns} rowKey="rule_id" loading={loading} pagination={false} />
      <Modal title="Rule Detail" open={!!detailRule} onCancel={() => setDetailRule(null)} footer={null} width={700}>
        {detailRule && <pre style={{ maxHeight: 500, overflow: "auto" }}>{JSON.stringify(detailRule.rule_body, null, 2)}</pre>}
      </Modal>
    </div>
  );
}

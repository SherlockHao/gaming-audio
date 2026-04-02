"use client";

import { Card, Table, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface CategoryRule { rule_id: string; project_id: string; category: string; rule_level: string; rule_body: Record<string, unknown>; version: number; is_active: boolean; }
interface Project { project_id: string; name: string; }

export default function QaRulesPage() {
  const [rules, setRules] = useState<CategoryRule[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState("");

  useEffect(() => { apiFetch<Project[]>("/projects").then(setProjects).catch(() => {}); }, []);
  useEffect(() => { if (projects.length > 0 && !selectedProject) setSelectedProject(projects[0].project_id); }, [projects, selectedProject]);
  useEffect(() => {
    if (selectedProject) {
      apiFetch<CategoryRule[]>(`/projects/${selectedProject}/rules/categories?category=qa`).then(setRules).catch(() => {});
    }
  }, [selectedProject]);

  const qaEntries = rules.length > 0 ? Object.entries(rules[0].rule_body as Record<string, Record<string, unknown>>) : [];

  return (
    <div>
      <Typography.Title level={3}>QA Detection Rules</Typography.Title>
      {projects.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <span>Project: </span>
          <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)} style={{ padding: "4px 8px" }}>
            {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
          </select>
          {rules.length > 0 && <Tag color="blue" style={{ marginLeft: 12 }}>v{rules[0].version}</Tag>}
        </Card>
      )}
      <Table
        dataSource={qaEntries.map(([key, value]) => ({ key, ...value as Record<string, unknown> }))}
        columns={[
          { title: "Rule Key", dataIndex: "key", key: "key" },
          { title: "Description", dataIndex: "description", key: "description" },
          { title: "Severity", dataIndex: "severity", key: "severity", render: (v: string) => {
            const color = v === "critical" ? "red" : v === "high" ? "orange" : "blue";
            return <Tag color={color}>{v}</Tag>;
          }},
        ]}
        rowKey="key"
        pagination={false}
      />
    </div>
  );
}

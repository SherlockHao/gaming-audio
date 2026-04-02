"use client";

import { Select, Space, Typography } from "antd";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Project } from "@/lib/types";

interface ProjectSelectorProps {
  value: string;
  onChange: (projectId: string) => void;
}

export function ProjectSelector({ value, onChange }: ProjectSelectorProps) {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    apiFetch<Project[]>("/projects")
      .then(setProjects)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (projects.length > 0 && !value) {
      onChange(projects[0].project_id);
    }
  }, [projects, value, onChange]);

  return (
    <Space>
      <Typography.Text>Project:</Typography.Text>
      <Select
        value={value || undefined}
        onChange={onChange}
        style={{ minWidth: 200 }}
        placeholder="Select project"
        options={projects.map((p) => ({ label: p.name, value: p.project_id }))}
      />
    </Space>
  );
}

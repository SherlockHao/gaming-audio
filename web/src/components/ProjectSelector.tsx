"use client";

import { Select, Space, Typography } from "antd";
import { useEffect } from "react";
import { useProjects } from "@/lib/hooks";

interface ProjectSelectorProps {
  value: string;
  onChange: (projectId: string) => void;
}

export function ProjectSelector({ value, onChange }: ProjectSelectorProps) {
  const { data: projects = [], isLoading, error } = useProjects();

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
        placeholder={isLoading ? "Loading..." : "Select project"}
        loading={isLoading}
        status={error ? "error" : undefined}
        options={projects.map((p) => ({ label: p.name, value: p.project_id }))}
      />
    </Space>
  );
}

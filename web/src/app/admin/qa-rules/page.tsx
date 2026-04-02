"use client";

import { Card, Table, Tag, Typography } from "antd";
import { useState } from "react";
import { ProjectSelector } from "@/components/ProjectSelector";
import { useCategoryRules } from "@/lib/hooks";

export default function QaRulesPage() {
  const [selectedProject, setSelectedProject] = useState("");
  const { data: rules = [], isLoading } = useCategoryRules(selectedProject, "qa");

  const qaRule = rules.length > 0 ? rules[0] : null;
  const qaEntries = qaRule
    ? Object.entries(qaRule.rule_body as Record<string, Record<string, unknown>>).map(
        ([key, value]) => ({ key, ...(value as Record<string, unknown>) })
      )
    : [];

  return (
    <div>
      <Typography.Title level={3}>QA Detection Rules</Typography.Title>
      <Card size="small" style={{ marginBottom: 16 }}>
        <ProjectSelector value={selectedProject} onChange={setSelectedProject} />
        {qaRule && <Tag color="blue" style={{ marginLeft: 12 }}>v{qaRule.version}</Tag>}
      </Card>
      <Table
        dataSource={qaEntries}
        loading={isLoading}
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

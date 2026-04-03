"use client";

import { Button, Card, Modal, Table, Tag, Typography, message } from "antd";
import { useCallback, useEffect, useState } from "react";
import { ProjectSelector } from "@/components/ProjectSelector";
import { useCategoryRules } from "@/lib/hooks";
import type { CategoryRule } from "@/lib/types";

export default function CategoryRulesPage() {
  const [selectedProject, setSelectedProject] = useState("");
  const [detailRule, setDetailRule] = useState<CategoryRule | null>(null);
  const { data: rules = [], isLoading, error } = useCategoryRules(selectedProject);

  useEffect(() => {
    if (error) message.error("Failed to load rules");
  }, [error]);

  const columns = [
    { title: "Category", dataIndex: "category", key: "category", render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: "Level", dataIndex: "rule_level", key: "rule_level" },
    { title: "Version", dataIndex: "version", key: "version" },
    { title: "Active", dataIndex: "is_active", key: "is_active", render: (v: boolean) => v ? <Tag color="green">Active</Tag> : <Tag>Inactive</Tag> },
    {
      title: "Action", key: "action",
      render: (_: unknown, record: CategoryRule) => (
        <Button type="link" onClick={() => setDetailRule(record)}>View Detail</Button>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={3}>Category Rules</Typography.Title>
      <Card size="small" style={{ marginBottom: 16 }}>
        <ProjectSelector value={selectedProject} onChange={setSelectedProject} />
      </Card>
      <Table dataSource={rules} columns={columns} rowKey="rule_id" loading={isLoading} pagination={false} />
      <Modal title="Rule Detail" open={!!detailRule} onCancel={() => setDetailRule(null)} footer={null} width={700}>
        {detailRule && <pre style={{ maxHeight: 500, overflow: "auto" }}>{JSON.stringify(detailRule.rule_body, null, 2)}</pre>}
      </Modal>
    </div>
  );
}

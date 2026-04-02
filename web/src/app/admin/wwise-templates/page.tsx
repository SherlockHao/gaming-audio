"use client";

import { Button, Card, Modal, Table, Tag, Typography } from "antd";
import { useState } from "react";
import { ProjectSelector } from "@/components/ProjectSelector";
import { useWwiseTemplates } from "@/lib/hooks";
import type { WwiseTemplate } from "@/lib/types";

export default function WwiseTemplatesPage() {
  const [selectedProject, setSelectedProject] = useState("");
  const [detail, setDetail] = useState<WwiseTemplate | null>(null);
  const { data: templates = [], isLoading } = useWwiseTemplates(selectedProject);

  return (
    <div>
      <Typography.Title level={3}>Wwise Templates</Typography.Title>
      <Card size="small" style={{ marginBottom: 16 }}>
        <ProjectSelector value={selectedProject} onChange={setSelectedProject} />
      </Card>
      <Table dataSource={templates} columns={[
        { title: "Name", dataIndex: "name", key: "name" },
        { title: "Type", dataIndex: "template_type", key: "template_type", render: (v: string) => <Tag>{v}</Tag> },
        { title: "Version", dataIndex: "version", key: "version" },
        { title: "Action", key: "action", render: (_: unknown, r: WwiseTemplate) => <Button type="link" onClick={() => setDetail(r)}>View</Button> },
      ]} rowKey="template_id" loading={isLoading} pagination={false} />
      <Modal title="Template Detail" open={!!detail} onCancel={() => setDetail(null)} footer={null} width={700}>
        {detail && <pre style={{ maxHeight: 500, overflow: "auto" }}>{JSON.stringify(detail.template_body, null, 2)}</pre>}
      </Modal>
    </div>
  );
}

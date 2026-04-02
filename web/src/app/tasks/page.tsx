"use client";

import { Button, Card, Space, Table, Tag, Typography } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ProjectSelector } from "@/components/ProjectSelector";
import { useTasks } from "@/lib/hooks";
import { STATUS_COLORS } from "@/lib/constants";
import type { Task } from "@/lib/types";

export default function TasksPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const { data, isLoading } = useTasks(projectId, { offset: (page - 1) * pageSize, limit: pageSize });

  const columns = [
    { title: "Title", dataIndex: "title", key: "title",
      render: (title: string, record: Task) => (
        <a onClick={() => router.push(`/tasks/${record.task_id}`)}>{title}</a>
      ),
    },
    { title: "Type", dataIndex: "asset_type", key: "asset_type", render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: "Scene", dataIndex: "semantic_scene", key: "semantic_scene" },
    { title: "Status", dataIndex: "status", key: "status",
      render: (v: string) => <Tag color={STATUS_COLORS[v] || "default"}>{v}</Tag>,
    },
    { title: "Requester", dataIndex: "requester", key: "requester" },
    { title: "Created", dataIndex: "created_at", key: "created_at",
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ marginBottom: 16, width: "100%", justifyContent: "space-between" }}>
        <Typography.Title level={3} style={{ margin: 0 }}>Tasks</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => router.push("/tasks/create")}>
          New Task
        </Button>
      </Space>

      <Card size="small" style={{ marginBottom: 16 }}>
        <ProjectSelector value={projectId} onChange={setProjectId} />
      </Card>

      <Table
        dataSource={data?.items || []}
        columns={columns}
        rowKey="task_id"
        loading={isLoading}
        pagination={{
          current: page,
          total: data?.total || 0,
          pageSize,
          onChange: (p) => setPage(p),
        }}
      />
    </div>
  );
}

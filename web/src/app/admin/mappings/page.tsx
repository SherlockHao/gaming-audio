"use client";

import { Button, Card, Input, Tag, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { ProjectSelector } from "@/components/ProjectSelector";
import { useMapping, useUpdateMapping } from "@/lib/hooks";

export default function MappingsPage() {
  const [selectedProject, setSelectedProject] = useState("");
  const [editJson, setEditJson] = useState("{}");
  const { data: mapping } = useMapping(selectedProject);
  const updateMutation = useUpdateMapping(selectedProject);

  useEffect(() => {
    if (mapping) {
      setEditJson(JSON.stringify(mapping.mapping_body, null, 2));
    } else {
      setEditJson("{}");
    }
  }, [mapping]);

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(editJson);
      await updateMutation.mutateAsync(parsed);
      message.success("Mapping Dictionary saved");
    } catch {
      message.error("Invalid JSON or save failed");
    }
  };

  return (
    <div>
      <Typography.Title level={3}>Mapping Dictionary</Typography.Title>
      <Card size="small" style={{ marginBottom: 16 }}>
        <ProjectSelector value={selectedProject} onChange={setSelectedProject} />
        {mapping && <Tag color="blue" style={{ marginLeft: 12 }}>v{mapping.version}</Tag>}
      </Card>
      <Input.TextArea rows={20} value={editJson} onChange={(e) => setEditJson(e.target.value)} style={{ fontFamily: "monospace", fontSize: 13 }} />
      <Button type="primary" onClick={handleSave} loading={updateMutation.isPending} style={{ marginTop: 12 }}>Save</Button>
    </div>
  );
}

"use client";

import { Button, Card, Input, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { ProjectSelector } from "@/components/ProjectSelector";
import { useStyleBible, useUpdateStyleBible } from "@/lib/hooks";

export default function StyleBiblePage() {
  const [selectedProject, setSelectedProject] = useState("");
  const [editJson, setEditJson] = useState("");
  const { data: styleBible } = useStyleBible(selectedProject);
  const updateMutation = useUpdateStyleBible(selectedProject);

  useEffect(() => {
    if (styleBible) {
      setEditJson(JSON.stringify(styleBible.style_bible, null, 2));
    }
  }, [styleBible]);

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(editJson);
      await updateMutation.mutateAsync(parsed);
      message.success("Style Bible saved");
    } catch {
      message.error("Invalid JSON or save failed");
    }
  };

  return (
    <div>
      <Typography.Title level={3}>Style Bible</Typography.Title>
      <Card size="small" style={{ marginBottom: 16 }}>
        <ProjectSelector value={selectedProject} onChange={setSelectedProject} />
      </Card>
      <Input.TextArea rows={20} value={editJson} onChange={(e) => setEditJson(e.target.value)} style={{ fontFamily: "monospace", fontSize: 13 }} />
      <Button type="primary" onClick={handleSave} loading={updateMutation.isPending} style={{ marginTop: 12 }}>Save</Button>
    </div>
  );
}

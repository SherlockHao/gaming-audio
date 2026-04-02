"use client";

import { Button, Card, Typography, Input, Tag, message } from "antd";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Project { project_id: string; name: string; }
interface MappingDict { mapping_id: string; project_id: string; mapping_body: Record<string, unknown>; version: number; is_active: boolean; }

export default function MappingsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [mapping, setMapping] = useState<MappingDict | null>(null);
  const [editJson, setEditJson] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { apiFetch<Project[]>("/projects").then(setProjects).catch(() => {}); }, []);
  useEffect(() => { if (projects.length > 0 && !selectedProject) setSelectedProject(projects[0].project_id); }, [projects, selectedProject]);
  useEffect(() => {
    if (selectedProject) {
      apiFetch<MappingDict | null>(`/projects/${selectedProject}/rules/mappings`)
        .then((data) => { setMapping(data); setEditJson(data ? JSON.stringify(data.mapping_body, null, 2) : "{}"); })
        .catch(() => setEditJson("{}"));
    }
  }, [selectedProject]);

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(editJson);
      setSaving(true);
      const result = await apiFetch<MappingDict>(`/projects/${selectedProject}/rules/mappings`, { method: "PUT", body: JSON.stringify({ mapping_body: parsed }) });
      setMapping(result);
      message.success("Mapping Dictionary saved");
    } catch { message.error("Invalid JSON or save failed"); }
    finally { setSaving(false); }
  };

  return (
    <div>
      <Typography.Title level={3}>Mapping Dictionary</Typography.Title>
      {projects.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <span>Project: </span>
          <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)} style={{ padding: "4px 8px" }}>
            {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
          </select>
          {mapping && <Tag color="blue" style={{ marginLeft: 12 }}>v{mapping.version}</Tag>}
        </Card>
      )}
      <Input.TextArea rows={20} value={editJson} onChange={(e) => setEditJson(e.target.value)} style={{ fontFamily: "monospace", fontSize: 13 }} />
      <Button type="primary" onClick={handleSave} loading={saving} style={{ marginTop: 12 }}>Save</Button>
    </div>
  );
}

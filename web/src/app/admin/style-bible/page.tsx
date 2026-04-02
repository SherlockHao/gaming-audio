"use client";

import { Button, Card, Typography, Input, message } from "antd";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Project { project_id: string; name: string; }
interface StyleBible { project_id: string; name: string; style_bible: Record<string, unknown> | null; }

export default function StyleBiblePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [styleBible, setStyleBible] = useState<Record<string, unknown> | null>(null);
  const [editJson, setEditJson] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { apiFetch<Project[]>("/projects").then(setProjects).catch(() => {}); }, []);
  useEffect(() => { if (projects.length > 0 && !selectedProject) setSelectedProject(projects[0].project_id); }, [projects, selectedProject]);

  useEffect(() => {
    if (selectedProject) {
      apiFetch<StyleBible>(`/projects/${selectedProject}/style-bible`)
        .then((data) => { setStyleBible(data.style_bible); setEditJson(JSON.stringify(data.style_bible, null, 2)); })
        .catch(() => {});
    }
  }, [selectedProject]);

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(editJson);
      setSaving(true);
      await apiFetch(`/projects/${selectedProject}/style-bible`, { method: "PUT", body: JSON.stringify({ style_bible: parsed }) });
      setStyleBible(parsed);
      message.success("Style Bible saved");
    } catch (e) {
      message.error("Invalid JSON or save failed");
    } finally { setSaving(false); }
  };

  return (
    <div>
      <Typography.Title level={3}>Style Bible</Typography.Title>
      {projects.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <span>Project: </span>
          <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)} style={{ padding: "4px 8px" }}>
            {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
          </select>
        </Card>
      )}
      <Input.TextArea rows={20} value={editJson} onChange={(e) => setEditJson(e.target.value)} style={{ fontFamily: "monospace", fontSize: 13 }} />
      <Button type="primary" onClick={handleSave} loading={saving} style={{ marginTop: 12 }}>Save</Button>
    </div>
  );
}

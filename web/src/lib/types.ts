export interface Task {
  task_id: string;
  project_id: string;
  title: string;
  requester: string;
  asset_type: "sfx" | "ui" | "ambience_loop";
  semantic_scene: string;
  play_mode: "one_shot" | "loop";
  tags: string[] | null;
  notes: string | null;
  priority: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
}

export interface CategoryRule {
  rule_id: string;
  project_id: string;
  category: string;
  rule_level: string;
  rule_body: Record<string, unknown>;
  version: number;
  is_active: boolean;
}

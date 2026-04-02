export const TASK_STATES = [
  "Draft", "Submitted", "SpecGenerated", "SpecReviewPending",
  "AudioGenerated", "AudioGenerationFailed",
  "QCReady", "QCFailed",
  "WwiseImported", "WwiseImportFailed",
  "BankBuilt", "BankBuildFailed",
  "UEBound", "UEBindFailed", "BindingReviewPending",
  "QARun", "ReviewPending",
  "Approved", "Rejected", "RolledBack",
] as const;

export type TaskStatus = typeof TASK_STATES[number];

export interface Project {
  project_id: string;
  name: string;
  created_at: string;
}

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
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
}

export interface TaskCreate {
  project_id: string;
  title: string;
  requester: string;
  asset_type: "sfx" | "ui" | "ambience_loop";
  semantic_scene: string;
  play_mode: "one_shot" | "loop";
  tags?: string[];
  notes?: string;
  priority?: number;
}

export interface TaskUpdate {
  title?: string;
  asset_type?: "sfx" | "ui" | "ambience_loop";
  semantic_scene?: string;
  play_mode?: "one_shot" | "loop";
  tags?: string[];
  notes?: string;
  priority?: number;
}

export interface AuditLog {
  log_id: number;
  task_id: string | null;
  project_id: string | null;
  actor: string;
  action: string;
  old_state: string | null;
  new_state: string | null;
  detail: Record<string, unknown> | null;
  error_context: Record<string, unknown> | null;
  created_at: string;
}

export interface WwiseTemplate {
  template_id: string;
  project_id: string;
  name: string;
  template_type: string;
  template_body: Record<string, unknown>;
  version: number;
  is_active: boolean;
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

export interface MappingDictionary {
  mapping_id: string;
  project_id: string;
  mapping_body: Record<string, unknown>;
  version: number;
  is_active: boolean;
}

export interface StyleBible {
  project_id: string;
  name: string;
  style_bible: Record<string, unknown> | null;
}

export interface AudioIntentSpec {
  intent_id: string;
  task_id: string;
  content_type: string;
  semantic_role: string | null;
  intensity: string | null;
  material_hint: string | null;
  timing_points: Record<string, unknown> | null;
  loop_required: boolean;
  variation_count: number;
  design_pattern: string | null;
  category_rule_id: string | null;
  wwise_template_id: string | null;
  ue_binding_strategy: string | null;
  confidence: number | null;
  unresolved_fields: string[] | null;
}

export interface InputAssetRef {
  input_asset_id: string;
  task_id: string;
  asset_kind: string;
  asset_path: string;
  checksum: string | null;
}

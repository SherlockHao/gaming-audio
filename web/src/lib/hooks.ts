import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./api";
import type {
  CategoryRule,
  CandidateAudio,
  MappingDictionary,
  Project,
  QcReport,
  StyleBible,
  Task,
  TaskCreate,
  TaskListResponse,
  WwiseManifest,
  WwiseTemplate,
  AuditLog,
  AudioIntentSpec,
} from "./types";

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => apiFetch<Project[]>("/projects"),
  });
}

export function useTasks(projectId: string, options?: { status?: string; offset?: number; limit?: number }) {
  return useQuery({
    queryKey: ["tasks", projectId, options?.status, options?.offset, options?.limit],
    queryFn: () => {
      const params = new URLSearchParams({ project_id: projectId });
      if (options?.status) params.set("status", options.status);
      if (options?.offset !== undefined) params.set("offset", String(options.offset));
      if (options?.limit !== undefined) params.set("limit", String(options.limit));
      return apiFetch<TaskListResponse>(`/tasks?${params}`);
    },
    enabled: !!projectId,
  });
}

export function useTask(taskId: string) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => apiFetch<Task>(`/tasks/${taskId}`),
    enabled: !!taskId,
  });
}

export function useCategoryRules(projectId: string, category?: string) {
  return useQuery({
    queryKey: ["rules", "categories", projectId, category],
    queryFn: () => {
      let url = `/projects/${projectId}/rules/categories`;
      if (category) url += `?category=${category}`;
      return apiFetch<CategoryRule[]>(url);
    },
    enabled: !!projectId,
  });
}

export function useStyleBible(projectId: string) {
  return useQuery({
    queryKey: ["style-bible", projectId],
    queryFn: () => apiFetch<StyleBible>(`/projects/${projectId}/style-bible`),
    enabled: !!projectId,
  });
}

export function useUpdateStyleBible(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (styleBible: Record<string, unknown>) =>
      apiFetch<StyleBible>(`/projects/${projectId}/style-bible`, {
        method: "PUT",
        body: JSON.stringify({ style_bible: styleBible }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["style-bible", projectId] }),
  });
}

export function useWwiseTemplates(projectId: string) {
  return useQuery({
    queryKey: ["rules", "wwise-templates", projectId],
    queryFn: () => apiFetch<WwiseTemplate[]>(`/projects/${projectId}/rules/wwise-templates`),
    enabled: !!projectId,
  });
}

export function useMapping(projectId: string) {
  return useQuery({
    queryKey: ["rules", "mappings", projectId],
    queryFn: () => apiFetch<MappingDictionary | null>(`/projects/${projectId}/rules/mappings`),
    enabled: !!projectId,
  });
}

export function useUpdateMapping(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (mappingBody: Record<string, unknown>) =>
      apiFetch<MappingDictionary>(`/projects/${projectId}/rules/mappings`, {
        method: "PUT",
        body: JSON.stringify({ mapping_body: mappingBody }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules", "mappings", projectId] }),
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) =>
      apiFetch<Task>("/tasks", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useSubmitTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) =>
      apiFetch<Task>(`/tasks/${taskId}/submit`, { method: "POST" }),
    onSuccess: (_, taskId) => qc.invalidateQueries({ queryKey: ["task", taskId] }),
  });
}

export function useGenerateIntent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) =>
      apiFetch<AudioIntentSpec>(`/tasks/${taskId}/intent`, { method: "POST" }),
    onSuccess: (_, taskId) => qc.invalidateQueries({ queryKey: ["task", taskId] }),
  });
}

export function useIntentSpec(taskId: string) {
  return useQuery({
    queryKey: ["intent", taskId],
    queryFn: () => apiFetch<AudioIntentSpec>(`/tasks/${taskId}/intent`),
    enabled: !!taskId,
    retry: false,
  });
}

export function useAuditLogs(taskId: string) {
  return useQuery({
    queryKey: ["audit-log", taskId],
    queryFn: () => apiFetch<AuditLog[]>(`/tasks/${taskId}/audit-log`),
    enabled: !!taskId,
  });
}

export function useCandidates(taskId: string) {
  return useQuery({
    queryKey: ["candidates", taskId],
    queryFn: () => apiFetch<CandidateAudio[]>(`/tasks/${taskId}/audio/candidates`),
    enabled: !!taskId,
  });
}

export function useGenerateAudio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) =>
      apiFetch<CandidateAudio[]>(`/tasks/${taskId}/audio/generate`, { method: "POST" }),
    onSuccess: (_, taskId) => {
      qc.invalidateQueries({ queryKey: ["candidates", taskId] });
      qc.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });
}

export function useSelectCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, candidateId }: { taskId: string; candidateId: string }) =>
      apiFetch<CandidateAudio>(`/tasks/${taskId}/audio/${candidateId}/select`, { method: "POST" }),
    onSuccess: (_, { taskId }) => qc.invalidateQueries({ queryKey: ["candidates", taskId] }),
  });
}

export function useWwiseManifest(taskId: string) {
  return useQuery({
    queryKey: ["wwise-manifest", taskId],
    queryFn: () => apiFetch<WwiseManifest | null>(`/tasks/${taskId}/wwise/manifest`),
    enabled: !!taskId,
    retry: false,
  });
}

export function useImportWwise() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) =>
      apiFetch<WwiseManifest>(`/tasks/${taskId}/wwise/import`, { method: "POST" }),
    onSuccess: (_, taskId) => {
      qc.invalidateQueries({ queryKey: ["wwise-manifest", taskId] });
      qc.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });
}

export function useBuildBank() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) =>
      apiFetch<WwiseManifest>(`/tasks/${taskId}/wwise/build-bank`, { method: "POST" }),
    onSuccess: (_, taskId) => {
      qc.invalidateQueries({ queryKey: ["wwise-manifest", taskId] });
      qc.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });
}

export function useRunQc() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) =>
      apiFetch<QcReport[]>(`/tasks/${taskId}/audio/qc`, { method: "POST" }),
    onSuccess: (_, taskId) => {
      qc.invalidateQueries({ queryKey: ["task", taskId] });
      qc.invalidateQueries({ queryKey: ["candidates", taskId] });
    },
  });
}

export function useQcReports(taskId: string) {
  return useQuery({
    queryKey: ["qc-reports", taskId],
    queryFn: () => apiFetch<QcReport[]>(`/tasks/${taskId}/audio/qc-reports`),
    enabled: !!taskId,
    retry: false,
  });
}

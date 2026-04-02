import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./api";
import type {
  CategoryRule,
  MappingDictionary,
  Project,
  StyleBible,
  Task,
  TaskListResponse,
  WwiseTemplate,
} from "./types";

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => apiFetch<Project[]>("/projects"),
  });
}

export function useTasks(projectId: string, status?: string) {
  return useQuery({
    queryKey: ["tasks", projectId, status],
    queryFn: () => {
      const params = new URLSearchParams({ project_id: projectId });
      if (status) params.set("status", status);
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

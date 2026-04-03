"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function useTaskSSE(taskId: string | null) {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const url = `${API_BASE}/tasks/${taskId}/events`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.addEventListener("status_change", (event) => {
      // Invalidate task and related queries
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
      queryClient.invalidateQueries({ queryKey: ["intent", taskId] });
      queryClient.invalidateQueries({ queryKey: ["audit-log", taskId] });
      queryClient.invalidateQueries({ queryKey: ["candidates", taskId] });
      queryClient.invalidateQueries({ queryKey: ["wwise-manifest", taskId] });
    });

    es.addEventListener("error", () => {
      // EventSource auto-reconnects, no action needed
    });

    es.addEventListener("timeout", () => {
      es.close();
    });

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [taskId, queryClient]);
}

import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Import after mocking
import { apiFetch } from "@/lib/api";

describe("apiFetch", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("should call fetch with correct URL", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: "test" }),
    });

    const result = await apiFetch("/tasks");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/tasks"),
      expect.any(Object)
    );
    expect(result).toEqual({ data: "test" });
  });

  it("should throw on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Not found" }),
    });

    await expect(apiFetch("/tasks/nonexistent")).rejects.toThrow("Not found");
  });
});

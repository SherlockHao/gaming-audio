import { describe, it, expect } from "vitest";
import { TASK_STATES } from "@/lib/types";

describe("types", () => {
  it("should have 20 task states", () => {
    expect(TASK_STATES).toHaveLength(20);
  });

  it("should include Draft and Approved states", () => {
    expect(TASK_STATES).toContain("Draft");
    expect(TASK_STATES).toContain("Approved");
  });

  it("should include all failure states", () => {
    const failureStates = TASK_STATES.filter((s) => s.includes("Failed"));
    expect(failureStates).toHaveLength(5);
  });
});

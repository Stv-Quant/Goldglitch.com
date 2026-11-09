import { describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
vi.mock("@/lib/env", () => ({ getDB: async () => { throw new Error("no db"); } }));
const { bogotaDay } = await import("@/lib/fixtures");

describe("bogotaDay", () => {
  it("uses the Colombian calendar day, not UTC", () => {
    // 2026-11-10 02:00Z is still 2026-11-09 21:00 in Bogotá
    const d = bogotaDay(Date.parse("2026-11-10T02:00:00Z"));
    expect(d.ymd).toBe("20261109");
    expect(new Date(d.start).toISOString()).toBe("2026-11-09T05:00:00.000Z");
    expect(d.end - d.start).toBe(86_400_000);
  });
});

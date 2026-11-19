import { describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
vi.mock("@/lib/env", () => ({ getDB: async () => ({}) }));
vi.mock("next/headers", () => ({ cookies: async () => ({}) }));
import { normalizeUsername } from "@/lib/auth";

describe("usernames", () => {
  it("accepts 3-20 letters, numbers, dot and underscore", () => {
    expect(normalizeUsername("  steven_10 ")).toBe("steven_10");
    expect(normalizeUsername("Gold.Glitch")).toBe("Gold.Glitch");
  });
  it("rejects bad shapes", () => {
    for (const u of ["ab", "a".repeat(21), "con espacio", "_lead", "trail.", "ñandú", "x@y", ""]) expect(normalizeUsername(u)).toBeNull();
  });
});

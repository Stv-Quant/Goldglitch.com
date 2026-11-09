import { execFileSync } from "node:child_process";
import { describe, expect, it } from "vitest";
import { hashPassword, passwordProblem, verifyPassword } from "@/lib/password";

describe("passwords", () => {
  it("hash/verify roundtrip and rejects wrong password", async () => {
    const h = await hashPassword("Correct-Horse-9-Battery");
    expect(h.startsWith("pbkdf2$100000$")).toBe(true);
    expect(await verifyPassword("Correct-Horse-9-Battery", h)).toBe(true);
    expect(await verifyPassword("correct-horse-9-battery", h)).toBe(false);
    expect(await verifyPassword("x", null)).toBe(false);
  });
  it("verifies a hash produced by Python (used to seed the admin)", async () => {
    const py = execFileSync("python3", ["-c", `
import hashlib,base64,os,sys
pw=sys.argv[1].encode(); salt=os.urandom(16)
h=hashlib.pbkdf2_hmac('sha256',pw,salt,100000,32)
print('pbkdf2$100000$'+base64.b64encode(salt).decode()+'$'+base64.b64encode(h).decode())`, "Temp-Pass-123!x"]).toString().trim();
    expect(await verifyPassword("Temp-Pass-123!x", py)).toBe(true);
    expect(await verifyPassword("Temp-Pass-123!y", py)).toBe(false);
  });
  it("enforces the policy", () => {
    expect(passwordProblem("short")).toMatch(/12/);
    expect(passwordProblem("alllowercaseletters")).toMatch(/3 de/);
    expect(passwordProblem("Steven-Strong-123", "steven@x.co")).toMatch(/correo/);
    expect(passwordProblem("Gold-Glitch-2026!")).toBeNull();
  });
});

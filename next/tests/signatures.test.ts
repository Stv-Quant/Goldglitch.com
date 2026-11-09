import { execFileSync } from "node:child_process";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { ingestBatchSchema, predictionSchema } from "@/lib/contracts";
import { hmacSha256Hex, safeEqual, sha256Hex } from "@/lib/crypto";
import { redactPrediction } from "@/lib/entitlements";
import { buildCheckoutUrl, integritySignature, verifyEventChecksum, type WompiEvent } from "@/lib/wompi";

const PY = path.resolve(__dirname, "../../integrations/sqpc/goldglitch_publish.py");

describe("Wompi", () => {
  it("integrity signature = sha256(reference+amount+currency+secret)", async () => {
    const sig = await integritySignature("gg_ref1", 3990000, "COP", "test_integrity_abc");
    expect(sig).toBe(await sha256Hex("gg_ref13990000COPtest_integrity_abc"));
  });

  it("checkout URL carries every required param", async () => {
    const url = new URL(
      await buildCheckoutUrl({
        publicKey: "pub_test_x", integritySecret: "s", reference: "gg_1", amountInCents: 100,
        currency: "COP", redirectUrl: "https://goldglitch.com/app/cuenta?pago=gg_1", email: "a@b.co",
      }),
    );
    expect(url.origin + url.pathname).toBe("https://checkout.wompi.co/p/");
    for (const k of ["public-key", "currency", "amount-in-cents", "reference", "signature:integrity", "redirect-url", "customer-data:email"]) {
      expect(url.searchParams.get(k)).toBeTruthy();
    }
  });

  const secret = "test_events_secret";
  const base = (): WompiEvent => ({
    event: "transaction.updated",
    data: { transaction: { id: "1234-1610641025-49201", status: "APPROVED", reference: "gg_1", amount_in_cents: 4490000, currency: "COP" } },
    signature: { properties: ["transaction.id", "transaction.status", "transaction.amount_in_cents"], checksum: "" },
    timestamp: 1530291411,
  });

  it("accepts the documented checksum construction", async () => {
    const evt = base();
    evt.signature!.checksum = (await sha256Hex(`1234-1610641025-49201APPROVED44900001530291411${secret}`)).toUpperCase();
    expect(await verifyEventChecksum(evt, secret)).toBe(true);
    expect(await verifyEventChecksum(evt, secret, evt.signature!.checksum)).toBe(true);
  });

  it("rejects tampered amount, wrong secret, missing properties", async () => {
    const evt = base();
    evt.signature!.checksum = await sha256Hex(`1234-1610641025-49201APPROVED44900001530291411${secret}`);
    const tampered = structuredClone(evt);
    tampered.data.transaction!.amount_in_cents = 100;
    expect(await verifyEventChecksum(tampered, secret)).toBe(false);
    expect(await verifyEventChecksum(evt, "other")).toBe(false);
    const noProps = structuredClone(evt);
    noProps.signature!.properties = [];
    expect(await verifyEventChecksum(noProps, secret)).toBe(false);
  });
});

describe("Ingest signature", () => {
  it("Python publisher and TS verifier agree byte-for-byte", async () => {
    const ts = 1762650000000;
    const raw = JSON.stringify({ batchId: "b1", source: "t", note: "ñandú — áé" });
    const py = execFileSync("python3", ["-c",
      `import importlib.util,sys;s=importlib.util.spec_from_file_location('p',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.sign('k',${ts},sys.argv[2]))`,
      PY, raw]).toString().trim();
    const ts_ = await hmacSha256Hex("k", `${ts}.${raw}`);
    expect(safeEqual(py, ts_)).toBe(true);
  });

  it("demo batch from the Python publisher validates against the contract", () => {
    const json = execFileSync("python3", ["-c",
      `import importlib.util,sys,json;s=importlib.util.spec_from_file_location('p',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(json.dumps(m.demo_batch()))`,
      PY]).toString();
    const r = ingestBatchSchema.safeParse(JSON.parse(json));
    expect(r.success, JSON.stringify(r.error?.issues?.slice(0, 3))).toBe(true);
  });
});

describe("Entitlements", () => {
  const json = execFileSync("python3", ["-c",
    `import importlib.util,sys,json;s=importlib.util.spec_from_file_location('p',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(json.dumps(m.demo_batch()['predictions'][0]))`,
    PY]).toString();
  const p = predictionSchema.parse(JSON.parse(json));

  it("free never receives pro/elite fields", () => {
    const r = redactPrediction(p, "free");
    const s = JSON.stringify(r);
    expect(r.scoreMatrix).toBeUndefined();
    expect(r.edges).toBeUndefined();
    expect(s).not.toContain("interval");
    expect(s).not.toContain("bookmaker");
    expect(r.locked).toEqual({ pro: true, elite: true });
  });
  it("pro gets model depth but not market edges", () => {
    const r = redactPrediction(p, "pro");
    expect(r.scoreMatrix).toBeDefined();
    expect(r.edges).toBeUndefined();
  });
  it("elite gets everything", () => {
    expect(redactPrediction(p, "elite").edges?.length).toBeGreaterThan(0);
  });
});

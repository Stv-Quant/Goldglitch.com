import { safeEqual, sha256Hex } from "./crypto";

export const WOMPI_CHECKOUT_URL = "https://checkout.wompi.co/p/";

/** Integrity signature for Web Checkout: SHA256(reference + amountInCents + currency + integritySecret). */
export async function integritySignature(
  reference: string,
  amountInCents: number,
  currency: string,
  integritySecret: string,
): Promise<string> {
  return sha256Hex(`${reference}${amountInCents}${currency}${integritySecret}`);
}

export async function buildCheckoutUrl(opts: {
  publicKey: string;
  integritySecret: string;
  reference: string;
  amountInCents: number;
  currency: string;
  redirectUrl: string;
  email: string;
}): Promise<string> {
  const sig = await integritySignature(opts.reference, opts.amountInCents, opts.currency, opts.integritySecret);
  const q = new URLSearchParams({
    "public-key": opts.publicKey,
    currency: opts.currency,
    "amount-in-cents": String(opts.amountInCents),
    reference: opts.reference,
    "signature:integrity": sig,
    "redirect-url": opts.redirectUrl,
    "customer-data:email": opts.email,
  });
  return `${WOMPI_CHECKOUT_URL}?${q.toString()}`;
}

export type WompiEvent = {
  event: string;
  data: { transaction?: WompiTransaction } & Record<string, unknown>;
  signature?: { properties: string[]; checksum: string };
  timestamp: number;
  sent_at?: string;
};

export type WompiTransaction = {
  id: string;
  status: "PENDING" | "APPROVED" | "DECLINED" | "VOIDED" | "ERROR";
  reference: string;
  amount_in_cents: number;
  currency: string;
  customer_email?: string;
};

function readPath(obj: unknown, path: string): unknown {
  return path.split(".").reduce<unknown>(
    (acc, key) => (acc && typeof acc === "object" ? (acc as Record<string, unknown>)[key] : undefined),
    obj,
  );
}

/**
 * Event authenticity: concatenate the values of signature.properties (paths inside `data`),
 * then the event timestamp, then the events secret; SHA256 must match the checksum.
 * Properties are read from each event, never hardcoded, because Wompi may change them.
 */
export async function verifyEventChecksum(
  evt: WompiEvent,
  eventsSecret: string,
  headerChecksum?: string | null,
): Promise<boolean> {
  const props = evt.signature?.properties;
  const checksum = headerChecksum || evt.signature?.checksum;
  if (!Array.isArray(props) || props.length === 0 || !checksum || !Number.isFinite(evt.timestamp)) return false;

  let concat = "";
  for (const p of props) {
    const v = readPath(evt.data, p);
    if (v === undefined || v === null) return false;
    concat += String(v);
  }
  const computed = await sha256Hex(`${concat}${evt.timestamp}${eventsSecret}`);
  return safeEqual(computed, checksum);
}

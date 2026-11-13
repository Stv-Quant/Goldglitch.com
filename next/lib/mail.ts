import "server-only";
import { getCloudflareContext } from "@opennextjs/cloudflare";
import { getDB, getEnv } from "./env";
import { PLANS, formatCOP, type BillingPeriod, type PaidPlan } from "./plans";

export type MailKind =
  | "magic_link" | "welcome" | "password_reset" | "password_changed"
  | "renewal_7d" | "renewal_1d" | "expired" | "payment_approved" | "test";

const DEFAULT_URL = "https://easygoldglitch.com";
const DEFAULT_FROM = "Goldglitch <hola@easygoldglitch.com>";

export async function appUrl(): Promise<string> {
  const env = await getEnv();
  return (env.APP_URL ?? DEFAULT_URL).replace(/\/$/, "");
}

const esc = (s: string) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

/** One branded layout for every email: dark, gold accent, single call to action, plain-text twin. */
function layout(o: { preheader: string; title: string; paragraphs: string[]; cta?: { label: string; url: string }; note?: string; base: string }) {
  const p = o.paragraphs.map((t) => `<p style="color:#B5B2AA;line-height:1.6;margin:0 0 16px;font-size:15px">${t}</p>`).join("");
  const cta = o.cta
    ? `<a href="${esc(o.cta.url)}" style="display:inline-block;background:#D4AF37;color:#020202;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px;margin:8px 0 4px">${esc(o.cta.label)}</a>`
    : "";
  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta name="color-scheme" content="dark"></head>
<body style="margin:0;background:#020202">
<span style="display:none;max-height:0;overflow:hidden;opacity:0">${esc(o.preheader)}</span>
<div style="background:#020202;padding:40px 20px;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#F5F3EE">
  <div style="max-width:480px;margin:0 auto">
    <p style="letter-spacing:.22em;font-size:11px;color:#D4AF37;margin:0 0 28px">GOLDGLITCH · STATS</p>
    <h1 style="font-size:24px;line-height:1.25;font-weight:600;margin:0 0 16px;color:#F5F3EE">${o.title}</h1>
    ${p}${cta}
    ${o.note ? `<p style="color:#8A8780;font-size:12px;line-height:1.5;margin:28px 0 0">${o.note}</p>` : ""}
    <hr style="border:none;border-top:1px solid #1f1d19;margin:32px 0 16px">
    <p style="color:#6b6862;font-size:11px;line-height:1.5;margin:0">Goldglitch publica estadísticas y probabilidades, no garantiza resultados. Juega con responsabilidad; solo mayores de 18.<br>
    <a href="${o.base}" style="color:#8A8780">easygoldglitch.com</a> · <a href="${o.base}/legal/privacidad" style="color:#8A8780">Privacidad</a></p>
  </div>
</div></body></html>`;
  const strip = (s: string) => s.replace(/<[^>]+>/g, "").replace(/&nbsp;/g, " ");
  const text = [o.title, "", ...o.paragraphs.map(strip), o.cta ? `${o.cta.label}: ${o.cta.url}` : "", o.note ? strip(o.note) : "", "", "Goldglitch · easygoldglitch.com"]
    .filter((l, i, a) => l !== "" || a[i - 1] !== "")
    .join("\n");
  return { html, text };
}

type Send = { to: string; subject: string; html: string; text: string; kind: MailKind; userId?: string | null; dedupeKey?: string };

/**
 * Sends through Resend and records the attempt in email_log. With a dedupe key the email goes out at most once
 * (reminders, welcome). Without RESEND_API_KEY (local dev) the email is logged as skipped and printed.
 */
export async function sendEmail(m: Send): Promise<boolean> {
  const env = await getEnv();
  const db = await getDB();
  const now = Date.now();

  if (m.dedupeKey) {
    // Claim the key first so two concurrent runs cannot both send.
    const claimed = await db
      .prepare("INSERT INTO email_log (user_id, email, kind, dedupe_key, status, created_at) VALUES (?, ?, ?, ?, 'skipped', ?) ON CONFLICT(dedupe_key) DO NOTHING RETURNING id")
      .bind(m.userId ?? null, m.to, m.kind, m.dedupeKey, now)
      .first<{ id: number }>()
      .catch(() => null);
    if (!claimed) return true; // already sent (or in flight)
    return deliver(m, env, async (status, providerId, error) => {
      await db.prepare("UPDATE email_log SET status = ?, provider_id = ?, error = ? WHERE id = ?").bind(status, providerId, error, claimed.id).run();
      // A failed (or not-yet-configured) reminder must be retryable on the next run.
      if (status !== "sent") await db.prepare("UPDATE email_log SET dedupe_key = NULL WHERE id = ?").bind(claimed.id).run();
    });
  }
  return deliver(m, env, async (status, providerId, error) => {
    await db
      .prepare("INSERT INTO email_log (user_id, email, kind, status, provider_id, error, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)")
      .bind(m.userId ?? null, m.to, m.kind, status, providerId, error, now)
      .run()
      .catch(() => undefined);
  });
}

async function deliver(
  m: Send,
  env: Awaited<ReturnType<typeof getEnv>>,
  record: (status: "sent" | "failed" | "skipped", providerId: string | null, error: string | null) => Promise<void>,
): Promise<boolean> {
  if (!env.RESEND_API_KEY) {
    console.log(`[mail:dev] ${m.kind} → ${m.to}: ${m.subject}\n${m.text}`);
    await record("skipped", null, "RESEND_API_KEY no configurada");
    return true;
  }
  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        authorization: `Bearer ${env.RESEND_API_KEY}`,
        "content-type": "application/json",
        ...(m.dedupeKey ? { "idempotency-key": m.dedupeKey.slice(0, 256) } : {}),
      },
      body: JSON.stringify({
        from: env.MAIL_FROM ?? DEFAULT_FROM,
        to: [m.to],
        subject: m.subject,
        html: m.html,
        text: m.text,
        tags: [{ name: "kind", value: m.kind }],
      }),
    });
    const body = (await r.json().catch(() => ({}))) as { id?: string; message?: string; name?: string };
    if (!r.ok) {
      await record("failed", null, `${r.status} ${body.name ?? ""} ${body.message ?? ""}`.trim().slice(0, 300));
      return false;
    }
    await record("sent", body.id ?? null, null);
    return true;
  } catch (e) {
    await record("failed", null, String(e).slice(0, 300));
    return false;
  }
}

/** Run an email after the response is sent (never slows a login or a webhook). */
export async function later(p: Promise<unknown>): Promise<void> {
  try {
    const { ctx } = await getCloudflareContext({ async: true });
    ctx.waitUntil(p.catch((e) => console.error("mail", e)));
  } catch {
    await p.catch((e) => console.error("mail", e));
  }
}

// ---------------------------------------------------------------- templates

const dateFmt = new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "long", year: "numeric", timeZone: "America/Bogota" });

export async function sendMagicLink(email: string, link: string): Promise<boolean> {
  const base = await appUrl();
  const { html, text } = layout({
    base,
    preheader: "Tu enlace para entrar. Vence en 15 minutos.",
    title: "Tu acceso",
    paragraphs: ["Usa este botón para entrar a Goldglitch. El enlace vence en 15 minutos y funciona una sola vez."],
    cta: { label: "Entrar a Goldglitch", url: link },
    note: "Si no pediste este acceso, ignora este correo: nadie puede entrar sin él.",
  });
  return sendEmail({ to: email, subject: "Tu enlace de acceso a Goldglitch", html, text, kind: "magic_link" });
}

export async function sendWelcome(user: { id: string; email: string }): Promise<boolean> {
  const base = await appUrl();
  const { html, text } = layout({
    base,
    preheader: "Probabilidades con su rango de error y un historial que no se borra.",
    title: "Bienvenido a Goldglitch",
    paragraphs: [
      "Ya tienes tu cuenta. Aquí no vendemos picks ni certezas: publicamos la probabilidad de cada resultado, con su rango de incertidumbre, y llevamos un historial abierto de aciertos y fallos.",
      "Con el plan gratis ves las probabilidades 1X2 de fútbol. Pro abre todas las estadísticas: picks del modelo, líneas de goles, córners, tarjetas y jugadores, marcadores probables, todos los deportes y el modelo contra las cuotas de las casas.",
      "Un consejo para empezar: mira el rango, no solo el número. Un 55% con rango 45–65% no es lo mismo que un 55% con rango 52–58%.",
    ],
    cta: { label: "Ver los partidos de hoy", url: `${base}/app` },
    note: "Recibes este correo porque creaste una cuenta en easygoldglitch.com.",
  });
  return sendEmail({ to: user.email, subject: "Bienvenido a Goldglitch", html, text, kind: "welcome", userId: user.id, dedupeKey: `welcome:${user.id}` });
}

export async function sendPasswordReset(user: { id: string; email: string }, link: string): Promise<boolean> {
  const base = await appUrl();
  const { html, text } = layout({
    base,
    preheader: "Crea una contraseña nueva. El enlace vence en 30 minutos.",
    title: "Restablece tu contraseña",
    paragraphs: ["Recibimos una solicitud para cambiar la contraseña de tu cuenta. El enlace vence en 30 minutos y solo funciona una vez."],
    cta: { label: "Crear contraseña nueva", url: link },
    note: "Si no lo pediste tú, ignora este correo: tu contraseña actual sigue funcionando.",
  });
  return sendEmail({ to: user.email, subject: "Restablece tu contraseña de Goldglitch", html, text, kind: "password_reset", userId: user.id });
}

export async function sendPasswordChanged(user: { id: string; email: string }): Promise<boolean> {
  const base = await appUrl();
  const when = new Intl.DateTimeFormat("es-CO", { dateStyle: "long", timeStyle: "short", timeZone: "America/Bogota" }).format(Date.now());
  const { html, text } = layout({
    base,
    preheader: "Aviso de seguridad de tu cuenta.",
    title: "Tu contraseña cambió",
    paragraphs: [`La contraseña de tu cuenta se cambió el ${when} (hora Colombia) y se cerraron las demás sesiones.`],
    cta: { label: "No fui yo: recuperar acceso", url: `${base}/acceso/recuperar` },
    note: "Si fuiste tú, no tienes que hacer nada.",
  });
  return sendEmail({ to: user.email, subject: "Tu contraseña de Goldglitch cambió", html, text, kind: "password_changed", userId: user.id });
}

export async function sendRenewalReminder(
  user: { id: string; email: string },
  sub: { plan: PaidPlan; periodEnd: number },
  stage: "renewal_7d" | "renewal_1d" | "expired",
): Promise<boolean> {
  const base = await appUrl();
  const plan = PLANS[sub.plan].name;
  const end = dateFmt.format(sub.periodEnd);
  const copy = {
    renewal_7d: {
      subject: `Tu plan ${plan} vence el ${end}`,
      title: `Tu plan ${plan} vence en 7 días`,
      body: `Tu membresía ${plan} está activa hasta el ${end}. No hacemos cobros automáticos: si quieres seguir, renueva antes de esa fecha y el tiempo se suma al que te queda.`,
    },
    renewal_1d: {
      subject: `Mañana vence tu plan ${plan}`,
      title: `Tu plan ${plan} vence mañana`,
      body: `Tu membresía ${plan} termina el ${end}. Después pasarás al plan gratis y dejarás de ver ${sub.plan === "elite" ? "el modelo contra el mercado y los otros deportes" : "goles esperados, marcadores y mercados"}.`,
    },
    expired: {
      subject: `Tu plan ${plan} terminó`,
      title: `Tu plan ${plan} terminó`,
      body: `Tu membresía venció el ${end} y tu cuenta pasó al plan gratis. Tus datos y tu historial siguen ahí: renueva cuando quieras y retomas donde ibas.`,
    },
  }[stage];
  const { html, text } = layout({
    base,
    preheader: copy.title,
    title: copy.title,
    paragraphs: [copy.body, `Precio actual: ${formatCOP(PLANS[sub.plan].price.monthly)} al mes o ${formatCOP(PLANS[sub.plan].price.annual)} al año.`],
    cta: { label: stage === "expired" ? "Reactivar mi plan" : "Renovar ahora", url: `${base}/planes` },
    note: "Recibes este aviso porque tienes o tuviste una membresía paga en Goldglitch.",
  });
  return sendEmail({
    to: user.email, subject: copy.subject, html, text, kind: stage, userId: user.id,
    dedupeKey: `${stage}:${user.id}:${sub.periodEnd}`,
  });
}

export async function sendPaymentApproved(
  user: { id: string; email: string },
  p: { reference: string; plan: PaidPlan; period: BillingPeriod; amountInCents: number; periodEnd: number },
): Promise<boolean> {
  const base = await appUrl();
  const plan = PLANS[p.plan].name;
  const { html, text } = layout({
    base,
    preheader: `Pago aprobado: ${plan} activo hasta el ${dateFmt.format(p.periodEnd)}.`,
    title: "Pago aprobado",
    paragraphs: [
      `Recibimos tu pago de ${formatCOP(p.amountInCents)} por el plan ${plan} ${p.period === "annual" ? "anual" : "mensual"}.`,
      `Tu membresía está activa hasta el <b style="color:#F5F3EE">${dateFmt.format(p.periodEnd)}</b>. Te avisaremos antes de que venza; no hay cobros automáticos.`,
      `Referencia: ${esc(p.reference)}`,
    ],
    cta: { label: "Abrir Goldglitch", url: `${base}/app` },
  });
  return sendEmail({
    to: user.email, subject: `Pago aprobado · ${plan}`, html, text, kind: "payment_approved", userId: user.id,
    dedupeKey: `payment:${p.reference}`,
  });
}

export async function sendTestEmail(to: string, userId: string): Promise<boolean> {
  const base = await appUrl();
  const { html, text } = layout({
    base,
    preheader: "Correo de prueba desde el panel de administración.",
    title: "Correo de prueba",
    paragraphs: ["Si lees esto, Resend y el dominio están bien configurados y los correos automáticos de Goldglitch están saliendo."],
    cta: { label: "Ir al panel", url: `${base}/admin/correos` },
  });
  return sendEmail({ to, subject: "Prueba de correo · Goldglitch", html, text, kind: "test", userId });
}

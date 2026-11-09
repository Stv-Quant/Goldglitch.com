import "server-only";
import { getEnv } from "./env";

/**
 * Sends the magic link via Resend's HTTP API. Without RESEND_API_KEY (local dev)
 * the link is logged to the server console instead.
 */
export async function sendMagicLink(email: string, link: string): Promise<boolean> {
  const env = await getEnv();
  if (!env.RESEND_API_KEY) {
    console.log(`[dev] magic link for ${email}: ${link}`);
    return true;
  }

  const html = `
  <div style="background:#020202;padding:40px 24px;font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#F5F3EE">
    <div style="max-width:440px;margin:0 auto">
      <p style="letter-spacing:.2em;font-size:12px;color:#D4AF37;margin:0 0 24px">GOLDGLITCH · STATS</p>
      <h1 style="font-size:22px;font-weight:600;margin:0 0 12px">Tu acceso</h1>
      <p style="color:#B5B2AA;line-height:1.5;margin:0 0 28px">Este enlace es válido por 15 minutos y solo funciona una vez.</p>
      <a href="${link}" style="display:inline-block;background:#D4AF37;color:#020202;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px">Entrar a Goldglitch</a>
      <p style="color:#8A8780;font-size:12px;margin-top:32px">Si no solicitaste este acceso, ignora este correo.</p>
    </div>
  </div>`;

  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${env.RESEND_API_KEY}`, "content-type": "application/json" },
    body: JSON.stringify({
      from: env.MAIL_FROM ?? "Goldglitch <acceso@goldglitch.com>",
      to: [email],
      subject: "Tu enlace de acceso a Goldglitch",
      html,
      text: `Entra a Goldglitch: ${link}\nVálido 15 minutos, un solo uso.`,
    }),
  });
  return r.ok;
}

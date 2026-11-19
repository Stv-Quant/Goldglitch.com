/**
 * PBKDF2-SHA256 password hashing via WebCrypto (Workers caps PBKDF2 at 100k iterations).
 * Format: pbkdf2$<iterations>$<salt b64>$<hash b64>
 */
const ITERATIONS = 100_000;
const enc = new TextEncoder();

function b64(buf: ArrayBuffer | Uint8Array): string {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
}

function unb64(s: string): Uint8Array<ArrayBuffer> {
  const bin = atob(s);
  const out = new Uint8Array(new ArrayBuffer(bin.length));
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function derive(password: string, salt: Uint8Array<ArrayBuffer>, iterations: number): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations }, key, 256);
  return new Uint8Array(bits);
}

export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await derive(password, salt, ITERATIONS);
  return `pbkdf2$${ITERATIONS}$${b64(salt)}$${b64(hash)}`;
}

export async function verifyPassword(password: string, stored: string | null | undefined): Promise<boolean> {
  if (!stored) return false;
  const [scheme, iter, saltB64, hashB64] = stored.split("$");
  if (scheme !== "pbkdf2" || !iter || !saltB64 || !hashB64) return false;
  const expected = unb64(hashB64);
  const actual = await derive(password, unb64(saltB64), Number(iter));
  if (actual.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < actual.length; i++) diff |= actual[i] ^ expected[i];
  return diff === 0;
}

/** Returns an error message (Spanish) or null when the password is acceptable. Same rule at signup and on change. */
export function passwordProblem(pw: string, email?: string, username?: string): string | null {
  if (pw.length < 8) return "Usa al menos 8 caracteres.";
  if (pw.length > 200) return "Máximo 200 caracteres.";
  if (!/[A-Za-zÀ-ÿ]/.test(pw) || !/[0-9]/.test(pw)) return "Combina letras y números.";
  const low = pw.toLowerCase();
  if (email && email.split("@")[0].length >= 3 && low.includes(email.split("@")[0].toLowerCase())) return "No uses tu correo dentro de la contraseña.";
  if (username && username.length >= 3 && low.includes(username.toLowerCase())) return "No uses tu usuario dentro de la contraseña.";
  return null;
}

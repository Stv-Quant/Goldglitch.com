#!/usr/bin/env bash
# Production deploy for goldglitch.com (Cloudflare Workers + D1).
# Order matters: the database schema must exist before the new Worker serves traffic.
set -euo pipefail
cd "$(dirname "$0")/.."

npx wrangler whoami >/dev/null 2>&1 || npx wrangler login

required=(INGEST_HMAC_SECRET WOMPI_PUBLIC_KEY WOMPI_INTEGRITY_SECRET WOMPI_EVENTS_SECRET RESEND_API_KEY)
existing="$(npx wrangler secret list 2>/dev/null || echo '[]')"
for s in "${required[@]}"; do
  if ! grep -q "\"$s\"" <<<"$existing"; then
    echo "→ Falta el secreto $s"
    npx wrangler secret put "$s"
  fi
done

npm ci
npm test
npx wrangler d1 migrations apply EGG_DB --remote
npm run deploy
curl -fsS https://goldglitch.com/api/health && echo " ✓ goldglitch.com en línea"

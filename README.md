# Goldglitch · Stats

PWA de estadísticas deportivas con membresías. Publica probabilidades con incertidumbre visible y un historial auditable. No vende señales.

## Arquitectura

```
SQPC (Python, local + WARP)
  └─ integrations/sqpc/goldglitch_publish.py ── HMAC ──▶ POST /api/ingest
                                                         │
Cloudflare Worker (Next 16 + OpenNext) ◀── D1 (EGG_DB) ◀─┘
  ├─ /            landing         ├─ /app                 partidos (requiere sesión)
  ├─ /planes      planes          ├─ /app/partido/[id]    ficha (gating por plan, server-side)
  ├─ /historial   track record    ├─ /app/cuenta          plan + pago Wompi
  └─ /acceso      magic link      └─ /api/billing/webhook eventos Wompi (checksum)
```

- **Gating:** `lib/entitlements.ts` recorta el payload en el servidor. Los datos bloqueados nunca llegan al cliente.
- **Planes:** Free (stats descriptivas y 1X2), Pro (intervalos, xG, matriz de marcadores, mercados, jugadores) y Elite (EV contra cuotas y MLB). Los precios están en `lib/plans.ts` y son provisionales.
- **Pagos:** Wompi Web Checkout con firma de integridad. Funcionan como periodos prepagados, sin cobro recurrente. El webhook verifica el checksum, el monto y la moneda, y es idempotente.
- **Contrato de datos:** `lib/contracts.ts` (zod). Es la única fuente de verdad entre SQPC y la PWA.

## Desarrollo local

```bash
cd next
npm ci
cp .dev.vars.example .dev.vars
npm run db:migrate:local
npm run dev                                   # los magic links se imprimen en consola
python3 ../integrations/sqpc/goldglitch_publish.py --url http://localhost:3000/api/ingest --secret dev-ingest-secret --demo
npm test
```

## Producción

```bash
cd next
npx wrangler secret put INGEST_HMAC_SECRET
npx wrangler secret put WOMPI_PUBLIC_KEY
npx wrangler secret put WOMPI_INTEGRITY_SECRET
npx wrangler secret put WOMPI_EVENTS_SECRET
npx wrangler secret put RESEND_API_KEY
npm run db:migrate:remote
npm run deploy
```

En el dashboard de Wompi, configura la URL de eventos como `https://goldglitch.com/api/billing/webhook`.

## Publicar desde SQPC

```python
from goldglitch_publish import publish
publish(batch, url="https://goldglitch.com/api/ingest", secret=os.environ["GG_INGEST_SECRET"])
```

`batchId` es la clave de idempotencia: reenviar el mismo batch no duplica nada.

## Legado

La tienda EGG (pago en ETH) se retiró en la rama `feat/stats-pwa-foundation`. Sigue disponible en el historial de git. La tabla `orders` se mantiene en D1 sin cambios.

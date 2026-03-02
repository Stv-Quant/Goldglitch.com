# EasyGoldGlitch — Arquitectura, Backlog y Plan de Entrega

## 0) Supuestos y variables de negocio iniciales

- `{{PRICE_USD}}`: **USD 1,490** (editable desde CMS / Admin).
- `{{REF_PRICE}}`: **ETHUSD spot** (fuente: provider market-data) y opcional secundario XAUUSD para storytelling educativo.
- `{{AMOUNT_ETH}}`: calculado server-side con margen de protección de volatilidad y expiración de cotización.
- `{{WALLET_ADDRESS}}`: generado por orden mediante derivación HD desde `xpub`.
- `{{NETWORK}}`: **Ethereum Mainnet** en MVP (evaluar L2 en Sprint 2.5 para fees).
- `{{DELIVERY_ASSET}}`: enlace único firmado + licencia PDF + guía de setup.
- `{{SUPPORT_EMAIL}}`: `support@easygoldglitch.com`.

---

## 1) Arquitectura final propuesta + diagrama simple

### Stack recomendado (cumple requisitos)
- **Frontend/App**: Next.js 15 (App Router) + TypeScript + TailwindCSS + design tokens CSS variables.
- **Motion/Scrollytelling**: Framer Motion + GSAP ScrollTrigger + Lenis (con fallback native scroll).
- **Tracking onView**: IntersectionObserver + scheduler con cooldown (anti-spam).
- **Backend ligero**: Route Handlers de Next.js + queue liviana (Upstash/QStash o cron jobs).
- **DB**: Postgres + Prisma.
- **Content layer/CMS**: Sanity (ideal), fallback: MDX + tabla `content_blocks` editable en mini-admin.
- **Email**: Resend (entrega asset tras verificación on-chain).
- **Blockchain verification**: ethers.js + provider (Alchemy/Infura) + confirmaciones configurables.
- **Infra/hosting**: Vercel + Postgres gestionado (Neon/Supabase/RDS).
- **Observabilidad**: Sentry + logs estructurados + auditoría de órdenes.

### Diagrama (alto nivel)
```text
Usuario
  │
  ▼
Next.js App Router (Home, Checkout, Terms, Risk, FAQ)
  ├─ Scrollytelling Engine (GSAP/Framer/Lenis)
  ├─ Analytics SDK (GA4 o PostHog)
  ├─ API /order-intent, /quote, /payment/mark-sent
  │
  ▼
Postgres + Prisma  ◄───────────── CMS (Sanity/Content Blocks)
  │
  ├─ Order Service (quote lock + amount + wallet derivation)
  ├─ Chain Watcher (tx detect + confirmations)
  └─ Delivery Service (Resend + signed link)
        │
        ▼
      Cliente (email de entrega + estado de orden)
```

---

## 2) Mapa de rutas (IA) + wireflow funnel

## IA de rutas
- `/` Home scrollytelling (capítulos + CTA sticky + stepper funnel).
- `/checkout` Checkout glass (orden, quote real, wallet, email, confirmación).
- `/terms` Términos.
- `/risk-disclosure` Riesgos y no asesoría financiera.
- `/faq` FAQ SEO + objeciones + enlaces internos.
- `/api/*` Endpoints de cotización, órdenes, tracking server y verificación.

## Wireflow funnel (visible para usuario)
1. **Step 1/3**: Descubrir (`/`) → “Ver cómo funciona”.
2. **Step 2/3**: Entender valor (`/` capítulos What you get + Price).
3. **Step 3/3**: Comprar (`/checkout`) → crear orden → pagar → “I sent the payment” → verificación → entrega email.

CTA obligatorios:
- `Unlock EasyGoldGlitch`
- `Go to Checkout`

---

## 3) Estructura de repo recomendada

```text
next/
  app/
    (marketing)/
      page.tsx
      sections/
    checkout/page.tsx
    terms/page.tsx
    risk-disclosure/page.tsx
    faq/page.tsx
    api/
      quote/route.ts
      order-intent/route.ts
      payment/mark-sent/route.ts
      payment/status/[orderId]/route.ts
      webhook/provider/route.ts
  components/
    glass/
    motion/
    checkout/
    seo/
  lib/
    analytics/
    blockchain/
    pricing/
    security/
    validations/
  prisma/
    schema.prisma
  docs/
    product-plan-easygoldglitch.md
```

---

## 4) Definición de componentes UI (design system)

### Tokens
- Colores: `bg.deep`, `glass.white/12`, `gold.400`, `gold.500`, `text.high`, `text.mid`.
- Radius: `r-lg=16`, `r-xl=22`, `r-2xl=28`.
- Blur: `glass-sm`, `glass-md`, `glass-lg`.
- Shadows: `soft-1`, `soft-2`, `glow-gold`.
- Motion timing: `fast 160ms`, `base 240ms`, `slow 420ms`.

### Componentes base
- `GlassCard`, `GlassPanel`, `GlowButton`, `StickyCTA`, `ProgressStepper`, `SectionReveal`.
- `VideoBlock` (autoplay muted inline, pause out-of-view, captions).
- `QuotePill` (countdown real + estado refresh).
- `CheckoutAmountCard`, `WalletFieldCopy`, `RiskDisclosureInline`, `TermsCheckbox`.
- `FunnelStepper` (Step 1/2/3 persistente y no invasivo).

### Accesibilidad
- Respeto `prefers-reduced-motion`.
- Contraste AA mínimo en textos críticos.
- Focus visible en CTA/inputs.
- Subtítulos opcionales en videos.

---

## 5) Contratos API + modelo de datos

## Endpoints (MVP)

### `POST /api/quote`
- **Input**: `{ currency: "USD", network: "ETH" }`
- **Output**:
```json
{
  "refPrice": 3821.42,
  "asset": "ETHUSD",
  "expiresAt": "2026-01-01T12:00:00.000Z",
  "ttlSec": 600,
  "source": "provider-name"
}
```

### `POST /api/order-intent`
- **Input**: `{ email, priceUsd, network, consentTerms, consentRisk }`
- **Output**:
```json
{
  "orderId": "ord_xxx",
  "walletAddress": "0x...",
  "amountEth": "0.389123",
  "quote": {
    "refPrice": 3821.42,
    "expiresAt": "2026-01-01T12:00:00.000Z"
  },
  "status": "awaiting_payment"
}
```

### `POST /api/payment/mark-sent`
- **Input**: `{ orderId, txHash? }`
- **Output**: `{ status: "pending_verification" }`

### `GET /api/payment/status/:orderId`
- **Output**:
```json
{
  "orderId": "ord_xxx",
  "status": "awaiting_payment|pending_verification|confirmed|expired|failed",
  "confirmations": 2,
  "requiredConfirmations": 3
}
```

### `POST /api/webhook/provider` (opcional)
- Callback de indexador/monitor chain para acelerar confirmación.

### Reglas de seguridad API
- Rate limit por IP + fingerprint básico.
- Validación con Zod en payloads.
- Logs auditables con `requestId`.
- Sanitización de email/input.

## Modelo de datos (Prisma conceptual)
- `UserContact(id, email, createdAt)`
- `Order(id, userContactId, priceUsd, refPrice, amountEth, network, walletAddress, quoteExpiresAt, status, createdAt, updatedAt)`
- `Payment(id, orderId, txHash, amountReceived, confirmations, chainTimestamp, status)`
- `Delivery(id, orderId, assetUrlSigned, sentAt, providerMessageId, status)`
- `ContentBlock(id, key, locale, payloadJson, published, order)`
- `AnalyticsEvent(id, sessionId, eventName, payloadJson, createdAt)` (si server-side mirror)
- `AuditLog(id, actor, action, entityType, entityId, metaJson, createdAt)`

---

## 6) Especificación de analítica (event taxonomy)

Proveedor recomendado: **PostHog** (autocapture selectivo + funnels + session replay con masking), alterno GA4.

### Eventos requeridos
- `page_view`
- `scroll_depth` `{depth:25|50|75|90}`
- `section_view` `{section_id, dwell_time_ms}`
- `video_view` `{video_id, seconds_watched, completed}`
- `cta_click` `{cta_id, section_id}`
- `checkout_start`
- `quote_refresh`
- `wallet_copy`
- `payment_marked_sent`
- `payment_verified`
- `email_delivered`

### Reglas técnicas
- IntersectionObserver thresholds `[0.25, 0.5, 0.75, 0.9]`.
- Cooldown por evento-sección (ej. 20s) para evitar spam.
- `dwell_time_ms` computado entre `section_enter` y `section_exit`.
- Consent mode para cookies/regiones aplicables.

---

## 7) Checklist SEO técnico (metadatos + schema + CWV)

### Metadata por ruta
- `title`, `description`, `canonical`, `robots`.
- OpenGraph (`og:title`, `og:description`, `og:image`, `og:type`).
- Twitter card (`summary_large_image`).

### Schema JSON-LD
- `Organization`
- `Product` (EasyGoldGlitch)
- `Offer` (precio + disponibilidad)
- `BreadcrumbList`
- `FAQPage` (si `/faq` activo)

### Indexación
- `sitemap.xml` dinámico.
- `robots.txt` correcto.
- Enlaces internos entre Home ↔ FAQ ↔ Terms ↔ Risk ↔ Checkout.

### Core Web Vitals targets
- LCP < 2.5s (video poster optimizado, fuentes preload selectivo).
- CLS < 0.1 (dimensiones fijas media/embeds).
- INP < 200ms (throttling handlers y animaciones GPU-friendly).

### Contenido
- Clusters: trading bot, XAU/XAUUSD, automatización, quant/HFT (sin keyword stuffing).
- Copy honesto: sin promesas de retorno.

---

## 8) Checklist QA / Performance / Accesibilidad

### QA funcional
- Flujo completo orden → pago → verificación → entrega email.
- Expiración real de cotización y refresh.
- Reintentos seguros en verificación.

### Performance
- Lazy-load de videos fuera de viewport.
- Preload adaptativo del primer capítulo.
- Bundle splitting por rutas.

### Accesibilidad
- Navegación por teclado (checkout completo).
- Labels/aria en controles críticos.
- `prefers-reduced-motion` en scrollytelling.
- Contraste en glass overlays.

### Seguridad/compliance
- Security headers (CSP, HSTS, X-Frame-Options, Referrer-Policy).
- Rate limiting endpoints críticos.
- Disclaimers legales visibles en Home + Checkout + Risk.

---

## 9) Backlog completo (tickets Jira-style, 34 tickets)

> Escala SP sugerida: 1, 2, 3, 5, 8, 13.

| ID | Epic | Título | Prioridad | SP | Dependencias |
|---|---|---|---|---:|---|
| EGG-001 | Foundation | Inicializar Next.js App Router + TS + Tailwind + ESLint/Prettier | P0 | 3 | - |
| EGG-002 | Foundation | Configurar design tokens (glass/gold) y tema oscuro | P0 | 3 | EGG-001 |
| EGG-003 | Foundation | Setup Prisma + Postgres + migraciones base | P0 | 5 | EGG-001 |
| EGG-004 | Foundation | Configuración env, secrets y typed config | P0 | 2 | EGG-001 |
| EGG-005 | Foundation | Integrar Sentry + logging estructurado | P1 | 3 | EGG-001 |
| EGG-006 | Content | Integrar Sanity (o content layer fallback) | P0 | 5 | EGG-001 |
| EGG-007 | Content | Modelo de contenido: capítulos, videos, CTA, FAQ | P0 | 3 | EGG-006 |
| EGG-008 | Content | Mini panel de ordenamiento de secciones/videos | P1 | 5 | EGG-007 |
| EGG-009 | UX Motion | Motor Lenis + fallback accesible | P0 | 3 | EGG-001 |
| EGG-010 | UX Motion | Scrollytelling capítulos sticky + parallax + unlock | P0 | 8 | EGG-009, EGG-007 |
| EGG-011 | UX Motion | Progress indicator + sticky CTA no invasivo | P0 | 3 | EGG-010 |
| EGG-012 | UX Motion | Microinteracciones brainrot controlado (glitch/scanline) | P1 | 5 | EGG-010 |
| EGG-013 | Media | Componente VideoBlock (autoplay muted inline) | P0 | 5 | EGG-010 |
| EGG-014 | Media | Pause/resume por viewport + captions opcionales | P0 | 3 | EGG-013 |
| EGG-015 | Funnel | Implementar secciones Home (Hero → Final CTA) | P0 | 8 | EGG-010, EGG-013 |
| EGG-016 | Funnel | Funnel Stepper 1/2/3 persistente | P0 | 3 | EGG-015 |
| EGG-017 | Checkout | UI checkout glass según spec visual | P0 | 8 | EGG-002 |
| EGG-018 | Checkout | Endpoint quote real (`/api/quote`) con TTL real | P0 | 5 | EGG-003 |
| EGG-019 | Checkout | Endpoint crear orden (`/api/order-intent`) | P0 | 5 | EGG-003, EGG-018 |
| EGG-020 | Checkout | Generación address único por orden (xpub derivación) | P0 | 8 | EGG-019 |
| EGG-021 | Checkout | Countdown real + quote refresh sincronizado | P0 | 3 | EGG-018, EGG-017 |
| EGG-022 | Checkout | Acción “I sent the payment” + estado pending | P0 | 3 | EGG-019 |
| EGG-023 | Payments | Chain watcher verificación tx + confirmaciones | P0 | 8 | EGG-020, EGG-022 |
| EGG-024 | Delivery | Entrega email con Resend + asset firmado | P0 | 5 | EGG-023 |
| EGG-025 | Compliance | Páginas /terms y /risk-disclosure con disclaimers fuertes | P0 | 3 | EGG-001 |
| EGG-026 | Compliance | Hardening copy (sin promesas ni claims engañosos) | P0 | 2 | EGG-015, EGG-017 |
| EGG-027 | Analytics | Instrumentar event taxonomy completa | P0 | 5 | EGG-015, EGG-017 |
| EGG-028 | Analytics | Anti-spam eventos con cooldown/throttle | P0 | 3 | EGG-027 |
| EGG-029 | SEO | Metadata por ruta + OG/Twitter + canonical | P0 | 3 | EGG-015 |
| EGG-030 | SEO | JSON-LD Product/Offer/Org/Breadcrumb/FAQ | P0 | 5 | EGG-029 |
| EGG-031 | SEO | sitemap.xml + robots.txt dinámicos | P0 | 2 | EGG-029 |
| EGG-032 | Security | Security headers + rate limiting + input validation | P0 | 5 | EGG-019 |
| EGG-033 | QA | Suite e2e funnel principal + smoke API | P1 | 5 | EGG-015, EGG-024 |
| EGG-034 | Performance | Optimización CWV + budget Lighthouse mobile ≥90 | P1 | 8 | EGG-015, EGG-017 |

### Criterios de aceptación (Given/When/Then) resumidos por ticket

- **EGG-010 Scrollytelling**
  - Given usuario en Home, When hace scroll, Then cada capítulo se activa con transición fluida y desbloquea el siguiente.
  - Given `prefers-reduced-motion`, When carga Home, Then se usa versión sin animaciones intensas.
- **EGG-013 VideoBlock**
  - Given video visible >50%, When entra viewport, Then autoplay muted inline inicia.
  - Given sale de viewport, When visibilidad <25%, Then pausa automática.
- **EGG-018 Quote real**
  - Given request válida, When se consulta quote, Then retorna `refPrice` + `expiresAt` real y trazable.
- **EGG-019 Crear orden**
  - Given email válido y consentimiento activo, When crea orden, Then responde `orderId`, `walletAddress`, `amountEth`, `quoteExpiresAt`.
- **EGG-023 Verificación chain**
  - Given pago detectado en address de orden, When alcanza confirmaciones requeridas, Then estado de orden pasa a `confirmed`.
- **EGG-024 Entrega email**
  - Given orden `confirmed`, When se procesa delivery, Then usuario recibe email con asset y se registra `email_delivered`.
- **EGG-027 Analytics**
  - Given navegación normal, When ocurren interacciones, Then se emiten eventos de taxonomía con payload requerido.
- **EGG-032 Security**
  - Given requests maliciosas o excesivas, When golpean APIs, Then se bloquean por validación/rate-limit y se registran logs.
- **EGG-034 Lighthouse**
  - Given build producción, When corre auditoría mobile, Then Perf/SEO/Best Practices ≥ 90.

Notas técnicas backlog:
- Evitar coupling fuerte entre CMS y render: usar mapeador `contentBlocks -> components`.
- No hardcodear videos: IDs y fuentes vienen de content layer.
- Mantener animaciones GPU-friendly (`transform/opacity`) y evitar layout thrashing.

---

## 10) Plan de sprints

## Sprint 1 (MVP funcional, 2 semanas)
Objetivo: funnel completo funcional con pago/verificación/entrega básica y compliance mínimo.

Incluye:
- Foundation: EGG-001..004
- Content mínimo: EGG-006..007
- Funnel + Home: EGG-009, EGG-010, EGG-011, EGG-013, EGG-014, EGG-015, EGG-016
- Checkout core: EGG-017..024
- Compliance/Security: EGG-025, EGG-026, EGG-032
- SEO base: EGG-029, EGG-031
- Analytics base: EGG-027

Exit criteria Sprint 1:
- Usuario puede recorrer funnel y comprar.
- Orden verificable on-chain y entrega por email.
- Disclaimers visibles y sin claims engañosos.

## Sprint 2 (Polish brainrot + SEO hardening, 2 semanas)
Objetivo: elevar calidad visual, analítica robusta y rendimiento/SEO enterprise-lite.

Incluye:
- UX polish: EGG-012
- CMS extra: EGG-008
- Analytics robusta: EGG-028
- SEO avanzado: EGG-030
- QA + perf: EGG-033, EGG-034
- Observabilidad: EGG-005

Exit criteria Sprint 2:
- Lighthouse mobile ≥90 (objetivo).
- Taxonomía de eventos completa y limpia.
- Calidad visual “Liquid Glass” estable a 60fps.

---

## 11) Riesgos técnicos/legales + mitigaciones

1. **Volatilidad de precio ETH**
   - Mitigar con quote lock TTL corto + margen controlado + expiración real.
2. **Conciliación de pagos ambigua**
   - Mitigar con address único por orden (xpub) y confirmaciones mínimas.
3. **Falsos positivos en verificación**
   - Mitigar con estado intermedio + confirmaciones + validación amount/network.
4. **Riesgo legal por claims de riqueza**
   - Tratar narrativa como mito de marca + disclaimers explícitos en Home/Checkout/Risk.
5. **Rendimiento afectado por exceso de animaciones/videos**
   - Mitigar con lazy/preload adaptativo y fallbacks por capacidad del dispositivo.
6. **Tracking invasivo/compliance privacidad**
   - Consent mode + anonimización + minimización de payload.
7. **Abuso de APIs**
   - Rate limits + captcha invisible opcional + logging/auditoría.

---

## 12) Definiciones finales de copy/compliance (guardrails)

- Permitido: narrativa de marca tipo “mito”, “filtración”, “unlock”.
- Obligatorio: “No es asesoría financiera”, “Trading conlleva riesgo”, “No se garantizan resultados”.
- Prohibido: promesas de retorno, “ganancia segura”, “dinero garantizado”.

Este plan entrega una base **no-estática**, con backend real, funnel guiado, checkout funcional P2P en ETH, tracking robusto y guardrails de compliance.

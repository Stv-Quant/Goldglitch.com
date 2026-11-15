-- Imágenes que los agentes de redes publican: Instagram exige una URL pública (JPEG). Se guardan en base64 y se
-- borran a los 14 días (para entonces Instagram y Facebook ya tienen su copia).
CREATE TABLE IF NOT EXISTS social_media (
  id         TEXT PRIMARY KEY,
  ct         TEXT NOT NULL,
  data       TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_social_media_created ON social_media(created_at);

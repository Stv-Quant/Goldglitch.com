-- Special one-time payment links (easygoldglitch.com/app/pago/<code>): fixed plan, price and, optionally, lifetime access.
CREATE TABLE IF NOT EXISTS payment_codes (
  code            TEXT PRIMARY KEY,
  plan            TEXT NOT NULL CHECK (plan IN ('pro','elite')),
  amount_in_cents INTEGER NOT NULL CHECK (amount_in_cents > 0),
  lifetime        INTEGER NOT NULL DEFAULT 0,
  note            TEXT,
  created_at      INTEGER NOT NULL,
  used_at         INTEGER,
  used_by         TEXT REFERENCES users(id),
  payment_id      TEXT
);

ALTER TABLE payments ADD COLUMN code TEXT;   -- payment_codes.code when the payment came from a special link
ALTER TABLE payments ADD COLUMN note TEXT;   -- e.g. "Prueba pasarela de pagos"

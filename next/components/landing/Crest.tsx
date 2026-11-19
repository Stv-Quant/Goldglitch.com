"use client";

import { useState } from "react";

/** Team crest with a monogram fallback (no crest, blocked CDN, broken image): never an empty hole. */
export function Crest({ src, name, size = 40, className = "" }: { src?: string; name: string; size?: number; className?: string }) {
  const [broken, setBroken] = useState(false);
  const initials = name.replace(/[^\p{L}\p{N} ]/gu, "").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";
  return (
    <span className={`crest ${className}`} style={{ width: size, height: size }}>
      {src && !broken ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" width={size} height={size} loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setBroken(true)} />
      ) : (
        <span className="crest-mono num" style={{ fontSize: Math.max(9, size * 0.32) }} aria-hidden>{initials}</span>
      )}
      <span className="sr-only">{name}</span>
    </span>
  );
}

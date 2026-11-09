import Link from "next/link";

/** Original mark: a calibration ring framing three ascending probability bars. */
export function Mark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <circle cx="16" cy="16" r="14" fill="none" stroke="var(--gold)" strokeWidth="1.6" />
      <circle cx="16" cy="16" r="10.5" fill="none" stroke="var(--gold)" strokeOpacity=".25" strokeWidth="1" />
      <rect x="10" y="17" width="3" height="6" rx="1" fill="var(--gold)" fillOpacity=".45" />
      <rect x="14.5" y="13" width="3" height="10" rx="1" fill="var(--gold)" fillOpacity=".7" />
      <rect x="19" y="9" width="3" height="14" rx="1" fill="var(--gold)" />
    </svg>
  );
}

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2.5" aria-label="Goldglitch, inicio">
      <Mark />
      <span className="text-[15px] font-semibold tracking-tight">
        Goldglitch<span className="text-lo font-normal"> · Stats</span>
      </span>
    </Link>
  );
}

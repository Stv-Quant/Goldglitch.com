import { Suspense } from "react";
import { AppHome } from "@/components/app/AppHome";

/**
 * App home. The page itself is a static shell; the list is fetched from /api/app/matches and drawn in the browser.
 * Rendering hundreds of match cards on the server exceeded the Workers free plan's CPU limit (error 1102).
 */
export default function MatchesPage() {
  return (
    <Suspense>
      <AppHome />
    </Suspense>
  );
}

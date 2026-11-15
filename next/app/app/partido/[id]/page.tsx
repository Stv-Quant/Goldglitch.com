import { MatchClient } from "@/components/app/MatchClient";

/** Static shell: the sheet is fetched from /api/app/match/[id] and drawn in the browser (keeps server CPU minimal). */
export default async function MatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MatchClient id={decodeURIComponent(id)} />;
}

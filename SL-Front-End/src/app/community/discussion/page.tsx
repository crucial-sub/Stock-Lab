import { FreeBoardListPageClient } from "./FreeBoardListPageClient";

export default function DiscussionPage({
  searchParams,
}: {
  searchParams: Record<string, string | undefined>;
}) {
  return <FreeBoardListPageClient searchParams={searchParams} />;
}

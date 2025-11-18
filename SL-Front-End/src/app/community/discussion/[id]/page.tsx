import { FreeBoardDetailPageClient } from "./FreeBoardDetailPageClient";

export default function DiscussionDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return <FreeBoardDetailPageClient postId={params.id} />;
}

import { apiFetch } from "../../shared/api/client";
import type { TagCloudItem } from "../../shared/api/types";

export async function fetchTagCloud(params: URLSearchParams): Promise<TagCloudItem[]> {
  const qs = params.toString();
  return apiFetch<TagCloudItem[]>(`/stats/tag-cloud${qs ? `?${qs}` : ""}`);
}

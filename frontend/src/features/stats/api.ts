import { apiFetch } from "../../shared/api/client";
import type { QuoteCountItem, StatsSummary, WordCountItem } from "../../shared/api/types";

export async function fetchSummary(): Promise<StatsSummary> {
  return apiFetch<StatsSummary>("/stats/summary");
}

export async function fetchTopWords(params: URLSearchParams): Promise<WordCountItem[]> {
  const qs = params.toString();
  return apiFetch<WordCountItem[]>(`/stats/top-words${qs ? `?${qs}` : ""}`);
}

export async function fetchTopQuotes(params: URLSearchParams): Promise<QuoteCountItem[]> {
  const qs = params.toString();
  return apiFetch<QuoteCountItem[]>(`/stats/top-quotes${qs ? `?${qs}` : ""}`);
}

import { apiFetch } from "../../shared/api/client";
import type { Entry } from "../../shared/api/types";

export async function fetchEntries(params: URLSearchParams): Promise<Entry[]> {
  const qs = params.toString();
  return apiFetch<Entry[]>(`/entries${qs ? `?${qs}` : ""}`);
}

export async function fetchEntry(id: string): Promise<Entry> {
  return apiFetch<Entry>(`/entries/${id}`);
}

export async function updateEntry(id: string, text: string, correctText = false): Promise<Entry> {
  return apiFetch<Entry>(`/entries/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ text, correct_text: correctText }),
  });
}

export async function deleteEntry(id: string): Promise<void> {
  await apiFetch<void>(`/entries/${id}`, { method: "DELETE" });
}

export async function retagEntry(id: string): Promise<Entry> {
  return apiFetch<Entry>(`/entries/${id}/retag`, { method: "POST" });
}

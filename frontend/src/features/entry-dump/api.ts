import { apiFetch } from "../../shared/api/client";
import type { Entry } from "../../shared/api/types";

export async function createEntry(text: string, correctText = false): Promise<Entry> {
  return apiFetch<Entry>("/entries", {
    method: "POST",
    body: JSON.stringify({ text, source: "web", correct_text: correctText }),
  });
}

import { apiFetch } from "./client";
import type { TextSearchResult } from "./types";

export function searchNodes(text: string, k = 20) {
  return apiFetch<TextSearchResult[]>("/search/nodes", {
    method: "POST",
    body: JSON.stringify({ text, k }),
  });
}

import { useQuery } from "@tanstack/react-query";
import { searchNodes } from "../api/search";

export function useNodeSearch(text: string, k = 20) {
  return useQuery({
    queryKey: ["search-nodes", text, k],
    queryFn: () => searchNodes(text, k),
    enabled: text.length >= 2,
  });
}

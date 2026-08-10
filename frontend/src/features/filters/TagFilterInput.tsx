import { useState } from "react";
import type { TagCloudItem } from "../../shared/api/types";
import { TagChip } from "../../shared/ui/TagChip";

interface Props {
  allTags: TagCloudItem[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

export function TagFilterInput({ allTags, selectedIds, onChange }: Props) {
  const [query, setQuery] = useState("");

  const selected = allTags.filter((t) => selectedIds.includes(t.id));
  const suggestions = allTags
    .filter((t) => !selectedIds.includes(t.id))
    .filter((t) => t.canonical_name.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 12);

  function add(id: string) {
    onChange([...selectedIds, id]);
    setQuery("");
  }

  function remove(id: string) {
    onChange(selectedIds.filter((x) => x !== id));
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6em" }}>
      {selected.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4em" }}>
          {selected.map((t) => (
            <span key={t.id} style={{ display: "inline-flex", alignItems: "center", gap: "0.2em" }}>
              <TagChip name={t.canonical_name} color={t.color} onClick={() => remove(t.id)} />
            </span>
          ))}
        </div>
      )}
      <input
        className="minimal-input"
        style={{ width: "100%" }}
        type="text"
        placeholder="Фильтр по тегу…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {suggestions.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4em" }}>
          {suggestions.map((t) => (
            <TagChip key={t.id} name={t.canonical_name} color={t.color} onClick={() => add(t.id)} />
          ))}
        </div>
      )}
    </div>
  );
}

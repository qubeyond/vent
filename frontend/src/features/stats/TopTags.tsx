import type { TagCloudItem } from "../../shared/api/types";
import { TagChip } from "../../shared/ui/TagChip";

interface Props {
  items: TagCloudItem[];
  onSelect: (tag: TagCloudItem) => void;
}

export function TopTags({ items, onSelect }: Props) {
  const top5 = items.slice(0, 5);
  if (top5.length === 0) return <p className="muted">Недостаточно данных.</p>;

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5em" }}>
      {top5.map((item) => (
        <TagChip
          key={item.id}
          name={`${item.canonical_name} · ${item.count}`}
          color={item.color}
          fontSize="0.95em"
          onClick={() => onSelect(item)}
        />
      ))}
    </div>
  );
}

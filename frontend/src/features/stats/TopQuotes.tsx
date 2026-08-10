import type { QuoteCountItem } from "../../shared/api/types";

export function TopQuotes({ items }: { items: QuoteCountItem[] }) {
  if (items.length === 0) return <p className="muted">Повторяющихся цитат пока нет.</p>;
  return (
    <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: "0.5em" }}>
      {items.map((item) => (
        <li key={item.quote} style={{ borderLeft: "3px solid var(--accent)", paddingLeft: "0.7em" }}>
          «{item.quote}» <span className="muted">×{item.count}</span>
        </li>
      ))}
    </ul>
  );
}

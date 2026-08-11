import { Link } from "react-router-dom";
import type { Entry } from "../../shared/api/types";
import { TagChip } from "../../shared/ui/TagChip";
import { formatDateTime } from "../../shared/lib/formatDate";
import { countChars, pluralizeChars } from "../../shared/lib/textStats";

const MAX_TAGS = 5;
const EXCERPT_LENGTH = 220;

interface Props {
  entries: Entry[];
  activeTagIds?: string[];
  dateActive?: boolean;
  search?: string;
}

function Excerpt({ text, search }: { text: string; search?: string }) {
  const lowerSearch = search?.toLowerCase();
  const matchIndex = lowerSearch ? text.toLowerCase().indexOf(lowerSearch) : -1;
  const windowStart = matchIndex === -1 ? 0 : matchIndex;
  const windowEnd = Math.min(text.length, windowStart + EXCERPT_LENGTH);
  const window = text.slice(windowStart, windowEnd);
  const leadingEllipsis = windowStart > 0;
  const trailingEllipsis = windowEnd < text.length;

  if (!lowerSearch) {
    return (
      <>
        {leadingEllipsis && "…"}
        {window}
        {trailingEllipsis && "…"}
      </>
    );
  }

  const lowerWindow = window.toLowerCase();
  const parts: { text: string; match: boolean }[] = [];
  let cursor = 0;
  while (cursor < window.length) {
    const idx = lowerWindow.indexOf(lowerSearch, cursor);
    if (idx === -1) {
      parts.push({ text: window.slice(cursor), match: false });
      break;
    }
    if (idx > cursor) parts.push({ text: window.slice(cursor, idx), match: false });
    parts.push({ text: window.slice(idx, idx + lowerSearch.length), match: true });
    cursor = idx + lowerSearch.length;
  }

  return (
    <>
      {leadingEllipsis && <span className="muted">…</span>}
      {parts.map((p, i) =>
        p.match ? (
          <span key={i} style={{ color: "var(--text-h)" }}>
            {p.text}
          </span>
        ) : (
          <span key={i} className="muted">
            {p.text}
          </span>
        ),
      )}
      {trailingEllipsis && <span className="muted">…</span>}
    </>
  );
}

export function EntriesList({ entries, activeTagIds = [], dateActive = false, search = "" }: Props) {
  if (entries.length === 0) {
    return <p className="muted">Нет записей за выбранный период.</p>;
  }

  return (
    <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: "0.8em" }}>
      {entries.map((entry) => {
        const sortedTags =
          activeTagIds.length > 0
            ? [...entry.tags].sort(
                (a, b) => Number(activeTagIds.includes(b.id)) - Number(activeTagIds.includes(a.id)),
              )
            : entry.tags;
        const visibleTags = sortedTags.slice(0, MAX_TAGS);
        const restCount = entry.tags.length - visibleTags.length;
        const chars = countChars(entry.raw_text);
        return (
          <li key={entry.id}>
            <Link
              to={`/entries/${entry.id}`}
              style={{
                display: "block",
                border: "1px solid var(--border)",
                borderRadius: 10,
                padding: "0.8em",
                textDecoration: "none",
                color: "inherit",
                transition: "border-color 0.12s ease",
              }}
            >
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6em", fontSize: "0.85em", marginBottom: "0.3em" }}>
                <span
                  className={dateActive ? undefined : "muted"}
                  style={{ color: dateActive ? "var(--text-h)" : undefined }}
                >
                  {formatDateTime(entry.created_at)}
                  {entry.edited_at && " · ред."}
                </span>
                <span className="muted" style={{ opacity: 0.5 }}>
                  ·
                </span>
                <span className="muted">
                  {chars} {pluralizeChars(chars)}
                </span>
              </div>
              <p
                style={{
                  margin: "0 0 0.5em",
                  overflow: "hidden",
                  display: "-webkit-box",
                  WebkitLineClamp: 4,
                  WebkitBoxOrient: "vertical",
                }}
              >
                <Excerpt text={entry.raw_text} search={search} />
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4em", alignItems: "center" }}>
                {visibleTags.map((tag) => (
                  <TagChip
                    key={tag.id}
                    name={tag.canonical_name}
                    color={tag.color}
                    selected={activeTagIds.includes(tag.id)}
                    dim={activeTagIds.length > 0 && !activeTagIds.includes(tag.id)}
                  />
                ))}
                {restCount > 0 && <span className="muted" style={{ fontSize: "0.8em" }}>+{restCount}</span>}
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

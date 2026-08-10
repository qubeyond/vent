import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { TagCloudCanvas } from "../features/tag-cloud/TagCloudCanvas";
import { fetchTagCloud } from "../features/tag-cloud/api";
import { EntriesList } from "../features/entries-list/EntriesList";
import { fetchEntries } from "../features/entries-list/api";
import { FilterPanel } from "../features/filters/FilterPanel";
import { dateRangeToParams, type DateRange } from "../shared/ui/DateRangeFilter";
import { FunnelIcon } from "../shared/ui/icons";
import { TagChip } from "../shared/ui/TagChip";
import type { Entry, TagCloudItem } from "../shared/api/types";

type View = "cloud" | "notes";

export function CloudPage() {
  const [searchParams] = useSearchParams();
  const initialTag = searchParams.get("tag");
  const initialSearch = searchParams.get("search") ?? "";

  const [view, setView] = useState<View>("notes");
  const [dateRange, setDateRange] = useState<DateRange>({ from: "", to: "" });
  const [tagIds, setTagIds] = useState<string[]>(initialTag ? [initialTag] : []);
  const [search, setSearch] = useState(initialSearch);
  const [filterOpen, setFilterOpen] = useState(false);

  const [tags, setTags] = useState<TagCloudItem[]>([]);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [isLoadingCloud, setIsLoadingCloud] = useState(true);
  const [isLoadingEntries, setIsLoadingEntries] = useState(true);

  useEffect(() => {
    const params = dateRangeToParams(dateRange);
    if (search.trim()) params.set("search", search.trim());
    setIsLoadingCloud(true);
    fetchTagCloud(params)
      .then(setTags)
      .finally(() => setIsLoadingCloud(false));
  }, [dateRange, search]);

  useEffect(() => {
    const params = dateRangeToParams(dateRange);
    params.set("limit", "200");
    for (const id of tagIds) params.append("tag_ids", id);
    if (search.trim()) params.set("search", search.trim());
    setIsLoadingEntries(true);
    fetchEntries(params)
      .then(setEntries)
      .finally(() => setIsLoadingEntries(false));
  }, [dateRange, tagIds, search]);

  const tagsById = new Map(tags.map((t) => [t.id, t]));
  const activeTags = tagIds
    .map((id) => tagsById.get(id))
    .filter((t): t is TagCloudItem => Boolean(t));
  const hasActiveFilters = Boolean(dateRange.from || dateRange.to || tagIds.length > 0 || search.trim());

  const visibleCloudTags = tagIds.length > 0 ? tags.filter((t) => tagIds.includes(t.id)) : tags;

  return (
    <div
      style={{
        padding: "1.2em",
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "safe center",
        minHeight: 0,
        gap: "1em",
      }}
    >
      <section style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.8em" }}>
        <div className="segmented">
          <button
            type="button"
            className={`segmented-btn${view === "notes" ? " active" : ""}`}
            onClick={() => setView("notes")}
          >
            Заметки
          </button>
          <button
            type="button"
            className={`segmented-btn${view === "cloud" ? " active" : ""}`}
            onClick={() => setView("cloud")}
          >
            Облако
          </button>
        </div>
        <button
          type="button"
          className="icon-btn"
          title="Фильтры"
          aria-label="Фильтры"
          onClick={() => setFilterOpen(true)}
        >
          <FunnelIcon />
        </button>
      </section>

      {hasActiveFilters && (
        <div className="muted" style={{ fontSize: "0.8em", display: "flex", flexDirection: "column", gap: "0.35em" }}>
          {(dateRange.from || dateRange.to) && (
            <div>Период: {dateRange.from || "…"} – {dateRange.to || "…"}</div>
          )}
          {activeTags.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.35em" }}>
              Теги:
              {activeTags.map((t) => (
                <TagChip key={t.id} name={t.canonical_name} color={t.color} fontSize="0.85em" />
              ))}
            </div>
          )}
          {search.trim() && <div>Поиск: «{search.trim()}»</div>}
          {view === "notes" && !isLoadingEntries && <div>Найдено: {entries.length}</div>}
        </div>
      )}

      {view === "cloud" ? (
        isLoadingCloud ? (
          <p className="muted">Загрузка…</p>
        ) : (
          <TagCloudCanvas
            tags={visibleCloudTags}
            onSelectTag={(tag) => {
              setTagIds([tag.id]);
              setView("notes");
            }}
          />
        )
      ) : isLoadingEntries ? (
        <p className="muted">Загрузка…</p>
      ) : (
        <EntriesList entries={entries} activeTagIds={tagIds} dateActive={Boolean(dateRange.from || dateRange.to)} search={search.trim()} />
      )}

      <FilterPanel
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        allTags={tags}
        selectedTagIds={tagIds}
        onTagIdsChange={setTagIds}
        search={search}
        onSearchChange={setSearch}
      />
    </div>
  );
}

import { DateRangeFilter, type DateRange } from "../../shared/ui/DateRangeFilter";
import { Modal } from "../../shared/ui/Modal";
import { useMediaQuery } from "../../shared/lib/useMediaQuery";
import { TagFilterInput } from "./TagFilterInput";
import type { TagCloudItem } from "../../shared/api/types";

interface Props {
  open: boolean;
  onClose: () => void;
  dateRange: DateRange;
  onDateRangeChange: (v: DateRange) => void;
  allTags: TagCloudItem[];
  selectedTagIds: string[];
  onTagIdsChange: (ids: string[]) => void;
  search: string;
  onSearchChange: (v: string) => void;
}

function FilterControls({
  dateRange,
  onDateRangeChange,
  allTags,
  selectedTagIds,
  onTagIdsChange,
  search,
  onSearchChange,
}: Omit<Props, "open" | "onClose">) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.2em" }}>
      <h3 style={{ margin: 0 }}>Фильтры</h3>
      <div>
        <div className="muted" style={{ fontSize: "0.8em", marginBottom: "0.4em" }}>
          Поиск по тексту
        </div>
        <input
          type="text"
          placeholder="Любой текст…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
      <div>
        <div className="muted" style={{ fontSize: "0.8em", marginBottom: "0.4em" }}>
          Теги
        </div>
        <TagFilterInput allTags={allTags} selectedIds={selectedTagIds} onChange={onTagIdsChange} />
      </div>
      <div>
        <div className="muted" style={{ fontSize: "0.8em", marginBottom: "0.4em" }}>
          Период
        </div>
        <DateRangeFilter value={dateRange} onChange={onDateRangeChange} />
      </div>
    </div>
  );
}

export function FilterPanel(props: Props) {
  const isDesktop = useMediaQuery("(min-width: 720px)");

  if (isDesktop) {
    return (
      <>
        {props.open && (
          <div
            style={{ position: "fixed", inset: 0, zIndex: 27 }}
            onClick={props.onClose}
          />
        )}
        <div className={`filter-panel${props.open ? " open" : ""}`}>
          <FilterControls {...props} />
        </div>
      </>
    );
  }

  return (
    <Modal open={props.open} onClose={props.onClose}>
      <FilterControls {...props} />
    </Modal>
  );
}

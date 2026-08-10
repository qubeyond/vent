export interface DateRange {
  from: string;
  to: string;
}

interface Props {
  value: DateRange;
  onChange: (value: DateRange) => void;
}

export function DateRangeFilter({ value, onChange }: Props) {
  return (
    <div style={{ display: "flex", gap: "0.8em", alignItems: "center", flexWrap: "wrap" }}>
      <label className="muted" style={{ display: "flex", gap: "0.4em", alignItems: "center" }}>
        с
        <input
          type="date"
          className="minimal-input"
          value={value.from}
          onChange={(e) => onChange({ ...value, from: e.target.value })}
        />
      </label>
      <label className="muted" style={{ display: "flex", gap: "0.4em", alignItems: "center" }}>
        по
        <input
          type="date"
          className="minimal-input"
          value={value.to}
          onChange={(e) => onChange({ ...value, to: e.target.value })}
        />
      </label>
      {(value.from || value.to) && (
        <button
          type="button"
          className="minimal-input"
          style={{ border: "none", cursor: "pointer" }}
          onClick={() => onChange({ from: "", to: "" })}
        >
          Сбросить
        </button>
      )}
    </div>
  );
}

export function dateRangeToParams(range: DateRange): URLSearchParams {
  const params = new URLSearchParams();
  if (range.from) params.set("date_from", `${range.from}T00:00:00`);
  if (range.to) params.set("date_to", `${range.to}T23:59:59`);
  return params;
}

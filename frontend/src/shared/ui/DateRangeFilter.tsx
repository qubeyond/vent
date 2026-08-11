import { useEffect, useRef, useState } from "react";
import { CalendarIcon } from "./icons";

export interface DateRange {
  from: string;
  to: string;
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

interface FieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

function DateField({ label, value, onChange }: FieldProps) {
  const [draft, setDraft] = useState(value);
  const pickerRef = useRef<HTMLInputElement>(null);

  useEffect(() => setDraft(value), [value]);

  function commit(next: string) {
    setDraft(next);
    if (next === "" || DATE_RE.test(next)) onChange(next);
  }

  return (
    <label className="muted" style={{ display: "flex", gap: "0.3em", alignItems: "center" }}>
      {label}
      <input
        type="text"
        inputMode="numeric"
        placeholder="ГГГГ-ММ-ДД"
        className="minimal-input"
        value={draft}
        onChange={(e) => commit(e.target.value.trim())}
        style={{ width: "7em" }}
      />
      <button
        type="button"
        className="icon-btn"
        title="Открыть календарь"
        aria-label="Открыть календарь"
        onClick={() => pickerRef.current?.showPicker?.()}
      >
        <CalendarIcon />
      </button>
      <input
        ref={pickerRef}
        type="date"
        value={DATE_RE.test(value) ? value : ""}
        onChange={(e) => commit(e.target.value)}
        tabIndex={-1}
        aria-hidden="true"
        style={{ position: "absolute", width: 0, height: 0, opacity: 0, pointerEvents: "none" }}
      />
    </label>
  );
}

interface Props {
  value: DateRange;
  onChange: (value: DateRange) => void;
}

export function DateRangeFilter({ value, onChange }: Props) {
  return (
    <div style={{ display: "flex", gap: "0.8em", alignItems: "center", flexWrap: "wrap" }}>
      <DateField label="с" value={value.from} onChange={(from) => onChange({ ...value, from })} />
      <DateField label="по" value={value.to} onChange={(to) => onChange({ ...value, to })} />
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

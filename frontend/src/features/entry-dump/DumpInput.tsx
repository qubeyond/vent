import { useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import { AutoTextarea } from "../../shared/ui/AutoTextarea";
import { Switch } from "../../shared/ui/Switch";
import { countChars, pluralizeChars } from "../../shared/lib/textStats";
import { createEntry } from "./api";
import { ApiError } from "../../shared/api/client";

interface Props {
  initialText?: string;
}

export function DumpInput({ initialText }: Props) {
  const [text, setText] = useState(initialText ?? "");
  const [correctText, setCorrectText] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function submit() {
    const trimmed = text.trim();
    if (!trimmed || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const entry = await createEntry(trimmed, correctText);
      navigate(`/entries/${entry.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось связаться с сервером");
      setIsSubmitting(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      void submit();
    }
  }

  const charCount = countChars(text);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6em" }}>
      <AutoTextarea
        placeholder="Что в голове? Просто выпиши…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus
        rows={8}
        style={{ color: "var(--text-h)" }}
      />
      <div className="muted" style={{ fontSize: "0.8em", textAlign: "right" }}>
        {charCount} {pluralizeChars(charCount)}
      </div>
      {error && <span className="error-text">{error}</span>}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.8em", flexWrap: "wrap" }}>
        <Switch checked={correctText} onChange={setCorrectText} label="Исправить орфографию и пунктуацию" />
        <button type="button" className="primary" onClick={() => void submit()} disabled={!text.trim() || isSubmitting}>
          {isSubmitting ? "Сохраняю…" : "Создать"}
        </button>
      </div>
    </div>
  );
}

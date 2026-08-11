import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { deleteEntry, fetchEntry, retagEntry, updateEntry } from "../features/entries-list/api";
import type { Entry } from "../shared/api/types";
import { ApiError } from "../shared/api/client";
import { TagChip } from "../shared/ui/TagChip";
import { AutoTextarea } from "../shared/ui/AutoTextarea";
import { ConfirmDeleteModal } from "../shared/ui/ConfirmDeleteModal";
import { Switch } from "../shared/ui/Switch";
import { PencilIcon, RefreshIcon, TrashIcon } from "../shared/ui/icons";
import { formatDateTime } from "../shared/lib/formatDate";
import { countChars, pluralizeChars } from "../shared/lib/textStats";

const POLL_INTERVAL_MS = 1500;

function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status >= 500) return `Проблема на сервере: ${err.message}`;
    return err.message;
  }
  return "Не удалось связаться с сервером — проблема на фронте или в сети";
}

export function EntryPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [entry, setEntry] = useState<Entry | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [correctOnSave, setCorrectOnSave] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditingRef = useRef(isEditing);
  useEffect(() => {
    isEditingRef.current = isEditing;
  }, [isEditing]);

  const pollGenerationRef = useRef(0);

  async function pollUntilReady(entryId: string) {
    const myGeneration = ++pollGenerationRef.current;
    while (pollGenerationRef.current === myGeneration) {
      try {
        const fresh = await fetchEntry(entryId);
        if (pollGenerationRef.current !== myGeneration) return;
        setEntry(fresh);
        if (!isEditingRef.current) setDraft(fresh.raw_text);
        if (fresh.status !== "processing") return;
      } catch (err) {
        if (pollGenerationRef.current !== myGeneration) return;
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else setError(describeError(err));
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
    }
  }

  useEffect(() => {
    if (!id) return;
    void pollUntilReady(id);
    return () => {
      pollGenerationRef.current++;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleSave() {
    if (!id || !draft.trim()) return;
    setIsSaving(true);
    setError(null);
    try {
      const updated = await updateEntry(id, draft.trim(), correctOnSave);
      setEntry(updated);
      setIsEditing(false);
      if (updated.status === "processing") void pollUntilReady(id);
    } catch (err) {
      setError(describeError(err));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRetag() {
    if (!id) return;
    setError(null);
    try {
      const started = await retagEntry(id);
      setEntry(started);
      void pollUntilReady(id);
    } catch (err) {
      setError(describeError(err));
    }
  }

  async function handleDelete() {
    if (!id) return;
    setConfirmingDelete(false);
    try {
      await deleteEntry(id);
      navigate("/cloud", { replace: true });
    } catch (err) {
      setError(describeError(err));
    }
  }

  if (notFound) {
    return (
      <div style={{ padding: "1.2em", flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <p className="muted">Запись не найдена — возможно, уже удалена.</p>
      </div>
    );
  }

  if (!entry) {
    return (
      <div style={{ padding: "1.2em", flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <p className="muted">Загрузка…</p>
      </div>
    );
  }

  const isProcessing = entry.status === "processing";

  return (
    <div
      style={{
        padding: "1.2em",
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "safe center",
        minHeight: 0,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "1em" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "0.6em",
          }}
        >
          <div className="muted" style={{ fontSize: "0.85em", display: "flex", flexDirection: "column", gap: "0.2em" }}>
            <div>Создано · {formatDateTime(entry.created_at)}</div>
            {entry.edited_at && <div>Отредактировано · {formatDateTime(entry.edited_at)}</div>}
            <div>{countChars(entry.raw_text)} {pluralizeChars(countChars(entry.raw_text))}</div>
          </div>

          {!isEditing && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.4em" }}>
              {isProcessing && (
                <span className="muted" style={{ fontSize: "0.75em" }}>
                  Обрабатываю…
                </span>
              )}
              <button
                type="button"
                className="icon-btn"
                title="Перетегировать (ИИ заново разложит по темам)"
                aria-label="Перетегировать"
                onClick={() => void handleRetag()}
                disabled={isProcessing}
              >
                <RefreshIcon
                  style={isProcessing ? { animation: "spin 0.8s linear infinite" } : undefined}
                />
              </button>
              <button
                type="button"
                className="icon-btn icon-btn-accent"
                title="Редактировать"
                aria-label="Редактировать"
                onClick={() => setIsEditing(true)}
                disabled={isProcessing}
              >
                <PencilIcon />
              </button>
              <button
                type="button"
                className="icon-btn icon-btn-danger"
                title="Удалить"
                aria-label="Удалить"
                onClick={() => setConfirmingDelete(true)}
              >
                <TrashIcon />
              </button>
            </div>
          )}
        </div>

        {isEditing ? (
          <AutoTextarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={6}
            autoFocus
          />
        ) : (
          <p style={{ margin: 0 }}>{entry.raw_text}</p>
        )}

        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4em" }}>
          {entry.tags.map((tag) => (
            <TagChip key={tag.id} name={tag.canonical_name} color={tag.color} />
          ))}
        </div>

        {entry.processing_error && (
          <span className="error-text">{entry.processing_error}</span>
        )}
        {error && <span className="error-text">{error}</span>}

        {isEditing && (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.8em", flexWrap: "wrap" }}>
            <Switch checked={correctOnSave} onChange={setCorrectOnSave} label="Исправить орфографию и пунктуацию" />
            <div style={{ display: "flex", gap: "0.6em" }}>
              <button type="button" className="primary" onClick={handleSave} disabled={isSaving}>
                {isSaving ? "Сохраняю…" : "Сохранить"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setDraft(entry.raw_text);
                  setIsEditing(false);
                }}
              >
                Отмена
              </button>
            </div>
          </div>
        )}
      </div>

      <ConfirmDeleteModal
        open={confirmingDelete}
        label="Удалить запись без возможности восстановить?"
        onConfirm={() => void handleDelete()}
        onCancel={() => setConfirmingDelete(false)}
      />
    </div>
  );
}

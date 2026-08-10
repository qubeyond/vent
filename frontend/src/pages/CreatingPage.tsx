import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { createEntry } from "../features/entry-dump/api";
import { ApiError } from "../shared/api/client";

const STEPS_PLAIN = ["Сохраняю текст", "ИИ анализирует", "Раскладываю по темам", "Готово"];
const STEPS_WITH_CORRECTION = [
  "Сохраняю текст",
  "Правлю текст",
  "ИИ анализирует",
  "Раскладываю по темам",
  "Готово",
];

export function CreatingPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as { text?: string; correctText?: boolean } | null;
  const text = state?.text;
  const correctText = state?.correctText ?? false;
  const STEPS = correctText ? STEPS_WITH_CORRECTION : STEPS_PLAIN;

  const [activeIndex, setActiveIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!text) {
      navigate("/", { replace: true });
      return;
    }
    if (startedRef.current) return;
    startedRef.current = true;

    const timeouts = correctText
      ? [setTimeout(() => setActiveIndex(1), 400), setTimeout(() => setActiveIndex(2), 1100), setTimeout(() => setActiveIndex(3), 1900)]
      : [setTimeout(() => setActiveIndex(1), 450), setTimeout(() => setActiveIndex(2), 1300)];

    createEntry(text, correctText)
      .then((entry) => {
        for (const t of timeouts) clearTimeout(t);
        setActiveIndex(STEPS.length - 1);
        setTimeout(() => navigate(`/entries/${entry.id}`, { replace: true }), 350);
      })
      .catch((err: unknown) => {
        for (const t of timeouts) clearTimeout(t);
        setError(err instanceof ApiError ? err.message : "Не удалось связаться с сервером");
      });

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, correctText, navigate]);

  if (!text) return null;

  return (
    <div
      style={{
        flex: 1,
        padding: "1.2em",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "2em",
      }}
    >
      <div className="steps-timeline">
        {STEPS.map((label, i) => {
          const stepState = i < activeIndex ? "done" : i === activeIndex && !error ? "active" : "";
          const side = i % 2 === 0 ? "side-a" : "side-b";
          return (
            <div key={label} className={`step-item ${stepState} ${side}`}>
              <span className={`step-dot ${stepState}`} />
              <span className="step-label">{label}</span>
            </div>
          );
        })}
      </div>

      {error && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.8em" }}>
          <span className="error-text">{error}</span>
          <button
            type="button"
            onClick={() => navigate("/", { replace: true, state: { draft: text } })}
          >
            Назад к тексту
          </button>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { TopTags } from "../features/stats/TopTags";
import { WordCloudCanvas } from "../features/stats/WordCloudCanvas";
import { TopQuotes } from "../features/stats/TopQuotes";
import { fetchSummary, fetchTopWords, fetchTopQuotes } from "../features/stats/api";
import { fetchTagCloud } from "../features/tag-cloud/api";
import type { QuoteCountItem, StatsSummary, TagCloudItem, WordCountItem } from "../shared/api/types";

export function StatsPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<StatsSummary | null>(null);
  const [topTags, setTopTags] = useState<TagCloudItem[]>([]);
  const [topWords, setTopWords] = useState<WordCountItem[]>([]);
  const [topQuotes, setTopQuotes] = useState<QuoteCountItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const empty = new URLSearchParams();
    Promise.all([fetchSummary(), fetchTagCloud(empty), fetchTopWords(empty), fetchTopQuotes(empty)])
      .then(([s, tags, words, quotes]) => {
        setSummary(s);
        setTopTags(tags);
        setTopWords(words);
        setTopQuotes(quotes);
      })
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div style={{ padding: "1.2em", display: "flex", flexDirection: "column", gap: "1.4em" }}>
      <section style={{ display: "flex", gap: "1.6em", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: "1.6em", fontWeight: 700, color: "var(--text-h)" }}>
            {summary?.total_entries ?? "…"}
          </div>
          <div className="muted" style={{ fontSize: "0.85em" }}>
            Всего заметок
          </div>
        </div>
        <div>
          <div style={{ fontSize: "1.6em", fontWeight: 700, color: "var(--text-h)" }}>
            {summary?.total_tags ?? "…"}
          </div>
          <div className="muted" style={{ fontSize: "0.85em" }}>
            Всего тегов
          </div>
        </div>
        <div>
          <div style={{ fontSize: "1.6em", fontWeight: 700, color: "var(--text-h)" }}>
            {summary?.total_chars ?? "…"}
          </div>
          <div className="muted" style={{ fontSize: "0.85em" }}>
            Всего символов
          </div>
        </div>
      </section>

      {isLoading ? (
        <p className="muted">Загрузка…</p>
      ) : (
        <>
          <section>
            <h2>Топ тегов</h2>
            <TopTags items={topTags} onSelect={(tag) => navigate(`/cloud?tag=${tag.id}`)} />
          </section>

          <section>
            <h2>Облако слов</h2>
            <WordCloudCanvas items={topWords} onWordClick={(word) => navigate(`/cloud?search=${encodeURIComponent(word)}`)} />
          </section>

          <section>
            <h2>Цитаты</h2>
            <TopQuotes items={topQuotes} />
          </section>
        </>
      )}
    </div>
  );
}

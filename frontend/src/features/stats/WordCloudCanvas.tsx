import { useEffect, useMemo, useRef, useState } from "react";
import { select } from "d3-selection";
import { zoom, zoomIdentity, type D3ZoomEvent } from "d3-zoom";
import type { WordCountItem } from "../../shared/api/types";

interface PlacedWord {
  word: string;
  x: number;
  y: number;
  width: number;
  height: number;
  fontSize: number;
}

const VIEWPORT_WIDTH = 800;
const VIEWPORT_HEIGHT = 360;
const HUES = [262, 199, 27, 355, 158, 330, 172, 217];

function rectsOverlap(a: PlacedWord, b: PlacedWord): boolean {
  return !(
    a.x + a.width / 2 < b.x - b.width / 2 ||
    a.x - a.width / 2 > b.x + b.width / 2 ||
    a.y + a.height / 2 < b.y - b.height / 2 ||
    a.y - a.height / 2 > b.y + b.height / 2
  );
}

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) hash = (hash * 31 + value.charCodeAt(i)) >>> 0;
  return hash;
}

let measureCtx: CanvasRenderingContext2D | null = null;
function getMeasureCtx(): CanvasRenderingContext2D {
  measureCtx ??= document.createElement("canvas").getContext("2d")!;
  return measureCtx;
}

function buildLayout(items: WordCountItem[], width: number, height: number): PlacedWord[] {
  if (items.length === 0) return [];
  const ctx = getMeasureCtx();
  const counts = items.map((i) => i.count);
  const maxCount = Math.max(...counts);
  const minCount = Math.min(...counts);
  const fontSizeOf = (count: number) =>
    maxCount === minCount ? 28 : 14 + ((count - minCount) / (maxCount - minCount)) * 42;

  const placed: PlacedWord[] = [];
  for (const item of [...items].sort((a, b) => b.count - a.count)) {
    const fontSize = fontSizeOf(item.count);
    ctx.font = `${fontSize <= 20 ? 400 : 700} ${fontSize}px "JetBrains Mono", monospace`;
    const boxWidth = ctx.measureText(item.word).width + 6;
    const boxHeight = fontSize * 1.15;

    let angle = 0;
    let radius = 0;
    let x = width / 2;
    let y = height / 2;
    let box: PlacedWord = { word: item.word, x, y, width: boxWidth, height: boxHeight, fontSize };

    for (let attempts = 0; attempts < 4000; attempts++) {
      box = { word: item.word, x, y, width: boxWidth, height: boxHeight, fontSize };
      const inBounds =
        x - boxWidth / 2 > 4 &&
        x + boxWidth / 2 < width - 4 &&
        y - boxHeight / 2 > 4 &&
        y + boxHeight / 2 < height - 4;
      if (inBounds && !placed.some((p) => rectsOverlap(box, p))) break;
      angle += 0.35;
      radius += 1.4;
      x = width / 2 + radius * Math.cos(angle);
      y = height / 2 + radius * Math.sin(angle) * 0.7;
    }
    placed.push(box);
  }
  return placed;
}

interface Props {
  items: WordCountItem[];
  onWordClick?: (word: string) => void;
}

export function WordCloudCanvas({ items, onWordClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverWord, setHoverWord] = useState<string | null>(null);
  const [transform, setTransform] = useState("translate(0,0) scale(1)");

  const width = Math.max(VIEWPORT_WIDTH, Math.ceil(Math.sqrt(Math.max(items.length, 1)) * 140));
  const height = Math.max(VIEWPORT_HEIGHT, Math.ceil(width * 0.45));

  const layout = useMemo(() => buildLayout(items, width, height), [items, width, height]);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl || layout.length === 0) return;
    const zoomBehavior = zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.4, 3])
      .filter((event: Event) => {
        if (event.type === "wheel") return true;
        return !(event.target as Element).closest(".cloud-word");
      })
      .on("zoom", (event: D3ZoomEvent<SVGSVGElement, unknown>) => {
        setTransform(event.transform.toString());
      });
    const initial = zoomIdentity.translate(
      (VIEWPORT_WIDTH - width) / 2,
      (VIEWPORT_HEIGHT - height) / 2,
    );
    const selection = select(svgEl);
    selection.call(zoomBehavior).call(zoomBehavior.transform, initial);
    return () => {
      selection.on(".zoom", null);
    };
  }, [layout, width, height]);

  if (items.length === 0) return <p className="muted">Недостаточно данных.</p>;

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${VIEWPORT_WIDTH} ${VIEWPORT_HEIGHT}`}
      style={{
        width: "100%",
        height: `${VIEWPORT_HEIGHT}px`,
        touchAction: "none",
        cursor: "grab",
        background: "var(--bg-muted)",
        borderRadius: 12,
        display: "block",
      }}
    >
      <g transform={transform}>
        {layout.map((p) => (
          <text
            key={p.word}
            className="cloud-word"
            x={p.x}
            y={p.y}
            dy="0.35em"
            textAnchor="middle"
            fontFamily='"JetBrains Mono", monospace'
            fontWeight={p.fontSize <= 20 ? 400 : 700}
            fontSize={p.fontSize}
            fill={
              p.word === hoverWord
                ? "var(--text-h)"
                : `hsl(${HUES[hashString(p.word) % HUES.length]} 62% 45%)`
            }
            style={{
              cursor: "pointer",
              textDecoration: p.word === hoverWord ? "underline" : "none",
            }}
            onMouseEnter={() => setHoverWord(p.word)}
            onMouseLeave={() => setHoverWord((w) => (w === p.word ? null : w))}
            onClick={(e) => {
              e.stopPropagation();
              onWordClick?.(p.word);
            }}
          >
            {p.word}
          </text>
        ))}
      </g>
    </svg>
  );
}

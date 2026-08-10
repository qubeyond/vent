import { useEffect, useMemo, useRef, useState } from "react";
import { hierarchy, pack, type HierarchyCircularNode } from "d3-hierarchy";
import {
  forceCollide,
  forceSimulation,
  forceX,
  forceY,
  type Simulation,
  type SimulationNodeDatum,
} from "d3-force";
import { select } from "d3-selection";
import { zoom, zoomIdentity, type D3ZoomEvent } from "d3-zoom";
import type { Category, TagCloudItem } from "../../shared/api/types";
import { darken } from "../../shared/lib/color";

const CATEGORY_COLOR: Record<Category, string> = {
  здоровье: "#4ade80",
  карьера: "#60a5fa",
  финансы: "#facc15",
  отношения: "#f472b6",
  саморазвитие: "#a78bfa",
  отдых: "#fb923c",
  быт: "#94a3b8",
  эмоции: "#f87171",
  другое: "#64748b",
};

interface LeafDatum {
  kind: "leaf";
  tag: TagCloudItem;
}

interface CategoryDatum {
  kind: "category";
  category: Category;
}

type NodeDatum = LeafDatum | CategoryDatum | { kind: "root" };

interface CategoryNode extends SimulationNodeDatum {
  id: string;
  category: Category;
  r: number;
  homeX: number;
  homeY: number;
  leaves: { tag: TagCloudItem; dx: number; dy: number; r: number }[];
}

const WIDTH = 900;
const HEIGHT = 620;

function buildLayout(tags: TagCloudItem[]): CategoryNode[] {
  const byCategory = new Map<Category, TagCloudItem[]>();
  for (const tag of tags) {
    const list = byCategory.get(tag.category) ?? [];
    list.push(tag);
    byCategory.set(tag.category, list);
  }

  const root = hierarchy<NodeDatum>(
    {
      kind: "root",
      // @ts-expect-error
      children: [...byCategory.entries()].map(([category, catTags]) => ({
        kind: "category",
        category,
        children: catTags.map((tag) => ({ kind: "leaf", tag })),
      })),
    },
    (d) => ("children" in d ? (d as { children: NodeDatum[] }).children : undefined),
  ).sum((d) => (d.kind === "leaf" ? Math.max(d.tag.count, 1) : 0));

  const packed = pack<NodeDatum>().size([WIDTH, HEIGHT]).padding(6)(root);

  return packed.children!.map((catNode) => {
    const c = catNode as HierarchyCircularNode<NodeDatum>;
    const data = c.data as CategoryDatum;
    return {
      id: data.category,
      category: data.category,
      r: c.r,
      homeX: c.x,
      homeY: c.y,
      x: c.x,
      y: c.y,
      leaves: (c.children ?? []).map((leaf) => {
        const l = leaf as HierarchyCircularNode<NodeDatum>;
        const ld = l.data as LeafDatum;
        return { tag: ld.tag, dx: l.x - c.x, dy: l.y - c.y, r: l.r };
      }),
    };
  });
}

interface Props {
  tags: TagCloudItem[];
  onSelectTag: (tag: TagCloudItem) => void;
}

export function TagCloudCanvas({ tags, onSelectTag }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomGroupRef = useRef<SVGGElement>(null);
  const simulationRef = useRef<Simulation<CategoryNode, undefined> | null>(null);
  const [nodes, setNodes] = useState<CategoryNode[]>([]);
  const [transform, setTransform] = useState("translate(0,0) scale(1)");

  const layout = useMemo(() => buildLayout(tags), [tags]);

  useEffect(() => {
    if (layout.length === 0) {
      setNodes([]);
      return;
    }
    const simulation = forceSimulation(layout)
      .force("x", forceX<CategoryNode>((d) => d.homeX).strength(0.12))
      .force("y", forceY<CategoryNode>((d) => d.homeY).strength(0.12))
      .force(
        "collide",
        forceCollide<CategoryNode>()
          .radius((d) => d.r + 4)
          .iterations(2),
      )
      .on("tick", () => setNodes([...layout]));

    simulationRef.current = simulation;
    return () => {
      simulation.stop();
      simulationRef.current = null;
    };
  }, [layout]);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;
    const zoomBehavior = zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.4, 3])
      .filter((event: Event) => {
        if (event.type === "wheel") return true;
        return !(event.target as Element).closest(".cloud-node");
      })
      .on("zoom", (event: D3ZoomEvent<SVGSVGElement, unknown>) => {
        setTransform(event.transform.toString());
      });
    const selection = select(svgEl);
    selection.call(zoomBehavior).call(zoomBehavior.transform, zoomIdentity);
    return () => {
      selection.on(".zoom", null);
    };
  }, []);

  function screenToWorld(clientX: number, clientY: number): { x: number; y: number } | null {
    const svg = svgRef.current;
    const group = zoomGroupRef.current;
    if (!svg || !group) return null;
    const ctm = group.getScreenCTM();
    if (!ctm) return null;
    const point = svg.createSVGPoint();
    point.x = clientX;
    point.y = clientY;
    const local = point.matrixTransform(ctm.inverse());
    return { x: local.x, y: local.y };
  }

  const DRAG_THRESHOLD = 5;

  function handlePointerDown(e: React.PointerEvent, node: CategoryNode) {
    e.stopPropagation();
    const startX = e.clientX;
    const startY = e.clientY;
    const leafId = (e.target as Element).closest("[data-tag-id]")?.getAttribute("data-tag-id") ?? null;
    let moved = false;

    (e.currentTarget as Element).setPointerCapture(e.pointerId);
    simulationRef.current?.alphaTarget(0.3).restart();

    function onMove(ev: PointerEvent) {
      if (!moved && Math.hypot(ev.clientX - startX, ev.clientY - startY) > DRAG_THRESHOLD) {
        moved = true;
      }
      const p = screenToWorld(ev.clientX, ev.clientY);
      if (!p) return;
      node.fx = p.x;
      node.fy = p.y;
    }
    function onUp() {
      node.fx = null;
      node.fy = null;
      simulationRef.current?.alphaTarget(0);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      if (!moved && leafId) {
        const leaf = node.leaves.find((l) => l.tag.id === leafId);
        if (leaf) onSelectTag(leaf.tag);
      }
    }
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  if (tags.length === 0) {
    return <p className="muted">Пока пусто — запиши первую мысль.</p>;
  }

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{
        width: "100%",
        height: "70vh",
        touchAction: "none",
        cursor: "grab",
        background: "var(--bg-muted)",
        borderRadius: 12,
      }}
    >
      <g ref={zoomGroupRef} transform={transform}>
        {nodes.map((node) => {
          const catColor = CATEGORY_COLOR[node.category];
          return (
            <g
              key={node.id}
              className="cloud-node"
              transform={`translate(${node.x ?? 0}, ${node.y ?? 0})`}
              onPointerDown={(e) => handlePointerDown(e, node)}
              style={{ cursor: "grab" }}
            >
              <circle r={node.r} fill={catColor} fillOpacity={0.12} stroke={catColor} strokeWidth={1.5} />
              <text
                y={-node.r + 14}
                textAnchor="middle"
                fontSize={13}
                fontWeight={700}
                fill={catColor}
                style={{ pointerEvents: "none", userSelect: "none" }}
              >
                {node.category}
              </text>
              {node.leaves.map((leaf) => (
                <g
                  key={leaf.tag.id}
                  data-tag-id={leaf.tag.id}
                  transform={`translate(${leaf.dx}, ${leaf.dy})`}
                  style={{ cursor: "pointer" }}
                >
                  <circle
                    r={leaf.r}
                    fill={leaf.tag.color}
                    fillOpacity={0.28}
                    stroke={darken(leaf.tag.color, 0.25)}
                    strokeWidth={1}
                  />
                  {leaf.r > 14 && (
                    <text
                      textAnchor="middle"
                      dy="0.35em"
                      fontSize={Math.min(12, leaf.r / 2.2)}
                      fill="var(--text-h)"
                      style={{ pointerEvents: "none", userSelect: "none" }}
                    >
                      {leaf.tag.canonical_name}
                    </text>
                  )}
                  <title>
                    {leaf.tag.canonical_name} · {leaf.tag.count}
                  </title>
                </g>
              ))}
            </g>
          );
        })}
      </g>
    </svg>
  );
}

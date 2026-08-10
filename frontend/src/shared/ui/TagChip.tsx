import type { ButtonHTMLAttributes } from "react";
import { darken, withAlpha } from "../lib/color";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  name: string;
  color: string;
  selected?: boolean;
  fontSize?: string;
  dim?: boolean;
}

export function TagChip({ name, color, selected, fontSize, dim, style, ...rest }: Props) {
  const isButton = rest.onClick !== undefined;
  const Tag = isButton ? "button" : "span";
  return (
    <Tag
      type={isButton ? "button" : undefined}
      className={isButton ? "tag-chip-btn" : undefined}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        fontSize: fontSize ?? "0.8em",
        lineHeight: 1.4,
        padding: "0.15em 0.6em",
        borderRadius: 6,
        border: `1px solid ${dim ? "var(--border)" : darken(color, selected ? 0.4 : 0.25)}`,
        background: dim ? "var(--bg-muted)" : selected ? color : withAlpha(color, 0.16),
        color: dim ? "var(--text)" : selected ? "#fff" : "var(--text-h)",
        cursor: isButton ? "pointer" : "default",
        transition: "transform 0.12s ease, background 0.12s ease",
        ...style,
      }}
      {...rest}
    >
      {name}
    </Tag>
  );
}

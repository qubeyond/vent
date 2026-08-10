function clamp(n: number): number {
  return Math.max(0, Math.min(255, n));
}

export function darken(hex: string, amount = 0.28): string {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex);
  if (!match) return hex;
  const num = parseInt(match[1], 16);
  const r = clamp(((num >> 16) & 0xff) * (1 - amount));
  const g = clamp(((num >> 8) & 0xff) * (1 - amount));
  const b = clamp((num & 0xff) * (1 - amount));
  return `#${[r, g, b].map((c) => Math.round(c).toString(16).padStart(2, "0")).join("")}`;
}

export function withAlpha(hex: string, alpha: number): string {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex);
  if (!match) return hex;
  const a = Math.round(clamp(alpha * 255)).toString(16).padStart(2, "0");
  return `#${match[1]}${a}`;
}

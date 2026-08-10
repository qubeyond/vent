export function countChars(text: string): number {
  return text.trim().length;
}

export function pluralizeChars(n: number): string {
  const mod100 = n % 100;
  const mod10 = n % 10;
  if (mod100 >= 11 && mod100 <= 14) return "символов";
  if (mod10 === 1) return "символ";
  if (mod10 >= 2 && mod10 <= 4) return "символа";
  return "символов";
}

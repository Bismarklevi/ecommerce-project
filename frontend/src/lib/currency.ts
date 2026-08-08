export function formatPrice(amount: string | number): string {
  const value = typeof amount === "string" ? Number(amount) : amount;
  return `GH\u20B5${value.toFixed(2)}`;
}

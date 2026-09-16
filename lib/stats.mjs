// Statistics for paired benchmark comparisons.
//
// The method follows cubedevinc/semantic-layer-benchmark: accuracy with a
// Wilson 95% interval per condition, and an exact two-sided McNemar test on
// the questions where two conditions disagree.

export const Z_95 = 1.959963984540054;

/** Wilson score interval for k successes out of n. */
export function wilsonInterval(k, n, z = Z_95) {
  if (!Number.isInteger(k) || !Number.isInteger(n) || k < 0 || n < 0 || k > n) {
    throw new Error(`wilsonInterval needs 0 <= k <= n, got k=${k}, n=${n}`);
  }
  if (n === 0) return { low: 0, high: 1 };
  const p = k / n;
  const z2 = z * z;
  const denominator = 1 + z2 / n;
  const center = (p + z2 / (2 * n)) / denominator;
  const half = (z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / denominator;
  return { low: Math.max(0, center - half), high: Math.min(1, center + half) };
}

/** log of n choose k, stable for the sizes benchmarks produce. */
function logChoose(n, k) {
  let total = 0;
  for (let i = 1; i <= k; i += 1) total += Math.log(n - k + i) - Math.log(i);
  return total;
}

/**
 * Exact two-sided McNemar test.
 * @param {number} b questions only the baseline got right
 * @param {number} c questions only the challenger got right
 */
export function mcnemarExact(b, c) {
  if (!Number.isInteger(b) || !Number.isInteger(c) || b < 0 || c < 0) {
    throw new Error(`mcnemarExact needs non-negative integers, got b=${b}, c=${c}`);
  }
  const n = b + c;
  if (n === 0) return 1;
  const smaller = Math.min(b, c);
  let tail = 0;
  for (let i = 0; i <= smaller; i += 1) tail += Math.exp(logChoose(n, i) - n * Math.LN2);
  return Math.min(1, 2 * tail);
}

/**
 * Difference in accuracy (challenger minus baseline) over N paired questions,
 * with a Wald interval computed from the discordant pairs.
 */
export function pairedDifference(b, c, total, z = Z_95) {
  if (total <= 0) return { difference: 0, low: 0, high: 0 };
  const difference = (c - b) / total;
  const variance = ((b + c) - ((c - b) ** 2) / total) / (total * total);
  const half = z * Math.sqrt(Math.max(0, variance));
  return { difference, low: Math.max(-1, difference - half), high: Math.min(1, difference + half) };
}

/** Linear-interpolated quantile; null for an empty list. */
export function quantile(values, q) {
  const sorted = values.filter((value) => typeof value === 'number' && Number.isFinite(value)).sort((a, b) => a - b);
  if (sorted.length === 0) return null;
  const position = (sorted.length - 1) * q;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

export function mean(values) {
  const numbers = values.filter((value) => typeof value === 'number' && Number.isFinite(value));
  return numbers.length === 0 ? null : numbers.reduce((sum, value) => sum + value, 0) / numbers.length;
}

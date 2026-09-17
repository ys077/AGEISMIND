/**
 * Utility functions for probability normalization and formatting.
 * Backend returns decimal probabilities (0.0 to 1.0).
 * Frontend displays probabilities as percentages (0% to 100%).
 */

/**
 * Normalizes a probability value safely to a 0-100 scale.
 * Handles null, undefined, NaN, decimal 0-1, and 0-100 gracefully.
 */
export function normalizeProbability(value: number | null | undefined): number {
  if (value === null || value === undefined || isNaN(value)) {
    return 0;
  }
  if (value >= 0 && value <= 1) {
    return value * 100;
  }
  if (value > 1 && value <= 100) {
    return value;
  }
  return 0;
}

/**
 * Formats a probability value for display in the UI.
 * e.g., 0.95 -> "95%", 0.85 -> "85%", 0.65 -> "65%", 0.005 -> "<1%", 0 -> "0%"
 */
export function formatProbability(value: number | null | undefined): string {
  const normalized = normalizeProbability(value);
  if (normalized === 0) {
    return '0%';
  }
  if (normalized > 0 && normalized < 1) {
    return '<1%';
  }
  return `${Math.round(normalized)}%`;
}

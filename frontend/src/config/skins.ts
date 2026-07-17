/**
 * Reactor palette — the fixed VIIBE thermal ramp.
 *
 * The skin-selection feature was removed; the reactor renders in one brand
 * palette (Heat) mapped to the five energy levels:
 *   [dormant, stirring, buzzing, popping, electric]
 *
 * resolveSkinPalette keeps its signature so callers need no changes; any
 * argument (including a legacy reactor_skin value) resolves to Heat.
 */
export const HEAT_PALETTE: [string, string, string, string, string] = [
  '#241C16', '#7A2E00', '#E85D00', '#FFB300', '#FFF3D6',
];

export function resolveSkinPalette(
  _skinKey?: string,
): [string, string, string, string, string] {
  return HEAT_PALETTE;
}

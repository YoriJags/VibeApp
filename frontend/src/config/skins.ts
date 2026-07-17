/**
 * VibeReactor Skin System
 *
 * Each skin defines a 5-color palette mapped to energy levels:
 * [dormant, stirring, buzzing, popping, electric]
 *
 * Custom skins (VIBE+ only) derive a palette from a user-supplied hex.
 */

export interface SkinPreset {
  key:     string;
  name:    string;
  preview: string;          // single color shown in picker
  palette: [string, string, string, string, string];
  vibePlus?: boolean;       // if true, requires Vibe+
}

// Launch: one skin only — Heat, the brand thermal ramp. getSkinPreset falls
// back to SKIN_PRESETS[0], so any legacy reactor_skin value resolves to Heat.
export const SKIN_PRESETS: SkinPreset[] = [
  {
    key:     'heat',
    name:    'Heat',
    preview: '#FF4D00',
    palette: ['#241C16', '#7A2E00', '#E85D00', '#FFB300', '#FFF3D6'],
  },
];

/** Look up a preset by key, falling back to default. */
export function getSkinPreset(key: string): SkinPreset {
  return SKIN_PRESETS.find(s => s.key === key) ?? SKIN_PRESETS[0];
}

/**
 * Derive a 5-stop palette from any hex color.
 * Produces [very-dark, dark, mid, bright, near-white] tones of the hue.
 */
export function hexToLevelPalette(hex: string): [string, string, string, string, string] {
  const c = hexToRgb(hex);
  if (!c) return SKIN_PRESETS[0].palette;

  const blend = (ratio: number, toWhite = false): string => {
    const bg = toWhite ? { r: 255, g: 255, b: 255 } : { r: 0, g: 0, b: 0 };
    const r = Math.round(c.r * ratio + bg.r * (1 - ratio));
    const g = Math.round(c.g * ratio + bg.g * (1 - ratio));
    const b = Math.round(c.b * ratio + bg.b * (1 - ratio));
    return rgbToHex(r, g, b);
  };

  return [
    blend(0.12),           // dormant  — near-black tint
    blend(0.42),           // stirring — dark saturated
    blend(0.72),           // buzzing  — mid tone
    hex,                   // popping  — full color
    blend(0.55, true),     // electric — pale pastel towards white
  ];
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const clean = hex.replace('#', '');
  if (clean.length !== 6) return null;
  return {
    r: parseInt(clean.slice(0, 2), 16),
    g: parseInt(clean.slice(2, 4), 16),
    b: parseInt(clean.slice(4, 6), 16),
  };
}

function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
}

/**
 * Resolve any skin key (preset or 'custom:#RRGGBB') to its 5-color palette.
 */
export function resolveSkinPalette(
  skinKey: string | undefined,
): [string, string, string, string, string] {
  if (!skinKey) return SKIN_PRESETS[0].palette;

  if (skinKey.startsWith('custom:')) {
    const hex = skinKey.slice(7);
    return hexToLevelPalette(hex);
  }

  return getSkinPreset(skinKey).palette;
}

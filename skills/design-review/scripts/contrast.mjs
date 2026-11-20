#!/usr/bin/env node
/** contrast.mjs – WCAG 2.1 contrast ratio (AA=4.5, AAA=7.0)
 * Uso: node contrast.mjs --fg=#HEX --bg=#HEX [--aaa]
 * Salida: JSON { fg, bg, ratio, passAA, passAAA }
 * Requiere: nada (fórmula WCAG pura, sin dependencias).
 */

const args = process.argv.slice(2);
const fg = args.find(a => a.startsWith('--fg='))?.split('=')[1];
const bg = args.find(a => a.startsWith('--bg='))?.split('=')[1];
const aaa = args.includes('--aaa');

if (!fg || !bg) {
  console.error('Usage: node contrast.mjs --fg=#HEX --bg=#HEX [--aaa]');
  process.exit(1);
}

function hexToRgb(h) {
  const r = parseInt(h.slice(1, 3), 16) / 255;
  const g = parseInt(h.slice(3, 5), 16) / 255;
  const b = parseInt(h.slice(5, 7), 16) / 255;
  return [r, g, b].map(c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
}

function luminance(rgb) {
  return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
}

function contrast(fgHex, bgHex) {
  const l1 = luminance(hexToRgb(fgHex));
  const l2 = luminance(hexToRgb(bgHex));
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

const ratio = contrast(fg, bg);
const passAA = ratio >= 4.5;
const passAAA = aaa ? ratio >= 7.0 : null;

console.log(JSON.stringify({
  fg,
  bg,
  ratio: Math.round(ratio * 100) / 100,
  passAA,
  passAAA: passAAA === null ? "not requested" : passAAA
}));

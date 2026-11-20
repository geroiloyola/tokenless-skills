---
name: design-review
description: "Chooses one aesthetic direction and a small token set before writing UI code, then audits the result. Use when building or restyling any page or component, or before shipping frontend work. Not for backend or API-only changes."
license: MIT
metadata:
  version: "0.4.0"
---

# design-review

Read `references/uiux.md` (in this skill's folder) for the full digest: priority
table 1-10, token set, style families, seed palettes, font pairings, query
contract. The searchable catalog lives in the upstream skill if installed.

## Before coding (2 minutes, no exceptions)
1. Name the product type, the audience and the ONE feeling the page must convey.
2. Commit to one direction and write it down in the task: reference, mood, density.
   Generic means no decision was made. "Modern with purple gradients" is not a direction.
3. Derive tokens first, then components: background, surface, text, muted, accent,
   danger, success, plus a 4/8px spacing scale, a modular type scale, and one radius set.
4. Every color must exist as a token. No raw hex in components.
5. If the upstream skill is present, query it for the chosen
   product type and style; use its palettes and font pairings as the starting data.

## Hard rules (CRITICAL)
| Area | Must | Never |
|---|---|---|
| Accessibility | Text contrast ≥4.5:1, visible focus, labels, alt text | Remove focus rings |
| Target size | ≥44×44px interactive, ≥8px gap | Icon-only buttons without name |
| Responsive | Mobile-first, no horizontal scroll, 375px works | Disable zoom, fixed px containers |
| States | loading, empty, error, disabled for every async view | Ship only the happy path |
| Type | Body ≥16px, line-height ≥1.5, ≤75ch | Gray-on-gray text |
| Motion | 150–250ms, reduced-motion respected, animate transform/opacity | Animate width/height, one duration for all |
| Icons | SVG set, one family | Emoji as icons |
| Content | Real copy, real data | Lorem ipsum, placeholder avatars |

## Audit after building
Open the result in a browser (use the webapp-testing skill) at 375 and 1440. Score out of 10
on: hierarchy, spacing rhythm, contrast, state coverage, consistency of tokens.
For **contrast verification**: run `node <skill-dir>/scripts/contrast.mjs --fg=<hex> --bg=<hex>` for each token pair; mark PASS if ratio >=4.5. Otherwise: NOT AUDITED.
Scale anchors: 10 = shippable, coherent, states complete; 7 = good with minor polish; ≤6 = visible defects a user would notice — fix before finishing. Screenshot both widths as evidence.

## Output
`direction | tokens used | contrast checks | widths verified | score /10 | fixes applied`

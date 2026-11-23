---
name: design-review
description: "Chooses one aesthetic direction and a small token set before writing UI code, then audits the result. Use when building or restyling any page or component, or before shipping frontend work. Not for backend or API-only changes."
license: MIT
metadata:
  version: "0.5.0"
---

# design-review

## Before coding
1. Commit to ONE direction: product type + audience + style family + density, written down. "Modern" is not a direction.
2. Detect the stack from manifests (`package.json`, `pubspec.yaml`, ...); ask only if undetectable and it matters.
3. Tokens before components; zero raw hex in components. Color never the only meaning carrier; dark mode designed, not inverted.

## Token set (copy and derive)
```
bg / surface / surface-2 · text / text-muted / text-inverse
accent(+hover,on-accent) | danger success warning info | border focus-ring
space 4 8 12 16 24 32 48 64 · radius 4 8 16 full · shadow <=3
type 12 14 16 20 24 32 40 (body 16, lh 1.5, <=75ch) · motion 150-300ms ease-out, transform/opacity only
```

Fonts: max 2 families + 1 mono (Neutral: Inter + JetBrains Mono · Editorial: Source Sans 3 + Playfair). Palettes: SaaS `#0F172A #38BDF8 #F8FAFC` · Dark `#0A0A0B #A3E635 #E5E7EB`.

## Hard rules (CRITICAL)
| Area | Must | Never |
|---|---|---|
| Accessibility | Text contrast >=4.5:1, visible focus, labels, alt text | Remove focus rings |
| Target size | >=44x44px interactive, >=8px gap | Icon-only button without name |
| Responsive | Mobile-first, no horizontal scroll, 375px works | Disable zoom, fixed px containers |
| States | loading, empty, error, disabled for every async view | Ship only the happy path |
| Type | Body >=16px, lh >=1.5, <=75ch | Gray-on-gray text |
| Motion/Forms | 150-250ms, reduced-motion, transform/opacity only; visible label, error next to field | Animate width/height; placeholder as label |
| Icons/Content | One SVG family; real copy, real data | Emoji as icons; lorem ipsum |

AI tells: 3 shadow levels · emoji icons · gray-on-gray text · everything centered, no hierarchy · hover scale everywhere · component without empty state.

## Audit after building
Open in a browser (webapp-testing skill) at 375 and 1440. Verify contrast >=4.5:1 per token pair (NOT AUDITED if unverifiable). Score /10: 10 shippable · 7 minor polish · <=6 fix before finishing. Screenshot both widths.

## Output
`direction | tokens used | contrast checks | widths verified | score /10 | fixes applied`
